# Especificações Técnicas Operacionais — Avatar v3.1.6

Este documento contém as definições técnicas para operação, manutenção e escalonamento do ecossistema.

## 1. Definições de API (Cérebro)
- **URL Base:** `https://avatar-api-180096224219.us-east1.run.app`
- **Endpoints Principais:**
    - `POST /produce`: Início do processo assíncrono.
    - `GET /status/{job_id}`: Consulta estado no Firestore.
    - `GET /health`: Diagnóstico de infraestrutura.
    - `POST /webhook/render-complete`: Ponto de retorno da GPU.

## 2. Configurações de Nuvem (GCP)
- **Projeto:** `brasili-ia-news`
- **Região Primária:** `us-east1`
- **VPC / Rede:** `default` (com acesso IAP para SSH).
- **Service Account (API):** `avatar-api-sa@brasili-ia-news.iam.gserviceaccount.com` (Permissões: Compute Admin, Cloud Tasks Enqueuer, Secret Manager Accessor, Firestore User).

## 3. Imagens Docker Oficiais (Artifact Registry)
- **API Image:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-api:v3.1.6`
- **Worker Image:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/avatar-l4:v2.9`

## 4. O Agente de Ponte (Local Bridge)
- **Script:** `src/sync_bridge.py`
- **Tecnologia:** Google Cloud Pub/Sub (Subscriber).
- **Missão:** Download automático via trigger instantâneo.
- **Configuração:** Deve rodar como serviço em background na máquina do usuário.

## 5. FinOps & Custos (Zero-Waste)
- **Cloud Run:** Cobrança apenas por requisição.
- **Compute Engine (L4):** Cobrança por segundo de uso.
- **GCS Fuse:** Evita custos de tráfego interno ao não baixar pesos de modelos entre regiões (Streaming).
- **Self-Destruction:** Shutdown em 60 minutos garantido via script de startup.

## 6. Checklist de Manutenção
1.  Verificar cotas de GPU L4 anualmente ou em caso de aumento de demanda.
2.  Garantir que a chave `API_SECRET_KEY` no Secret Manager não foi rotacionada sem atualizar a API.
3.  Monitorar a fila `avatar-render-queue` para identificar gargalos de provisionamento.

---
*Status: Industrial v3.1.6 - Todos os sistemas nominais.*
