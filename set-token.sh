#!/bin/bash
# Salva o token do bot em /opt/linkgen/.env sem mostrar na tela e reinicia o bot.
set -e
cd /opt/linkgen
read -rsp "Cole o token do bot e aperte Enter: " TOKEN
echo
if [ -z "$TOKEN" ]; then echo "Token vazio, nada alterado."; exit 1; fi
touch .env
chmod 600 .env
grep -v '^DISCORD_TOKEN=' .env > .env.tmp || true
echo "DISCORD_TOKEN=$TOKEN" >> .env.tmp
mv .env.tmp .env
chmod 600 .env
systemctl restart linkgen
sleep 4
systemctl --no-pager --lines=5 status linkgen | tail -n 6
