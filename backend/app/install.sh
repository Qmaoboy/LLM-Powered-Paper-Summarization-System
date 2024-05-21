#!/bin/bash
# 安裝 Python 依賴
echo Starting install.sh
echo y | pip install torch torchvision torchaudio
echo y | pip install flask pillow flask-login openai transformers pymysql python-pptx DBUtils pynvml pymupdf
# 啟動 Python 應用
exec python app.py
