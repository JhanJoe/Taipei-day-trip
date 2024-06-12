#!/bin/bash

# 設定變數
PROJECT_DIR="/home/ubuntu/jjwhtwo"
VENV_DIR="/home/ubuntu/myenv"
GIT_BRANCH="develop"

# 設置腳本選項
set -e  # 遇到錯誤立即退出
set -x  # 顯示每一步的命令

# 停止當前的 Uvicorn 進程
echo "Stopping current Uvicorn process..."
pkill -f uvicorn

# 進入項目目錄
echo "Navigating to project directory..."
cd $PROJECT_DIR

# 進入虛擬環境
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# 拉取最新代碼
echo "Pulling latest code from GitHub..."
git fetch origin
git log origin/$GIT_BRANCH --oneline
git pull origin $GIT_BRANCH

# 確認檔案code有更新
# echo "Checking updated code..."
# ls -l api/api_attractions.py

# 重啟 Uvicorn 進程
echo "Restarting Uvicorn process..."
nohup uvicorn app:app --host 0.0.0.0 --port 8000 &

echo "Update and restart completed."
