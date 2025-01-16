#!/bin/bash

TG_URL=$1
TG_CHAT_ID=$2
CMD_URL=$3

function src_git_repo {
  #check if directory exists
  if [ -d "/root/root/restarter" ]; then
    echo "restarter exists, pulling latest changes"
    cd /root/restarter/restarter || exit
    sudo -u root git pull
  else
    echo "restarter does not exist, cloning repo"
    sudo -u root mkdir -p /root/restarter/restarter
    sudo -u root git clone https://github.com/repchinskiy/restarter /root/restarter/restarter
    cd /root/restarter/restarter || exit
  fi
}

function prepare_python_env {
  if [ -d "/root/restarter/venv" ]; then
    echo "venv exists, it's ok"
    sudo -u root bash << EOF
    source /root/restarter/venv/bin/activate
    pip install -r /root/restarter/restarter/requirements.txt
EOF
    return
  else
    cd /root/restarter || exit
    
    # Проверяем наличие виртуального окружения
    if [ ! -d "venv" ]; then
        echo "venv does not exist, installing requirements"
        
        # Устанавливаем python3-venv
        sudo apt-get install python3-venv -y
        
        # Создаем виртуальное окружение от пользователя root
        sudo -u root python3 -m venv venv
    fi
    
    # Активируем виртуальное окружение и устанавливаем зависимости от пользователя root
    sudo -u root bash << EOF
    source /root/restarter/venv/bin/activate
    pip install -r /root/restarter/restarter/requirements.txt
EOF
  fi

}

function create_systemd {
  sudo tee <<EOF >/dev/null /etc/systemd/system/restarter.service
[Unit]
Description=Restarter
After=network-online.target
StartLimitIntervalSec=0
[Service]
User=root
Restart=always
RestartSec=3
LimitNOFILE=65535
#todo тут на основных аках не прокатит
ExecStart=/root/restarter/venv/bin/python3 /root/restarter/restarter/restarter.py $TG_URL $TG_CHAT_ID $CMD_URL
#ExecStart=/root/.pyenv/versions/3.11.10/bin/python3.11 /root/restarter/restarter/restarter.py $TG_URL $TG_CHAT_ID $CMD_URL
[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable restarter
  sudo systemctl restart restarter
}

function main {
  src_git_repo
  prepare_python_env
  create_systemd
}

main