#!/bin/sh
# Copy to ~/n8n-start.sh, fill the three placeholders, keep private: chmod 700 ~/n8n-start.sh
export PATH="$HOME/n8n/bin:/usr/local/bin:$PATH"
export NODE_OPTIONS="--max-old-space-size=384"
export N8N_PORT="YOUR_RESERVED_WEB_PORT"
export N8N_LISTEN_ADDRESS="127.0.0.1"
export N8N_PROTOCOL="https"
export WEBHOOK_URL="https://YOUR_SUBDOMAIN.serv00.net/"
export GENERIC_TIMEZONE="YOUR_IANA_TIMEZONE"
export N8N_ENCRYPTION_KEY="YOUR_STABLE_RANDOM_KEY_FROM_OPENSSL"
export N8N_LOG_LEVEL="info"
# Only enable unrestricted Code-node imports if you understand the security impact:
# export NODE_FUNCTION_ALLOW_BUILTIN="*"
# export NODE_FUNCTION_ALLOW_EXTERNAL="*"
mkdir -p "$HOME/logs"
# Match the actual executable path. A broad "n8n start" matches this cron shell itself.
if pgrep -f "bin/n8n start" >/dev/null 2>&1; then exit 0; fi
cd "$HOME" || exit 1
nohup n8n start >> "$HOME/logs/n8n.log" 2>&1 &
