#!/usr/bin/env bash
# Build script pour Render
set -o errexit

pip install -r requirements.txt

# Compiler le CSS Tailwind
npm install && npm run build:css || true

python manage.py collectstatic --noinput
python manage.py migrate --noinput
