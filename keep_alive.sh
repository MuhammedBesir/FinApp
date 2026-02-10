#!/bin/bash
# ============================================
# Midas Trading - Backend Keep-Alive System
# ============================================
# Bu script:
# 1. Her 5 dakikada /api/health endpoint'ini ping'ler (cold start'ı önler)
# 2. Yanıt gelmezse otomatik redeploy yapar
# 3. Log tutar
#
# Kullanım:
#   ./keep_alive.sh           → Tek seferlik kontrol
#   ./keep_alive.sh daemon    → Sonsuz döngüde çalış (5dk aralıkla)
#   ./keep_alive.sh install   → systemd timer olarak kur
# ============================================

BACKEND_URL="https://trading-botu.vercel.app"
HEALTH_ENDPOINT="$BACKEND_URL/api/health"
MARKET_ENDPOINT="$BACKEND_URL/api/market/all"
PROJECT_DIR="/home/MuhammedBesir/trading-botu"
LOG_FILE="/tmp/midas_keepalive.log"
MAX_LOG_SIZE=5242880  # 5MB

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
    
    # Log dosyası çok büyükse kırp
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
        tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
}

# Health check → HTTP 200 ve "healthy" içermeli
health_check() {
    local response
    response=$(curl -s --max-time 15 "$HEALTH_ENDPOINT" 2>/dev/null)
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log "${RED}❌ Health check FAILED - curl error ($exit_code)${NC}"
        return 1
    fi
    
    if echo "$response" | grep -q '"healthy"'; then
        log "${GREEN}✅ Health check OK${NC}"
        return 0
    else
        log "${YELLOW}⚠️ Health check unexpected response: ${response:0:100}${NC}"
        return 1
    fi
}

# Market endpoint'i warm-up et (en yavaş endpoint, cold start'ı tetikler)
warm_up() {
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$MARKET_ENDPOINT" 2>/dev/null)
    if [ "$status" = "200" ]; then
        log "${GREEN}🔥 Warm-up OK (market data loaded)${NC}"
    else
        log "${YELLOW}⚠️ Warm-up returned status $status${NC}"
    fi
}

# Vercel'e yeniden deploy et
redeploy() {
    log "${YELLOW}🔄 Redeploying to Vercel...${NC}"
    
    if ! command -v vercel &> /dev/null; then
        log "${RED}❌ Vercel CLI not found${NC}"
        return 1
    fi
    
    cd "$PROJECT_DIR" || return 1
    
    local output
    output=$(vercel --prod --yes 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✅ Redeploy successful${NC}"
        sleep 15  # Deployment'ın hazır olmasını bekle
        health_check
    else
        log "${RED}❌ Redeploy failed: ${output:0:200}${NC}"
        return 1
    fi
}

# Ana kontrol: health check → fail ise retry → hala fail ise redeploy
run_check() {
    if health_check; then
        # Her 3 check'te bir warm-up yap
        if [ $((RANDOM % 3)) -eq 0 ]; then
            warm_up
        fi
        return 0
    fi
    
    # İlk denemede fail → 10 saniye bekle, tekrar dene
    log "⏳ Retrying in 10 seconds..."
    sleep 10
    
    if health_check; then
        return 0
    fi
    
    # İki denemede de fail → redeploy
    log "${RED}🚨 Backend is DOWN! Starting redeploy...${NC}"
    redeploy
}

# Daemon modu: sonsuz döngüde çalış
daemon_mode() {
    log "🐕 Keep-alive daemon started (interval: 5 minutes)"
    log "   URL: $BACKEND_URL"
    log "   Log: $LOG_FILE"
    
    while true; do
        run_check
        sleep 300  # 5 dakika
    done
}

# systemd timer olarak kur
install_systemd() {
    local script_path
    script_path=$(realpath "$0")
    
    # Service dosyası
    sudo tee /etc/systemd/system/midas-keepalive.service > /dev/null << EOF
[Unit]
Description=Midas Trading Backend Keep-Alive
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
ExecStart=$script_path
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Timer dosyası (5 dakikada bir)
    sudo tee /etc/systemd/system/midas-keepalive.timer > /dev/null << EOF
[Unit]
Description=Midas Trading Backend Keep-Alive Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=300
Persistent=true

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable midas-keepalive.timer
    sudo systemctl start midas-keepalive.timer
    
    log "${GREEN}✅ systemd timer installed and started${NC}"
    log "   Check status: systemctl status midas-keepalive.timer"
    log "   Check logs:   journalctl -u midas-keepalive.service -f"
}

uninstall_systemd() {
    sudo systemctl stop midas-keepalive.timer 2>/dev/null
    sudo systemctl disable midas-keepalive.timer 2>/dev/null
    sudo rm -f /etc/systemd/system/midas-keepalive.service
    sudo rm -f /etc/systemd/system/midas-keepalive.timer
    sudo systemctl daemon-reload
    log "${GREEN}✅ systemd timer removed${NC}"
}

# Kullanım
case "${1:-check}" in
    check)      run_check ;;
    daemon)     daemon_mode ;;
    warmup)     warm_up ;;
    install)    install_systemd ;;
    uninstall)  uninstall_systemd ;;
    status)
        echo "=== Last 20 log entries ==="
        tail -20 "$LOG_FILE" 2>/dev/null || echo "No logs yet"
        echo ""
        if systemctl is-active --quiet midas-keepalive.timer 2>/dev/null; then
            echo "✅ systemd timer is ACTIVE"
            systemctl status midas-keepalive.timer --no-pager 2>/dev/null
        else
            echo "❌ systemd timer is NOT active"
        fi
        ;;
    *)
        echo "Midas Trading - Backend Keep-Alive System"
        echo ""
        echo "Kullanım: $0 {check|daemon|warmup|install|uninstall|status}"
        echo ""
        echo "  check      - Tek seferlik health check (default)"
        echo "  daemon     - Arka planda sürekli çalıştır (5dk aralıkla)"
        echo "  warmup     - Market endpoint'i warm-up et"
        echo "  install    - systemd timer olarak kur (bilgisayar açıkken otomatik)"
        echo "  uninstall  - systemd timer'ı kaldır"
        echo "  status     - Durum ve logları göster"
        ;;
esac
