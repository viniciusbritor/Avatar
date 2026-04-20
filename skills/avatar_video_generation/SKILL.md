---
name: avatar_video_generation
description: Gera vídeos de apresentadores de IA (avatares) utilizando D-ID, HeyGen e ElevenLabs.
---

# Skill: avatar_video_generation (MASTER)

Esta é a ferramenta definitiva de criação de persona para o **Brasil-Ei AI**. Ela integra motores de animação de pixels para dar voz aos roteiros produzidos.

### 🎭 Especificações da Persona Lana (BrasilIA):
- **Presenter ID:** `v2_public_lana_black_suite_green_screen@BTQAFVuIxZ`.
- **Voz Neural:** `Sarah - ElevenLabs` (ID: `EXAVITQu4vr4xnSDxMaL`) - Voz de autoridade e credibilidade.
- **Fundo Técnico:** Chroma Key Verde (#00AD3D) para montagem final.

### 🎼 Protocolo de Produção Dual:
A skill processa o roteiro em blocos:
1.  **Abertura:** `03_01_AVATAR_ABERTURA.mp4`.
2.  **Fechamento:** `03_02_AVATAR_FECHAMENTO.mp4`.

### 🚀 Motor de Disparo:
Utilize o script `scripts/generate_video.py` (ou `lana_generator_v5.py` na raiz) para automatizar a chamada à API da D-ID e realizar o download automático dos ativos. 📸💵✨
