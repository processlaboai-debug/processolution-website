#!/bin/sh
# Build per Cloudflare Pages: copia in dist/ solo i file pubblici del sito.
# Impostazioni Pages: Build command = "sh build.sh", Build output directory = "dist".
set -e
rm -rf dist
mkdir -p dist
cp index.html task-coordinator.html dist/
# Pagine legali di Task Coordinator (generate da tools/legal/sync_legal.py)
cp privacy.html terms.html dpa.html delete-account.html support.html dist/
cp logo.png favicon.png app-icon.png dist/
cp maxime-valcarce-mAj8xn5zXsk-unsplash.jpg google-deepmind-LIlsk-UFVxk-unsplash.jpg dist/
cp -R assets dist/
echo "dist/ pronto:"
ls -la dist
