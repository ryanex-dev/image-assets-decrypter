#!/data/data/com.termux/files/usr/bin/bash

echo "Installing Image Assets Decrypter..."

pkg update -y
pkg upgrade -y
pkg install -y python git libjpeg-turbo libpng

pip install pillow

termux-setup-storage

mkdir -p /storage/emulated/0/ryanex
cd /storage/emulated/0/ryanex

git clone https://github.com/ryanex-dev/image-assets-decrypter.git repo_tmp

cp repo_tmp/image_decrypter_v4.py .
rm -rf repo_tmp

echo ""
echo "Install selesai."
echo "Jalankan dengan:"
echo "cd /storage/emulated/0/ryanex"
echo "python image_decrypter_v4.py"
