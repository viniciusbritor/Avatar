---
description: Renderiza fluxos Mermaid como HTML interativo e abre no navegador. Use quando o usuario pedir para visualizar fluxo, pipeline, orquestracao, diagrama, mermaid, ou arquitetura.
mode: subagent
permission:
  write: allow
  edit: allow
  bash: allow
---

# Skill: Visualizador de Fluxos Mermaid

Quando o usuario solicitar "visualizar fluxo", "abrir diagrama", "ver pipeline", ou qualquer pedido de visualizacao de fluxo/orquestracao/arquitetura:

## Procedimento

### 1. Criar ou atualizar o arquivo .mermaid

Salve o diagrama Mermaid em `.temp/fluxo_{nome}.mermaid` com comentarios descritivos usando `%%`.

Formato obrigatorio:
```
flowchart TD
    NODE1["descricao"]
    NODE2{"decisao"}
    NODE1 --> NODE2
```

Convencoes:
- Use `[]` para nos de processo (retangulo)
- Use `{}` para nos de decisao (losango)
- Use `-->` para fluxo sincrono (linha cheia)
- Use `-.->` para fluxo assincrono/polling (linha pontilhada)
- Use `-- "texto" -->` para arestas com label
- Use emojis como prefixo para legibilidade
- Use subgraphs com `subgraph ID["titulo"]` para agrupar fases
- Inclua comentarios `%%` explicando cada secao
- Mantenha labels concisos mas informativos

### 2. Criar HTML renderizavel

Gere `.temp/fluxo_{nome}.html` com este template:

```html
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<title>{TITULO}</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'dark', flowchart:{useMaxWidth:true,htmlLabels:true}, securityLevel:'loose'});</script>
<style>
  body { background: #0c0e12; margin: 0; padding: 16px; }
  h2 { color: #a1faff; font-family: sans-serif; font-size: 14px; }
</style>
</head>
<body>
<h2>{TITULO}</h2>
<pre class="mermaid">
{CONTEUDO_DO_MERMAID}
</pre>
</body>
</html>
```

IMPORTANTE: O conteudo do Mermaid dentro da tag `<pre class="mermaid">` deve ser o codigo PURO do Mermaid, exatamente como esta no arquivo .mermaid, sem aspas extras ou escapes.

### 3. Abrir no navegador

```bash
start .temp/fluxo_{nome}.html
```

### 4. Confirmar

Informe ao usuario: "Fluxo aberto em `.temp/fluxo_{nome}.html`"

## Exemplo de uso

Usuario: "me mostre o fluxo de autenticacao"
→ 1. Analisa o codigo de auth no projeto
→ 2. Cria `.temp/fluxo_auth.mermaid` com o diagrama
→ 3. Cria `.temp/fluxo_auth.html` 
→ 4. Abre no navegador
