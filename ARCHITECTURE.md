# Arquitetura Industrial Avatar (V18/V19) - 100% Nuvem e "Zero-Waste"

Este documento serve como a "Bíblia" do pipeline de produção de avatares. **Qualquer agente de Inteligência Artificial que for atuar neste repositório DEVE respeitar estritamente as regras descritas abaixo.**

## 1. Regras de Ouro (Zero-Waste & Cloud-Native)
- **Nunca instale dependências do zero no boot da máquina alvo.** O boot deve ser quase instantâneo.
- **Nunca use `git clone` na inicialização da GPU para baixar bibliotecas pesadas (como o LatentSync).** Bibliotecas, binários e dependências críticas devem estar "assados" (baked) dentro da Imagem Docker.
- **Modelos Pesados ficam em Golden Disks.** O pipeline não baixa arquivos `.pth` toda vez; os discos persistentes e instantâneos da GCP (`/mnt/weights`) são montados `Read-Only` na máquina.
- **Eficiência Financeira:** A máquina de GPU (L4 / G2) só deve estar ligada enquanto processa. Assim que o vídeo é entregue no Cloud Storage, a máquina deve ser purgada.

---

## 2. Visão Geral da Arquitetura Passo a Passo

O fluxo de trabalho foi projetado para rodar de forma completamente gerenciada no Google Cloud Platform. Aqui estão as 8 etapas e como o código as atende:

### Etapa 1: Provisionamento Leve (Orquestrador)
- **Conceito:** Subir uma máquina com imagem pronta para NVIDIA (48GB RAM).
- **Alinhamento do Código (`src/agente_lana_orchestrator.py`):** O orquestrador usa a API nativa da GCP (`google-cloud-compute`) para ligar uma instância `g2-standard-12` usando a imagem otimizada `deeplearning-platform-release`.

### Etapa 2: Instalação Limpa e Modelos Instantâneos
- **Conceito:** O modelo não deve ser baixado demoradamente; ele precisa estar pronto para uso imediato.
- **Alinhamento do Código (`bootstrap_v18` em `agente_lana_orchestrator.py`):** Em vez de usar buckets para baixar modelos pesados a cada boot (o que é demorado), o pipeline anexa um **Snapshot / Golden Disk** (Disco Rápido) e monta instantaneamente no caminho `/mnt/weights`. Essa abordagem é *mais avançada* e rápida que puxar do bucket a cada renderização.

### Etapa 3 e 4: Orquestração API-First 100% Agno
- **Conceito:** A chamada é via API RESTful delegando a um orquestrador Serverless.
- **Alinhamento do Código (`api/main.py` & `src/industrial_main.py`):** 
  - O Agno faz a ponte local. 
  - A API em Nuvem usa `Cloud Tasks` para colocar a solicitação de vídeo em fila.
  - A Máquina L4, ao bootar, liga o servidor FastAPI contido na imagem Docker imutável.

### Etapa 5 e 6: Áudio ElevenLabs e Processamento
- **Conceito:** A voz customizada Sarah é gerada (baseada no texto), baixada e enviada ao motor de IA no Docker (LatentSync).
- **Alinhamento do Código (`src/agente_lana_orchestrator.py` e `src/industrial_main.py`):** A função `generate_audio` chama a ElevenLabs antes da GPU subir. O áudio é passado para o script industrial (`industrial_main.py`) via URL HTTP/GCS, que usa a GPU para fazer o Sync e depois empacota o vídeo (Mux com FFmpeg).

### Etapa 7: Devolução Automática (Cloud Storage)
- **Conceito:** O vídeo deve ir para o Bucket e ser puxado para a máquina local.
- **Alinhamento do Código (`src/industrial_main.py` e `src/produce_requested_videos.py`):**
  - O `industrial_main.py` finaliza o Muxing e executa nativamente o upload usando a lib `google-cloud-storage` diretamente para `gs://brasil-ai-avatars-vault/outputs/`.
  - O script local (`produce_requested_videos.py`), que está coordenando o processo, aguarda a notificação de término e então dispara o `gsutil cp` para salvar o vídeo diretamente na pasta `sucesso/` local.

### Etapa 8: Versionamento e Pipeline
- **Conceito:** GitHub Actions atua como esteira de pipeline.
- **Alinhamento do Código (`.github/workflows/produce_avatar.yml`):** O workflow dispara o script Python orquestrador sem expor as chaves da GCP, garantindo que todo o sistema rode a partir dos segredos injetados no repositório.

---

## 3. Resumo sobre o Git
- O código do sistema de orquestração desenvolvido (`agente_lana_orchestrator.py`, etc) **continua versionado no GitHub (`master`)**.
- O GitHub Actions **continua sendo usado** como gatilho.
- O que o Git **DEIXOU** de fazer: Fazer o download compulsório de bibliotecas de terceiros (`git clone .../LatentSync`) dentro da GPU durante o boot. A responsabilidade de manter as dependências base passou a ser exclusividade do Registry do Docker (Imagem `avatar-l4:v2.8`).
