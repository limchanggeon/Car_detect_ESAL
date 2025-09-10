#!/bin/bash

# Ubuntu Installation Script for Car_detect_ESAL
echo "🚗 Car Detection ESAL - Ubuntu Installation Script"
echo "=================================================="

# Check if running on Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "❌ This script is designed for Ubuntu/Debian systems"
    exit 1
fi

echo "📦 Updating package lists..."
sudo apt update

echo "🐍 Installing Python3 development packages..."
sudo apt install -y python3-dev python3-pip python3-venv

echo "🖥️  Installing PyQt5 system packages..."
sudo apt install -y python3-pyqt5 python3-pyqt5-dev python3-pyqt5.qtwebengine

echo "📸 Installing OpenCV system dependencies..."
sudo apt install -y libopencv-dev python3-opencv

echo "🔧 Installing additional system dependencies..."
sudo apt install -y \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    libqt5webkit5-dev \
    libxcb-xinerama0

echo "📁 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements-ubuntu.txt

echo "✅ Installation completed!"
echo ""
echo "🚀 To run the application:"
echo "   source .venv/bin/activate"
echo "   python main.py"
echo ""
echo "📝 Note: If you encounter any GUI issues, run:"
echo "   export QT_QPA_PLATFORM=xcb"