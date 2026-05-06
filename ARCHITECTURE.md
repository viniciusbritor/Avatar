# Arquitetura Industrial Avatar (v3.2.2) — "Cérebro & Motor"

Este documento é a especificação soberana do ecossistema Brasil AI Avatar. Toda e qualquer modificação no código deve respeitar os pilares de **Zero-Waste**, **Cloud-Native** e **Blindagem de Segurança** aqui descritos.

---

## 1. Visão Geral (The Grand Design)
O sistema é dividido em duas camadas de responsabilidade distinta, conectadas via **Firestore** e **Webhook**:

1.  **O Cérebro (API v3.2.2):** Servidor FastAPI rodando em **VM e2-micro com IP fixo** (`35.231.46.76`). Responsável pela inteligência, orquestração e gestão de fila.
2.  **O Motor (L4 Engine):** Instâncias NVIDIA L4 (Compute Engine) dinâmicas, que nascem e morrem conforme a demanda, focadas exclusivamente em renderização pesada.

---

## 2. Componentes da Infraestrutura

### 2.1 API Cérebro (VM e2-micro — IP fixo)
- **Tecnologia:** Python 3.11, FastAPI.
- **Host:** VM e2-micro (`lana-api`) em `us-east1-c`. IP fixo: `35.231.46.76` (regional `us-east1`, movível entre zonas `b`/`c`/`d`).
- **Base Image:** `ubuntu-2204-lts` (Ubuntu 22.04 LTS, `ubuntu-os-cloud`). Obrigatório — o startup script depende de `apt-get`. NUNCA use `cos-stable` (Container-Optimized OS).
- **Orquestrador:** Agente Lana (Maestro via Agno/Phidata).
- **Segurança:** Autenticação via `X-API-Key` (validada **exclusivamente** contra GCP Secret Manager — Fail-Fast se ausente).
- **Missão:** Receber requisições, gerar áudio (ElevenLabs), enfileirar job no Firestore, e disparar GPU L4 sob demanda.
- **Deploy:** Cloud Build gera imagem → Artifact Registry → VM puxa via cron a cada 5 min (`infra/startup-e2-micro.sh`).

### 2.2 Cofre de Segredos (GCP Secret Manager — Free Tier)
- **Source of Truth único** para todas as credenciais do ecossistema.
- **Secrets ativas (4/6 do Free Tier):**
    - `API_SECRET_KEY` — Chave de autenticação HTTP interna entre Cérebro e Motor (header `X-API-Key`).
    - `GCP_SA_KEY` — JSON da Service Account master com acesso total ao projeto `brasili-ia-news`.
    - `ELEVEN_LABS_API_KEY` — Token da API ElevenLabs para síntese de voz (TTS).
    - `GEMINI_API_KEY` — Chave do Google Gemini para raciocínio do Maestro.
- **Backup:** O banco SQLite `brasil_ai.db` com todas as chaves do ecossistema YouTube está espelhado em `gs://brasil-ai-avatars-vault/brasil_ai.db` como cópia de segurança offline. NÃO é usado como fonte primária em runtime.

### 2.3 Gerenciamento de Jobs (Firestore)
- **Collection:** `avatar_jobs`.
- **Fluxo:** API escreve job como `queued` → GPU faz polling e processa → GPU notifica API via webhook → API atualiza para `completed`.
- **Vantagem:** Sem dependência de Cloud Tasks ou Pub/Sub. Firestore serve como fila e banco de estado simultaneamente.

### 2.4 Motor de IA (Compute Engine L4)
- **Hardware:** `g2-standard-12` (NVIDIA L4 24GB VRAM).
- **Estratégia de Boot:** Arquitetura 4 (Nativa) + Código Fresco via Git.
    - **Golden Disks:** Modelos pesados são montados via **GCS Fuse** em `/mnt/weights` (Zero download time).
    - **Startup Script:** Configura Docker, Nvidia Toolkit (`nvidia-ctk` incondicional), e GCS Fuse em segundos.
    - **Código Python:** Obtido fresco do GitHub (`git clone https://github.com/viniciusbritor/Avatar.git`) no boot — NUNCA extraído da imagem golden (evita rodar código congelado/defasado).
    - **Docker Image:** `avatar-l4:v2.10` (Layers otimizadas, todas deps baked).

