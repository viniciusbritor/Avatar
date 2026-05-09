# Blueprint: Industrialização Soberana do Avatar (Lana)

Este documento define a arquitetura final, agnóstico de região e autossuficiente para a produção de avatares IA.

## 1. Arquitetura de Infraestrutura (GCP)
- **API**: VM `e2-micro` com disco **30 GB pd-standard** e IP fixo (`35.231.46.76`) em `us-east1-c`. Deploy manual (sem cron). Boot puxa imagem do Artifact Registry.
- **GPU**: `g2-standard-12` (48GB RAM, NVIDIA L4 24GB VRAM).
- **Região Primária**: `us-east1` (fallback: 13 zonas globais).
- **Modelo de Custo**: **On-Demand Sovereignty** (Disponibilidade garantida sem dependência de leilão).
- **Gestão de Redução de Custos**:
  - **Zero-Waste**: Sentinel HOST (systemd) desliga GPU em 30 min de inatividade ou 30 min se container morrer. Dead Man Switch absoluto em 90 min.
  - **Sentinela**: `lana-sentinel.service` roda no HOST da VM (fora do container), sem single point of failure.
- **Segurança**: Firewall fechado; acesso exclusivo via **IAP (Identity-Aware Proxy)**.

## 2. Orquestração e Statelessness
- **Backbone de Ativos**: Bucket `gs://lana-weights-universal/` (checkpoints) + `gs://brasil-ai-avatars-vault/` (outputs).
  - `/models/`: 15GB de pesos (UNet, Whisper, SyncNet, Buffalo_L).
  - `/templates/`: Vídeos originais da Lana.
- **Startup-Script**: Automação total via metadados do Google Cloud. Toda nova VM injeta automaticamente os modelos e inicializa o Docker em regime stateless.

## 3. Fluxo de Dados (Text-to-Video)
1.  **Orquestrador Local (Python/Agno)**: Gera áudio via ElevenLabs.
2.  **Transferência**: Upload do áudio para GCS e liberação de acesso temporário.
3.  **Processamento**: O motor GPU baixa o áudio, localiza o template e realiza a inferência (LatentSync) com **Patch de Retificação Visual v4.0**.
4.  **Entrega**: O resultado é persistido no Bucket de resultados e baixado localmente.

---
*Status: Industrializado. Soberano. On-Demand.*
