conda create -n Search_py312 python=3.12 -y 
conda activate Search_py312
conda install pytorch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 pytorch-cuda=12.4 -c pytorch -c nvidia -y
pip install -U -r requirements_windows.txt
pause
