# Especificações Técnicas: Infraestrutura Industrial Lana v3.0 (V17.1 Tuning)

## 🖥️ Hardware Mandatório (Benchmark Gold)
Para garantir a estabilidade do pipeline de renderização HD (LatentSync + GFPGAN), a infraestrutura DEVE seguir os parâmetros abaixo:

- **Instância:** `g2-standard-12`
- **CPU:** 12 vCPUs
- **Memória RAM:** 48 GB (Mínimo necessário para evitar OOM na finalização)
- **Acelerador:** 1x NVIDIA L4 (24GB VRAM)
- **Disco:** 100 GB (Balanced PD)

## 🎞️ Imagem de Máquina (Gold Image)
- **Versão Atual:** `lana-v6-industrial-v1` (Zero-Waste: Pesos embutidos, sem discos externos)
- **Data de Registro:** 22/04/2026
- **Family:** `lana-industrial-v6`

## 🛡️ Notas de Blindagem
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
- **Fluxo de Infra:** [INFRASTRUCTURE_FLOW.md](file:///c:/Users/vinic/workspace_antigravity/Avatar/docs/INFRASTRUCTURE_FLOW.md) (Diagrama de Sequência)

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
