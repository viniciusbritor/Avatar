# 🏭 Arquitetura BrasilAI: Core Pipeline V13

Abaixo está a representação oficial em Diagrama (Mermaid) de toda a nossa lógica de orquestração industrial, desde a Caça à Notícia até a Aplicação da Borda e Proteção Anti-Copyright.

```mermaid
graph TD
    classDef init fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#fff
    classDef search fill:#3182ce,stroke:#63b3ed,stroke-width:2px,color:#fff
    classDef create fill:#4ca1af,stroke:#2c3e50,stroke-width:2px,color:#fff
    classDef shield fill:#c53030,stroke:#fc8181,stroke-width:2px,color:#fff
    classDef brand fill:#d69e2e,stroke:#f6e05e,stroke-width:2px,color:#fff
    classDef finish fill:#38a169,stroke:#68d391,stroke-width:2px,color:#fff

    Start(["START: brasil_ia_core_pipeline.py"]) --> S0

    subgraph Fase1 ["FASE 1: VARREDURA E HIGIENE"]
        S0["0. Limpeza do Workspace"]:::init
        S1["1. Pauta Sniper"]:::search
        S2["2. Download HD da Notícia"]:::search
    end

    subgraph Fase2 ["FASE 2: INTELIGÊNCIA VIRTUAL"]
        S3["3. Clipping (Corte do Clímax)"]:::create
        S4["4. Roteirização (LLM)"]:::create
        S5["5. Geração Avatar D-ID"]:::create
    end

    subgraph Fase3 ["FASE 3: BLINDAGEM DE VÍDEO (FAIR USE)"]
        S6["6. Edição V20 Anti-Copyright<br>(Crop 5%, Speeds 1.05x, Cores)"]:::shield
        S7["7. Transcrição Whisper<br>(Legendas)"]:::create
    end

    subgraph Fase4 ["FASE 4: MASTERIZAÇÃO"]
        S8["8. Auditoria de Vídeo QC"]:::create
        S9["9. Branding High-End<br>(Moldura L-Shape 3.5cm + Logo)"]:::brand
    end

    S0 --> S1 --> S2 --> S3
    S3 --> S4 --> S5 --> S6
    S6 --> S7 --> S8 --> S9
    
    S9 --> FINAL(["VÍDEO PRONTO PARA O YOUTUBE"]):::finish
```
