# -*- coding: utf-8 -*-
"""
Material Search Engine - 启动脚本 / Startup Script
"""

from app.main import app, init

if __name__ == '__main__':
    # 初始化应用
    init()
    
    # 配置日志
    import logging
    from app.config import LOG_LEVEL, PORT, HOST, FLASK_DEBUG
    logging.getLogger('werkzeug').setLevel(LOG_LEVEL)
    
    print("\n" + "=" * 70)
    print("Material Search Engine - 启动中 / Starting...")
    print("=" * 70)
    print()
    
    app.run(
        debug=FLASK_DEBUG,
        host=HOST,
        port=PORT
    )
