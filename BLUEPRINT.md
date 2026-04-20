# Blueprint: Industrialização Soberana do Avatar (Lana)

Este documento define a arquitetura final, agnóstico de região e autossuficiente para a produção de avatares IA.

## 1. Arquitetura de Infraestrutura (GCP)
- **Instância**: `g2-standard-4` (NVIDIA L4 24GB).
- **Região Primária**: `us-west1-a` (Oregon).
- **Modelo de Custo**: **On-Demand Sovereignty** (Disponibilidade garantida sem dependência de leilão).
- **Gestão de Redução de Custos**:
  - **Zero-Waste**: O orquestrador local desliga a instância imediatamente após o download do resultado.
  - **Sentinela de Inatividade**: Script interno na VM que dispara um `sudo shutdown -h now` caso a GPU permaneça ociosa por mais de 20 minutos (Proteção contra falhas de orquestração).
- **Segurança**: Firewall fechado; acesso exclusivo via **IAP (Identity-Aware Proxy)**.

## 2. Orquestração e Statelessness
- **Backbone de Ativos**: Bucket `gs://brasil-ia-lana-assets/`.
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
