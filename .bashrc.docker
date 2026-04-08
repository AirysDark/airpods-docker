# =========================    
# AirPods Docker Bash RC (Ultimate+)    
# =========================    

# -------------------------    
# Environment    
# -------------------------    
export IN_DOCKER=1    
export APP_ROOT="/debug"    
export PATH="$APP_ROOT:$APP_ROOT/scripts:$PATH"    

# API endpoint (override supported)    
export AP_API="${AP_API:-http://localhost:5050}"    

# -------------------------    
# Colors    
# -------------------------    
if [ -t 1 ]; then    
    RED='\033[0;31m'    
    GREEN='\033[0;32m'    
    YELLOW='\033[0;33m'    
    BLUE='\033[0;34m'    
    NC='\033[0m'    
else    
    RED='' GREEN='' YELLOW='' BLUE='' NC=''    
fi    

# -------------------------    
# Utilities    
# -------------------------    
_check_cmd() { command -v "$1" >/dev/null 2>&1; }    

# -------------------------    
# Load shared library    
# -------------------------    
if [ -f "$APP_ROOT/bashlib.sh" ]; then    
    source "$APP_ROOT/bashlib.sh"    
else    
    echo -e "${RED}[ERROR] bashlib.sh not found in $APP_ROOT${NC}"    
fi    

# -------------------------    
# Dependency checks    
# -------------------------    
_check_cmd curl || echo -e "${RED}[ERROR] curl not installed${NC}"    
_check_cmd jq   || echo -e "${YELLOW}[WARN] jq not installed ? raw JSON fallback${NC}"    
_check_cmd python || echo -e "${YELLOW}[WARN] python not found${NC}"    

# -------------------------    
# Aliases    
# -------------------------    
alias ll='ls -lah'    

alias ap-connect="curl -s $AP_API/connect"    
alias ap-state="curl -s $AP_API/state | jq 2>/dev/null || curl -s $AP_API/state"    

alias ap-anc="curl -s $AP_API/noise/2"    
alias ap-trans="curl -s $AP_API/noise/3"    
alias ap-adapt="curl -s $AP_API/noise/4"    

alias ap-ca-on="curl -s $AP_API/ca/1"    
alias ap-ca-off="curl -s $AP_API/ca/0"    

# -------------------------    
# Core Functions    
# -------------------------    

ap_help() {    
    echo -e "${BLUE}AirPods Control Commands:${NC}"    
    echo " ap_menu        ? interactive control menu"    
    echo " ap_dash        ? terminal dashboard (manual launch only)"    
    echo " ap_auto        ? auto reconnect loop"    
    echo " ap-connect     ? connect"    
    echo " ap-state       ? show state"    
    echo " ap_record_start ? start recording"    
    echo " ap_record_stop  ? stop recording"    
    echo " ap_record_save  ? save capture"    
    echo " ap_replay      ? replay packets"    
    echo " ap_raw HEX     ? send raw packet"    
    echo " ap_root        ? switch to root"    
    echo " ap_user        ? switch to airpods user"    
}    

ap_ping() {    
    if curl -s "$AP_API/state" >/dev/null; then    
        echo -e "${GREEN}[OK] API reachable${NC}"    
    else    
        echo -e "${RED}[FAIL] API unreachable${NC}"    
    fi    
}    

# -------------------------    
# Interactive Menu    
# -------------------------    
ap_menu() {    
    while true; do    
        echo -e "${BLUE}"    
        echo "====== AirPods Control Menu ======"    
        echo "1) Connect"    
        echo "2) ANC"    
        echo "3) Transparency"    
        echo "4) Adaptive"    
        echo "5) CA ON"    
        echo "6) CA OFF"    
        echo "7) Show State"    
        echo "8) Dashboard (manual launch)"    
        echo "9) Auto Reconnect"    
        echo "10) Start Recording"    
        echo "11) Stop Recording"    
        echo "12) Replay Recording"    
        echo "13) Send Raw Packet"    
        echo "0) Exit"    
        echo "=================================="    
        echo -e "${NC}"    

        read -p "Select option: " choice    

        case $choice in    
            1) ap-connect ;;    
            2) ap-anc ;;    
            3) ap-trans ;;    
            4) ap-adapt ;;    
            5) ap-ca-on ;;    
            6) ap-ca-off ;;    
            7) ap-state ;;    
            8) ap_dash ;;    
            9) ap_auto ;;    
            10) ap_record_start ;;    
            11) ap_record_stop ;;    
            12) ap_replay ;;    
            13)    
                read -p "Enter HEX packet: " hex    
                ap_raw "$hex"    
                ;;    
            0) break ;;    
            *) echo "Invalid option" ;;    
        esac    
    done    
}    

# -------------------------    
# Auto Reconnect    
# -------------------------    
ap_auto() {    
    while true; do    
        if curl -s "$AP_API/connect" >/dev/null; then    
            echo "[OK] Connected"    
        else    
            echo "[FAIL] Connection failed"    
        fi    
        sleep 10    
    done    
}    

# -------------------------    
# Raw Packet Sender    
# -------------------------    
ap_raw() {    
    if [ -z "$1" ]; then    
        echo "[ERROR] Usage: ap_raw \"HEX_STRING\""    
        return 1    
    fi    
    curl -s -X POST "$AP_API/raw" -d "$1"    
}    

# -------------------------    
# User Switching    
# -------------------------    
ap_root() {    
    if [ "$EUID" -eq 0 ]; then    
        echo "[INFO] Already root"    
    else    
        sudo su -    
    fi    
}    

ap_user() {    
    if [ "$USER" = "airpods" ]; then    
        echo "[INFO] Already airpods user"    
    else    
        su - airpods    
    fi    
}    

# -------------------------    
# User awareness    
# -------------------------    
if [ "$EUID" -eq 0 ]; then    
    echo -e "${YELLOW}[USER] root${NC}"    
else    
    echo -e "${GREEN}[USER] $USER${NC}"    
fi    

# -------------------------    
# Bluetooth check    
# -------------------------    
if _check_cmd hciconfig; then    
    if hciconfig | grep -q "hci"; then    
        echo -e "${GREEN}[BT] Bluetooth adapter detected${NC}"    
    else    
        echo -e "${YELLOW}[BT] No adapter detected${NC}"    
    fi    
else    
    echo -e "${RED}[BT] hciconfig missing${NC}"    
fi    

# -------------------------    
# Banner    
# -------------------------    
echo -e "${BLUE}"    
echo "======================================"    
echo "   AirPods Advanced Control Shell     "    
echo "======================================"    
echo -e "${NC}"    

echo "API: $AP_API"    
echo "Type 'ap_help' or 'ap_menu'"    

# -------------------------    
# API Check    
# -------------------------    
ap_ping