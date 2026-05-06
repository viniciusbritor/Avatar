# Skill: Atualização de Projeto (Docs, Specs e Git)

**Description:** Execute esta skill para sincronizar a documentação, as especificações arquiteturais e o controle de versão (Git) sempre que uma nova funcionalidade for implementada, um bug resolvido ou alterações estruturais ocorrerem. Garante que o projeto nunca fique com "dívida técnica" de documentação.

## Triggers
WHEN: "atualize a documentacao", "atualize as specs", "feche a issue", "sincronize o projeto", "atualizar projeto".

## Operational Workflow

### Step 1: Análise de Impacto (Diffing)
- Rode `git status` e `git diff` para entender exatamente o que foi modificado no código desde o último commit.
- Identifique se as mudanças afetam a Arquitetura (ex: mudança de portas, serviços, caminhos de deploy) ou a API (mudança de endpoints, payloads).

### Step 2: Atualização da Arquitetura (`ARCHITECTURE.md`)
- Se houver mudanças estruturais, modifique o `ARCHITECTURE.md`.
- Atualize a data e a versão do projeto no rodapé do documento.
- Garanta que as "Regras de Ouro" reflitam o novo estado da arte da segurança/infraestrutura.

### Step 3: Atualização de Manuais (`README.md` e pastas locais)
- Atualize os arquivos README relevantes (ex: `api/README.md`) para garantir que os guias de uso, comandos curl e instruções de teste estejam corretos para o novo código.

### Step 4: Limpeza de Lixo (Sanitização)
- Verifique proativamente a existência de arquivos de teste jogados na raiz (`test*.py`, `temp*`, `.json` órfãos) e delete-os para manter a árvore limpa antes do commit.

### Step 5: Sincronização de Código (Git)
- Rode `git add -A`.
- Escreva um commit semântico extremamente descritivo, no formato `docs: ...` (se foi só doc) ou englobando as `feat/fix` com `docs` anexado. Ex: `git commit -m "fix: corrige X e atualiza specs arquiteturais refletindo a mudanca"`.
- Rode `git push origin master`.
- Confirme ao usuário que a especificação e o repositório estão 100% atualizados.
