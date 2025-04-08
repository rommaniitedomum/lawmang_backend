#!/bin/bash
set -e  # 오류 발생시 스크립트 중단

echo "📦 Deleting old app"
sudo rm -rf /var/www/lawmang_backend

echo "📁 Creating app folder"
sudo mkdir -p /var/www/lawmang_backend

echo "📂 Moving files to app folder"
sudo cp -r * /var/www/lawmang_backend/

cd /var/www/lawmang_backend/

echo "🔐 Setting up .env file..."
if [ -f ~/app_deploy/.env ]; then
    sudo cp ~/app_deploy/.env .env
    sudo chown ubuntu:ubuntu .env
    echo "✅ .env file copied from ~/app_deploy/.env"
elif [ -f env ]; then
    sudo mv env .env
    sudo chown ubuntu:ubuntu .env
    echo "✅ .env file created from env file"
elif [ -f .env ]; then
    sudo chown ubuntu:ubuntu .env
    echo "✅ .env file already exists"
else
    echo "⚠️ Warning: .env file not found"
fi

echo "🔍 Checking .env file..."
if [ -f .env ]; then
    echo ".env file exists"
    ls -la .env
else
    echo "⚠️ Warning: .env file not found"
fi

# 미니콘다 설치
if [ ! -d "/home/ubuntu/miniconda" ]; then
    echo "📥 Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    sudo chown ubuntu:ubuntu /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p /home/ubuntu/miniconda
    rm /tmp/miniconda.sh
fi

# PATH 설정
export PATH="/home/ubuntu/miniconda/bin:$PATH"
source /home/ubuntu/miniconda/bin/activate

# Nginx 설치 및 교체 (extras)
if ! dpkg -l | grep -q nginx-extras; then
    echo "🔄 Replacing existing Nginx with nginx-extras..."
    sudo apt-get remove -y nginx nginx-core nginx-full || true
    sudo apt-get update
    sudo apt-get install -y nginx-extras
else
    echo "✅ nginx-extras already installed"
fi

# Nginx 설정
echo "⚙️ Configuring Nginx..."
if [ ! -d "/etc/nginx/sites-available" ]; then
    sudo mkdir -p /etc/nginx/sites-available
fi

sudo bash -c 'cat > /etc/nginx/sites-available/myapp <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF'

sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo mkdir -p /var/log/lawmang_backend
sudo touch /var/log/lawmang_backend/uvicorn.log
sudo chown -R ubuntu:ubuntu /var/log/lawmang_backend

echo "🧹 Cleaning up existing processes..."
sudo pkill uvicorn || true
sudo systemctl stop nginx || true

sudo chown -R ubuntu:ubuntu /var/www/lawmang_backend

echo "🐍 Creating and activating conda environment..."
/home/ubuntu/miniconda/bin/conda create -y -n lawmang-env python=3.11 || true
source /home/ubuntu/miniconda/bin/activate lawmang-env

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚦 Testing and restarting Nginx..."
sudo nginx -t
sudo systemctl restart nginx

echo "🚀 Starting FastAPI application..."
cd /var/www/lawmang_backend
nohup /home/ubuntu/miniconda/envs/lawmang-env/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 > /var/log/lawmang_backend/uvicorn.log 2>&1 &

sleep 5

echo "📄 Recent application logs:"
tail -n 20 /var/log/lawmang_backend/uvicorn.log || true

echo "✅ Deployment completed successfully! 🚀"

echo "📡 Checking service status..."
ps aux | grep uvicorn
sudo systemctl status nginx
