#!/bin/bash
# 安裝 Python 依賴
echo Starting install.sh
echo y | pip3 install torch torchvision torchaudio
echo y | pip3 install flask pillow flask-login openai transformers pymysql python-pptx
echo y | pip3 install flask pyyaml mysql-connector-python DBUtils pynvml pymupdf ftfy

# 啟動 Python 應用
exec python3 app.py
