# Specs: Motor Avatar Industrial (Lana / Brasil AI)

## 📌 Visão Geral
**Nome do Projeto**: Avatar Efêmero (Substituição D-ID pelo LatentSync)
**Objetivo Principal**: Substituir os custos altos e a dependência de plataformas de terceiros (como a D-ID) por uma infraestrutura própria baseada em Inteligência Artificial open-source (`ByteDance/LatentSync`) rodando em GPU dedicada na nuvem.
**Público-Alvo/Uso**: Automação final do canal do YouTube **Brasil AI**. A apresentadora oficial (Avatar Lana) lerá o áudio das notícias de forma hiper-realista, sendo todo o fluxo acionado automaticamente pelo *n8n*.

## 🎯 Pilares e Requisitos Fundamentais
1. **Autonomia Financeira**: Pagar estritamente os centavos referentes ao "Tempo de Computação na GPU" (Pay-per-use puro).
   - **REGRA DE DEGRADAÇÃO**: Em caso de falha de alocação ou instabilidade da GPU primaria (como L4 em modo Preemptivo/Spot), o sistema deve SEMPRE tentar o fallback imediato para GPU T4 (Standard) **na mesma região original** antes de acionar qualquer pivotagem para outras regiões (`us-central`, `us-east`, etc).
   - **POLÍTICA DE TERRA ARRASADA (Migração)**: Em caso extremo de mudança obrigatória de região, é estritamente obrigatório rastrear e DESTRUIR todo e qualquer disco persistente, IP estático ou resíduo de infraestrutura deixado na região abandonada, movendo apenas os recursos estritos, garantindo zero chance de custo dobrado oculto.
2. **Zero "Cold Start" (Resposta Imediata) e Container Registry**: O modelo da IA pesa +15GB e a imagem Docker base +6GB. O sistema *não pode* levar minutos baixando, instalando dependências ou sofrendo falhas de "build" a cada boot. 
   - Os modelos (`.pt`) devem ficar num Network Volume (RunPod/GCE) ou serem espelhados em alta velocidade num balde de armazenamento.
   - A Imagem Docker (`lana:vX`) **NÃO** deve ser compilada `from scratch`. Deve ser enviada para o **Google Artifact Registry** ou selada em uma **Custom Machine Image**, baixando o tempo de resposta da primeira renderização para segundos.
      > **Plano de Solução Permanente (Artifact Registry & Cache)**:
      > 1. Exportar a imagem concluída `lana:v6` para o Hub Privado (`us-west4-docker.pkg.dev`), desvinculando o Docker do disco local da VM.
      > 2. Mapear o diretório de cache `-v /mnt/hf_cache:/root/.cache/huggingface` no run-script para erradicar o download de 1.7GB a cada reboot silencioso da máquina.
      > 3. Configurar a Spot VM para **Auto-Destruição Total** (Delete VM + Boot Disk) após 25 minutos de ociosidade, sabendo que a imagem e os modelos estarão 100% isolados fora dela, gerando Custo Absoluto de US$ 0.00.
3. **Escalabilidade Assíncrona e Entrega Local API Local-First**: O Motor de Vídeo deve trabalhar "na espreita":
   - O servidor coloca na fila asíncrona, responde `{"job_id": "123", "status": "processing"}`.
   - O servidor renderiza na pesada L4 NVIDIA GPU.
   - O client fica fazendo "polling" perguntando "já acabou?"
   - Ao final, a API devolve o link temporário do arquivo em vídeo. O script que fez a chamada de API engatilha o download automático e **salva o `.mp4` resultante diretamente na sua máquina física / local**, idêntico à experiência da D-ID.

## 📐 Arquitetura Ideal de Implantação ("D-ID Mirror")
1. **Infraestrutura**: RunPod Serverless com **Network Volume** (Disco fixo de 50GB). 
   - O volume armazena os 15GB de modelos permanentemente.
   - O tempo de inicialização (Cold Start) cai de 15 minutos para ~3 segundos.
2. **Framework AI**: PyTorch + CUDA 12.1 usando o motor `LatentSync`.
3. **Backend Emulador (FastAPI)**:
   - Implementa endpoints `/clips` idênticos ao D-ID.
   - Gerencia uma fila local de jobs asíncronos.
4. **Integração de Continuidade (Brasil AI)**:
   - O script `generate_did_video.py` no workspace `youtube` poderá ser substituído por um que simplesmente aponta para esta nova URL, mantendo 90% da lógica de polling original.

## 🗂 Estrutura Básica Esperada
- `main.py` -> Emulador de API (Endpoints `/clips`).
- `worker.py` -> Motor de inferência (invoca LatentSync).
- `Dockerfile` -> Imagem leve que apenas monta o disco externo com os modelos.
- `demo_lana.py` -> Script cliente para validar o espelhamento da API antes do deploy em produção.
