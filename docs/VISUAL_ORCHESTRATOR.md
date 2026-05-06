# Orquestrador — Brasil AI Avatar v3.2.1

## Fluxo de Renderização

```mermaid
graph TD
    A[POST /produce] --> B[TTS ElevenLabs]
    B --> C[Upload GCS]
    C --> D[Firestore: queued]
    D --> E[GPU spawn]
    
    subgraph "GPU L4 — startup_arch4.sh"
        E --> F[Docker + NVIDIA Toolkit]
        F --> G[GCS Fuse mount]
        G --> H[Pull golden image v2.10]
        H --> I[docker cp src/ + latentsync/]
        I --> J[docker run lana-engine]
    end
    
    J --> K[polling Firestore]
    K --> L[Baixar audio]
    L --> M[LatentSync Inference]
    M --> N[GFPGAN Restoration]
    N --> O[ffmpeg mux]
    O --> P[Upload GCS]
    P --> Q[Webhook → completed]
    Q --> R[sync_bridge download]
    R --> S[GPU auto-shutdown]
```

## Parâmetros de Render (v3.2.1)

| Parâmetro | Valor |
|---|---|
| Whisper | small.pt + projeção 768→384 |
| Guidance | 2.5 |
| Steps | 20 |
| DeepCache | ON |
| Voz | Matilda (XrExE9yKIg1WjnnlVkGX) |
| Template | lana_comentario.mp4 |
| GFPGAN | ON |

## Shutdown

| Camada | Tempo | Onde roda |
|---|---|---|
| Sentinel HOST (idle GPU) | 30 min | systemd na VM |
| Sentinel HOST (container morto) | 30 min | systemd na VM |
| Dead Man Switch | 90 min | `at` command |
