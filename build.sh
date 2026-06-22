#!/usr/bin/env bash
# Build script pour Render
set -o errexit

# FFmpeg requis par pydub pour compresser les fichiers audio
if command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y ffmpeg
fi

pip install -r requirements.txt

# Compiler le CSS Tailwind
npm install && npm run build:css || true

python manage.py collectstatic --noinput
python manage.py migrate --noinput