### 2.5 Devolução e Gatilho (Firestore + GCS)
- **Storage:** Vídeos salvos em `gs://brasil-ai-avatars-vault/outputs/`.
- **Trigger:** O webhook da GPU atualiza o Firestore com status `completed` + `video_path`.
- **Local Bridge:** `sync_bridge.py` faz polling no Firestore (sem dependência de Pub/Sub) e baixa o vídeo para `sucesso/` assim que detecta o status `completed`.

---

## 3. Fluxo Industrial (Step-by-Step)

1.  **Injeção:** Usuário chama `POST /produce` na API.
2.  **Enfileiramento:** API gera áudio (TTS), salva o job no **Firestore** como `queued` com `webhook_url` apontando para `http://35.231.46.76:8080/webhook/render-complete` (HTTP puro, sem TLS — a API escuta na porta 8080 sem proxy reverso).
3.  **Spin-up GPU:** A API dispara `_spawn_gpu()` em background (caça 13+ zonas globais por L4 disponível, cria instância se necessário).
4.  **Processamento:** A GPU L4 faz polling no Firestore por jobs `queued`, executa o Lip Sync, sobe o vídeo para o GCS.
5.  **Callback (Webhook):** A GPU notifica a API via `POST` no endpoint `/webhook/render-complete` no IP fixo da e2-micro. **Crítico:** O protocolo deve ser sempre HTTP (não HTTPS), pois a API não tem TLS. O `webhook_url` é hardcoded no código (`api/main.py:155`) para evitar injeção de `https://` por proxies ou cabeçalhos de cliente.
6.  **Atualização Firestore:** A API recebe o webhook e atualiza o job para `completed` com o `video_path`.
7.  **Entrega Local:** O vídeo é baixado do bucket GCS para a máquina do operador. Dois métodos suportados:
    - **Automático:** `python src/sync_bridge.py --once` (polling Firestore, baixa jobs `completed` não baixados)
    - **Manual:** `gsutil cp gs://brasil-ai-avatars-vault/outputs/final_<JOB_ID>.mp4 sucesso/`
    - **Caminho local:** `sucesso/` na raiz do projeto Avatar. Ex: `C:\Users\vinic\workspace_antigravity\Avatar\sucesso\video.mp4`
8.  **Purga:** A GPU se auto-desliga após o processamento (Sentinel Mode) para garantir custo zero.

---

## 4. Regras de Ouro para Agentes IA
- **NUNCA** mude versões de pacotes em `requirements.txt` sem validar o grafo de dependências (especialmente Protobuf).
- **SEMPRE** use credenciais vindas EXCLUSIVAMENTE do GCP Secret Manager (`secrets_manager.py`). É proibido usar variáveis de ambiente injetadas em bash, fallbacks em texto claro (`brasilai-avatar-2026`), ou consultas SQLite em runtime. Se o Secret Manager falhar, o código deve falhar (Fail-Fast).
- **O BANCO SQLITE** (`gs://brasil-ai-avatars-vault/brasil_ai.db`) é backup offline das chaves do ecossistema. Nunca consulte-o em runtime via Python — use apenas o Secret Manager.
- **A IMAGEM DA API** deve ser leve (sem CUDA).
- **A IMAGEM DO WORKER** deve conter tudo (Imutável), com código como última layer para cache eficiente.
- **WEBHOOK URL** deve ser sempre `http://35.231.46.76:8080/webhook/render-complete` (hardcoded). Nunca use `request.base_url` — proxies e clientes podem injetar `https://`, quebrando a comunicação L4 → API na porta 8080 crua (sem TLS).
- **L4 BOOT:** O código Python do worker (`src/industrial_main.py`) deve ser obtido via `git clone` do repositório GitHub no startup script. NUNCA use `docker cp` da imagem golden (código congelado causa regressão de bugs).
- **ZONE FALLBACK:** Se `us-east1-b` estiver sem capacidade (`ZONE_RESOURCE_POOL_EXHAUSTED`), migrar para `us-east1-c` ou `us-east1-d`. O IP estático `35.231.46.76` é regional e acompanha a migração.

---

*Documento atualizado em 2026-05-06 por Antigravity (v3.2.2).*
