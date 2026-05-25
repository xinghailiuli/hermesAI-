# Post-Reset Recovery Checklist

When an Alibaba Cloud ECS instance is reset (reinstalled), follow this ordered checklist to restore Hermes + API Relay + proxy + cron.

## 1. SSH Access

```bash
# Alibaba Cloud VNC console → reset root password if needed
# Then:
ssh admin@<IP>   # password: Admin@2026!
# admin has sudo; root SSH may be disabled by default
```

## 2. Verify Hermes Data Survived

```bash
ls ~/.hermes/config.yaml ~/.hermes/.env ~/.hermes/memories/
# If missing, restore from backup:
hermes import ~/hermes-migration.zip --force
```

## 3. Restore API Relay (always lost — `hermes backup` excludes it)

```bash
mkdir -p ~/api-relay
# Copy templates from api-relay skill:
cp ~/.hermes/skills/infra/api-relay/templates/server.py ~/api-relay/
cp ~/.hermes/skills/infra/api-relay/templates/config.json ~/api-relay/
cp ~/.hermes/skills/infra/api-relay/templates/dashboard.html ~/api-relay/

# Install dependencies (Ubuntu 24.04 needs --break-system-packages)
export HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
pip3 install flask requests --break-system-packages
```

## 4. Proxy Systemd Service

```bash
# Config must be in user-writable dir (not /etc/mihomo/)
sudo cp /etc/mihomo/config.yaml ~/.config/mihomo/config.yaml
sudo chown $USER:$USER ~/.config/mihomo/config.yaml
# Remove GUI keys with Python (never sed!)
systemctl --user enable --now mihomo
```

## 5. Gateway Proxy Drop-in

```bash
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
# Add HTTP_PROXY/HTTPS_PROXY env vars
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```

## 6. API Relay Systemd Service

```bash
# Service must use EnvironmentFile=%h/.hermes/.env + proxy env vars
systemctl --user enable --now api-relay
```

## 7. Recreate Cron Jobs

```bash
hermes cron create --name '中转站每日备份' --deliver local '0 3 * * *' '...'
hermes cron create --name '服务器每日播报' --deliver origin '0 9 * * *' '...'
hermes cron create --name '中转站健康监控' --deliver origin '*/30 * * * *' '...'
hermes cron create --name 'Hermes每日备份' --deliver local '0 4 * * *' '...'
hermes cron create --name '服务器晚间播报' --deliver origin '0 20 * * *' '...'
```

## 8. Restore External Token Files

```bash
# GitHub token
cat > ~/.github_token << 'EOF'
export GITHUB_TOKEN=ghp_xxx
EOF
chmod 600 ~/.github_token

# 5sim token
cat > ~/.5sim_token << 'EOF'
export FIVESIM_TOKEN=eyJ...
EOF
chmod 600 ~/.5sim_token
```

## 9. Verify All Services

```bash
systemctl --user is-active hermes-gateway mihomo api-relay  # all should be "active"
curl http://127.0.0.1:8848/health                            # {"status":"ok"}
curl -x http://127.0.0.1:7897 -sI https://github.com | head -1  # HTTP/2 200
hermes cron list | grep -c '\[active\]'                       # expected: 5-7
```
