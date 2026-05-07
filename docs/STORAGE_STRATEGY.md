# 🛡️ Estratégia de Armazenamento Industrial: Lana V6

Para garantir a segurança, rastreabilidade e escalabilidade do projeto Lana, todos os arquivos fundamentais devem ser organizados em locais especializados.

## 1. 📂 Repositório de Código & Lógica (GitHub)
**Local:** [viniciusbritor/Avatar](https://github.com/viniciusbritor/Avatar)
**Finalidade:** Versão de verdade de toda a inteligência do projeto.

| Categoria | Arquivos Principais | Local Recomendado |
| :--- | :--- | :--- |
| **Orquestração** | `agente_lana_orchestrator.py`, `lana_mcp_server.py` | Root / `core/` |
| **Pipelines** | `lipsync_pipeline.py`, `industrial_main.py` | `engine/` |
| **Infraestrutura** | `Dockerfile`, `startup-script.sh`, `requirements.txt` | `infra/` |
| **Documentação** | `Specs.md`, `DASHBOARD_INDUSTRIAL.md`, `README.md` | Root / `docs/` |
| **Testes** | `test_industrial_v6.py` | `tests/` |

> [!TIP]
> **Ação Recomendada:** Criar uma estrutura de pastas (`src/`, `infra/`, `docs/`) e mover os arquivos soltos na raiz para limpar o workspace.

---

## 2. 🗄️ Cofre de Ativos & Modelos (GCS Vault)
**Local:** `gs://brasil-ai-avatars-vault/` (Google Cloud Storage)
**Finalidade:** Armazenamento de arquivos binários pesados e entrega de resultados.

*   **`/checkpoints/`**: Backups dos pesos dos modelos (LatentSync, GFPGAN).
*   **`/outputs/`**: Todos os vídeos finais renderizados (organizados por `/YYYY-MM/`).
*   **`/assets/`**: Vídeos de referência (Lana Base) e fundos.
*   **`/temp/`**: Áudios gerados pelo ElevenLabs durante o processo.

---

## 3. 💿 Imagem de Máquina Soberana (GCP Compute Registry)
**Local:** `lana-v6-industrial-v1`
**Finalidade:** Estado imutável do sistema.

*   Contém todas as dependências (CUDA, Python, Conda).
*   Contém os pesos "baked" em `/workspace` para evitar downloads em tempo de execução.
*   **Backup:** Deve ser mantida como imagem registrada, não como disco ativo.

---

## 4. 🔑 Gerenciamento de Segredos (Secret Manager)
**Local:** `brasil_ai.db` (SQLite Local) + **GCP Secret Manager** (Produção)
**Finalidade:** Evitar chaves hardcoded no código.

| Chave | Descrição | Status |
| :--- | :--- | :--- |
| `ELEVENLABS_API_KEY` | Acesso ao motor de voz Matilda (pt-BR) | 🔒 Protegido |
| `GCP_PROJECT_ID` | brasili-ia-news | 🔒 Protegido |
| `GCS_VAULT_BUCKET` | brasil-ai-avatars-vault | 🔒 Protegido |

**CI/CD Auth (Workload Identity Federation):** GitHub Actions autentica via OIDC (pool `github-actions-pool`), sem Service Account Key exportada. SA dedicada `github-actions-sa@brasili-ia-news.iam.gserviceaccount.com` com least-privilege:

> [!IMPORTANT]
> **Próximo Passo:** Migrar a chave do ElevenLabs que ainda está hardcoded no `agente_lana_orchestrator.py` para o `secrets_manager`.

---

## 🏗️ Estrutura do Workspace Local (Finalizada)

O diretório `Avatar/` foi reorganizado para seguir padrões de engenharia industrial:

```text
Avatar/
├── .git/
├── .gitignore
├── src/                    # Inteligência e Orquestração
│   ├── agente_lana_orchestrator.py
│   ├── lana_mcp_server.py
│   ├── lipsync_pipeline.py
│   ├── industrial_main.py
│   ├── secrets_manager.py
│   └── brasil_ai.db        # Banco de Segredos Local (Criptografado/Seguro)
├── infra/                  # Configuração de Sistemas e Containers
│   ├── Dockerfile
│   ├── startup-script.sh
│   ├── boot_industrial_v18.sh
│   ├── requirements.txt
│   ├── desligar_lana.bat
│   └── ligar_lana.bat
├── docs/                   # Governança e Especificações
│   ├── Specs.md
│   ├── DASHBOARD_INDUSTRIAL.md
│   ├── INFRASTRUCTURE_FLOW.md
│   └── STORAGE_STRATEGY.md
├── tests/                  # Scripts de Validação
│   └── test_industrial_v6.py
├── legacy/                 # Arquivamento de Versões Anteriores (Limpeza)
└── outputs/                # Entrega de Ativos (Gera filenames com timestamp)
```

**Conformidade Industrial:**
1. **Zero-Waste**: Ativado (Purga automática transregional).
2. **Security**: Segredos centralizados no `src/brasil_ai.db`.
3. **Traceability**: Documentação versionada em `/docs`.
4. **Resiliency**: Failover global implementado no `agente_lana_orchestrator.py`.
