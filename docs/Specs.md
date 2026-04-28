# Especificações Técnicas: Infraestrutura Industrial Lana v3.0 (V17.1 Tuning)

## 🖥️ Hardware Mandatório (Benchmark Gold)
Para garantir a estabilidade do pipeline de renderização HD (LatentSync + GFPGAN), a infraestrutura DEVE seguir os parâmetros abaixo:

- **Instância:** `g2-standard-12`
- **CPU:** 12 vCPUs
- **Memória RAM:** 48 GB (Mínimo necessário para evitar OOM na finalização)
- **Acelerador:** 1x NVIDIA L4 (24GB VRAM)
- **Disco:** 100 GB (Balanced PD)

## 🎞️ Imagem de Máquina (Arquitetura 4 - Stateless)
- **Imagem Base (OS):** `common-cu129-ubuntu-2204-nvidia-580` (GCP Deep Learning VM). Vem com drivers NVIDIA instalados de fábrica.
- **Projeto GCP:** `deeplearning-platform-release`
- **Tamanho do Disco Host:** 150GB
- **Container Engine:** `us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4-avatar:v2.0` (Imunizada com PyTorch 2.5 + GFPGAN)
- **Pesos (Modelos):** Armazenados no `gs://lana-weights-universal/checkpoints/` e transmitidos sob demanda via GCS Fuse. Zero download local.

## 🛡️ Notas de Blindagem e Protocolo de Pré-Voo (Mandatório)
Antes de iniciar qualquer Job, o Orquestrador DEVE validar a "Santíssima Trindade" da produção:
1.  **Código-Fonte:** Verificar existência de `/workspace/latentsync`. Se ausente, restaurar via Git.
2.  **Pesos de IA:** Verificar integridade de `/mnt/weights`. Se ausente, abortar e alertar o usuário.
3.  **Dependências:** Verificar presença de `omegaconf` e `diffusers` no ambiente Python.

- O escopo da máquina deve incluir `cloud-platform` para acesso total ao Artifact Registry e Storage.
- Variáveis de ambiente `PYTHONPATH` e `LD_LIBRARY_PATH` devem ser injetadas no boot via startup-script.

## 📦 Persistência e FinOps (Zero-Waste)
- **Vault (GCS):** `gs://brasil-ai-avatars-vault/`
- **Entrega Local:** Cópia automática para o notebook do usuário com caminho absoluto verificado.
- **Naming Convention:** `lana_DD_MM_YYYY_HH_MM_SS_{job_id}.mp4` (Rastreabilidade Industrial).
- **Limpeza Automática:** Instâncias e discos temporários são destruídos imediatamente após o hand-off do vídeo.

## 🎙️ Tuning de Voz (V17.1)
- **Modelo:** ElevenLabs Sarah (Multilingual V2).
- **Parâmetros:** Stability 0.4 / Similarity 0.9 / Style 0.2 / Speaker Boost ON.
- **Processamento:** Aceleração via FFmpeg em `1.18x` para naturalidade e cadência profissional.

## 📊 Governança e Monitoramento
- **Dashboard:** [DASHBOARD_INDUSTRIAL.md](file:///c:/Users/vinic/workspace_antigravity/Avatar/docs/DASHBOARD_INDUSTRIAL.md) (Status em tempo real)
- **Telemetria Triple-Bar:** O orquestrador DEVE exibir três barras de progresso reativas (atualização instantânea a cada evento):
  1. **[INFRA ]:** Ciclo de vida da máquina (Provisionamento, SSH, Heartbeat).
  2. **[DOCKER]:** Ciclo de vida do ambiente (Carga do motor, Pull de pesos, Health Check).
  3. **[AVATAR]:** Ciclo de vida criativo (TTS, Renderização, Upload Final).
- **Fluxo de Infra:** [INFRASTRUCTURE_FLOW.md](file:///c:/Users/vinic/workspace_antigravity/Avatar/docs/INFRASTRUCTURE_FLOW.md)

## 🏗️ Arquitetura e Orquestração
- **Arquivo Mestre:** [agente_lana_orchestrator.py](file:///c:/Users/vinic/workspace_antigravity/Avatar/src/agente_lana_orchestrator.py)
- **Bridge Server:** [lana_mcp_server.py](file:///c:/Users/vinic/workspace_antigravity/Avatar/src/lana_mcp_server.py) (Ponte SSH Stdio para comandos seguros).
- **Engine:** `LanaIndustrialEngine` (Responsável pelo provisionamento, failover de zona e IAP Tunneling).
- **Protocolo:** MCP (Model Context Protocol) via túnel IAP para segurança máxima.

## 🧪 Validação e QA
- **Script de Teste E2E:** [test_industrial_v6.py](file:///c:/Users/vinic/workspace_antigravity/Avatar/tests/test_industrial_v6.py) (Validação completa do pipeline desde o spawn até a entrega local).

## 🌍 Disponibilidade Global e Resiliência
- **Mandato de Busca Autônoma:** Em caso de `STOCKOUT` (falta de estoque) na zona primária, o orquestrador DEVE buscar a infraestrutura alvo (`g2-standard-12`) em qualquer região global disponível (EUA, Europa, Ásia), priorizando menor latência, mas garantindo a entrega do hardware mandatório.
- **Failover Automático:** A falha em uma região não deve interromper o pipeline; o agente deve iterar sobre a lista de zonas até obter sucesso no provisionamento.
