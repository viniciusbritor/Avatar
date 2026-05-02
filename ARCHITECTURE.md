# Arquitetura Industrial Avatar (v3.1.6) — "Cérebro & Motor"

Este documento é a especificação soberana do ecossistema Brasil AI Avatar. Toda e qualquer modificação no código deve respeitar os pilares de **Zero-Waste**, **Cloud-Native** e **Blindagem de Segurança** aqui descritos.

---

## 1. Visão Geral (The Grand Design)
O sistema é dividido em duas camadas de responsabilidade distinta, conectadas via **Cloud Tasks** e **Pub/Sub**:

1.  **O Cérebro (API v3.1.6):** Servidor FastAPI rodando em Google Cloud Run. Responsável pela inteligência, orquestração e gestão de fila.
2.  **O Motor (L4 Engine):** Instâncias NVIDIA L4 (Compute Engine) dinâmicas, que nascem e morrem conforme a demanda, focadas exclusivamente em renderização pesada.

---

## 2. Componentes da Infraestrutura

### 2.1 API Cérebro (Cloud Run)
- **Tecnologia:** Python 3.11, FastAPI.
- **Orquestrador:** Agente Lana (Maestro via Agno/Phidata).
- **Segurança:** Autenticação via `X-API-Key` (validada contra Secret Manager).
- **Missão:** Receber requisições, gerar áudio (ElevenLabs), e despachar o job para a fila.

### 2.2 Gerenciamento de Fila (Cloud Tasks)
- **Fila:** `avatar-render-queue`.
- **Papel:** Blindar a API contra picos de tráfego. O Cloud Tasks gerencia retentativas automáticas caso a GPU falhe no boot.
- **Deadline:** 30 minutos por tentativa.

### 2.3 Motor de IA (Compute Engine L4)
- **Hardware:** `g2-standard-12` (NVIDIA L4 24GB VRAM).
- **Estratégia de Boot:** Arquitetura 4 (Nativa).
    - **Golden Disks:** Modelos pesados são montados via **GCS Fuse** em `/mnt/weights` (Zero download time).
    - **Startup Script:** Configura o Docker e Nvidia Toolkit em segundos.
    - **Docker Image:** `avatar-l4:v2.10` (Layers otimizadas, todas deps baked, código incluso).

### 2.4 Devolução e Gatilho (Firestore + GCS)
- **Storage:** Vídeos salvos em `gs://brasil-ai-avatars-vault/outputs/`.
- **Trigger:** O webhook da GPU atualiza o Firestore com status `completed` + `video_path`.
- **Local Bridge:** `sync_bridge.py` faz polling no Firestore (sem dependência de Pub/Sub) e baixa o vídeo para `sucesso/` assim que detecta o status `completed`.

---

## 3. Fluxo Industrial (Step-by-Step)

1.  **Injeção:** Usuário chama `POST /produce` na API.
2.  **Enfileiramento:** API salva o job no **Firestore** como `queued` e cria uma Task no Cloud Tasks.
3.  **Despacho:** O Cloud Tasks aciona o Worker interno da API, que invoca o **Maestro**.
4.  **Caça por GPU:** O Maestro busca globalmente (13+ zonas) por uma GPU L4. Se necessário, cria uma nova.
5.  **Processamento:** A GPU executa o Lip Sync e sobe o vídeo para o GCS.
6.  **Callback:** O Worker avisa a API via Webhook que o vídeo está pronto.
7.  **Entrega:** O sync_bridge local (polling Firestore) detecta o status `completed`, baixa o vídeo do GCS, e salva em `sucesso/`.
8.  **Purga:** A GPU se auto-desliga após o processamento (Sentinel Mode) para garantir custo zero.

---

## 4. Regras de Ouro para Agentes IA
- **NUNCA** mude versões de pacotes em `requirements.txt` sem validar o grafo de dependências (especialmente Protobuf).
- **SEMPRE** use `X-API-Key` vinda do Secret Manager.
- **A IMAGEM DA API** deve ser leve (sem CUDA).
- **A IMAGEM DO WORKER** deve conter tudo (Imutável), com código como última layer para cache eficiente.

---

*Documento atualizado em 2026-05-02 por Antigravity (v3.1.6-r2).*
