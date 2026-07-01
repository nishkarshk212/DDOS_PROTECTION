#!/bin/bash
export SSHPASS='Sjdfddfh3fhfh4Hf'
HOST="root@168.144.157.140"

echo "[1/3] Cloning repository on remote server..."
sshpass -e ssh -o StrictHostKeyChecking=no $HOST "rm -rf ~/ddos-protection && git clone https://github.com/nishkarshk212/DDOS_PROTECTION.git ~/ddos-protection"

echo "[2/3] Uploading .env file securely..."
# Note: Using 'scp' to upload the file instead of 'cat' as it is the standard and safest method for file transfers over SSH.
sshpass -e scp -o StrictHostKeyChecking=no /Users/nishkarshkr/Desktop/ddos-protection/.env $HOST:~/ddos-protection/.env

echo "[3/3] Installing dependencies and starting the bot..."
sshpass -e ssh -o StrictHostKeyChecking=no $HOST "
    cd ~/ddos-protection && \
    apt update && \
    apt install -y python3-pip python3-venv screen iptables net-tools && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt && \
    screen -S ddos_bot -X quit || true && \
    screen -dmS ddos_bot ./venv/bin/python -m app.main
"

echo "✅ Deployment Complete! The DDoS Protection bot is now running on your server in a background screen session named 'ddos_bot'."
