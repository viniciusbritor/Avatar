---
name: git-auth
description: Autentica o GitHub CLI (gh) extraindo o GITHUB_TOKEN do vault SQLite local. Use quando gh não estiver autenticado ou o token expirar. Garante acesso total à API do GitHub.
---

# Git Auth — Autenticação GitHub CLI

> **VAULT:** `C:/Users/vinic/brasil_ai.db`
> **CHAVE:** `GITHUB_TOKEN` na tabela `secrets`
> **FERRAMENTA:** GitHub CLI (`gh`) instalado em `C:\Program Files\GitHub CLI\gh.exe`

## Triggers
WHEN: `gh auth status` retorna "not logged in", falha ao usar `gh` CLI, erro 401 da GitHub API, "autenticar git", "logar no github", "github token".

## Passo 1: Instalar GitHub CLI (se ausente)

```powershell
winget install --id GitHub.cli --silent --accept-package-agreements
```

Verificar instalação:
```powershell
Test-Path "C:\Program Files\GitHub CLI\gh.exe"
```

## Passo 2: Extrair Token do Vault SQLite

Script de extração (`get_gh_token.py`):

```python
import sqlite3
conn = sqlite3.connect("C:/Users/vinic/brasil_ai.db")
row = conn.execute("SELECT value FROM secrets WHERE key = 'GITHUB_TOKEN'").fetchone()
print(row[0] if row else "")
conn.close()
```

**Execução via PowerShell:**

```powershell
$tempScript = Join-Path $env:TEMP "get_gh_token.py"
Set-Content -LiteralPath $tempScript -Value @'
import sqlite3
conn = sqlite3.connect("C:/Users/vinic/brasil_ai.db")
row = conn.execute("SELECT value FROM secrets WHERE key = 'GITHUB_TOKEN'").fetchone()
print(row[0] if row else "")
conn.close()
'@
$token = python $tempScript
Remove-Item $tempScript
```

**IMPORTANTE:** Sempre usar arquivo temporário para evitar problemas de escaping de aspas no PowerShell. NUNCA tentar inline com aspas aninhadas.

## Passo 3: Autenticar

```powershell
$env:PATH = "C:\Program Files\GitHub CLI;$env:PATH"
$token | gh auth login --with-token
```

## Passo 4: Verificar

```powershell
$env:PATH = "C:\Program Files\GitHub CLI;$env:PATH"
gh auth status
```

Saída esperada:
```
github.com
  ✓ Logged in to github.com account viniciusbritor (keyring)
```

## Erros Conhecidos

| Erro | Causa | Correção |
|---|---|---|
| `CommandNotFoundException: gh` | `gh.exe` fora do PATH | Adicionar `C:\Program Files\GitHub CLI` ao PATH |
| `SyntaxError: '(' was never closed` | Aspas aninhadas no PowerShell | Usar arquivo `.py` temporário (Passo 2) |
| Abre browser de login | Token vazio/nulo pipeado | Verificar se `$token` não é vazio antes do pipe |
| `Keyring access error` | Permissões do Windows | Re-executar como `cmd /c gh auth login --with-token` |

## Rollback / Logout

```powershell
$env:PATH = "C:\Program Files\GitHub CLI;$env:PATH"
gh auth logout
```
