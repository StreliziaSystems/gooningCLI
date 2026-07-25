#!/bin/bash
# gooningCLI - Termux Setup Script
# Run: bash setup.sh

set -e

echo "==================================="
echo "  gooningCLI Setup for Termux"
echo "==================================="
echo ""

echo "[*] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "[*] Installing Python..."
pkg install -y python

echo "[*] Installing pip..."
pkg install -y python-pip

echo "[*] Installing core dependencies..."
pip install -r requirements.txt

echo "[*] Installing optional: yt-dlp (for video downloads)..."
pip install yt-dlp || echo "[!] yt-dlp install failed - video downloads from hentaihaven won't work"

echo "[*] Installing optional: termux-api (for notifications & wallpaper)..."
pkg install -y termux-api || echo "[!] termux-api install failed - notifications & wallpaper disabled"

echo "[*] Making script executable..."
chmod +x gooningcli.py

echo ""
echo "==================================="
echo "  Setup complete!"
echo "==================================="
echo ""
echo "  Run:  python gooningcli.py"
echo "  Or:   python gooningcli.py search 'futa' -n 10 -s nhentai"
echo ""
