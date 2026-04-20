#!/bin/bash
cd /workspace

# 1. Blindagem contra Sentinela
touch /tmp/lana_industrial.lock
echo "Iniciando Build Industrial v6.0 (Blindado)..." > build.log

# 2. Construção da Imagem Imutável
sudo docker build -t lana:v6 -f Dockerfile.v6 . >> build.log 2>&1

if [ $? -eq 0 ]; then
    echo "Build concluído com sucesso. Disparando Renderização..." >> build.log
    bash render.sh >> render.log 2>&1
else
    echo "Erro crítico no Build. Abortando." >> build.log
    exit 1
fi
