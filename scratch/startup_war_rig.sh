#!/bin/bash
echo '[SOBERANA] Ingressando no Tanque de Guerra...'
# Garante que o Docker estara pronto
systemctl start docker || true
# Dispara o Render dentro de um Tmux imortal
# O comando python3 trigger_dub.py ja foi testado e saneado
tmux new-session -d -s lana_render 'cd /workspace && python3 trigger_dub.py'
echo '[SOBERANA] Render disparado em background. O SSH pode cair, a Cris nao para.'
