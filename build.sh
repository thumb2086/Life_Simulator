#!/bin/bash
set -e

echo "============================================"
echo "  Life Simulator - Auto Build Script"
echo "============================================"
echo

# Step 1: Install dependencies
echo "[1/3] Installing dependencies..."
pip install -r requirements-desktop.txt
echo

# Step 2: Clean previous build
echo "[2/3] Cleaning previous build..."
rm -rf build dist/新股票銀行遊戲
echo

# Step 3: Compile with PyInstaller
echo "[3/3] Compiling executable..."
pyinstaller "新股票銀行遊戲.spec" --clean --noconfirm
echo

echo "============================================"
echo "  Build Complete!"
echo "  Output: dist/新股票銀行遊戲/"
echo "============================================"
