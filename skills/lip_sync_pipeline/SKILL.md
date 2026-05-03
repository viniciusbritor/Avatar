---
name: lip_sync_pipeline
description: Regras e lições aprendidas para modificar a pipeline de lip-sync do LatentSync. Use ao alterar máscara, parâmetros de difusão, ou debug de renderização.
---

# Lip-Sync Pipeline — Regras de Ouro

> **ARQUIVO CERTO:** `latentsync/latentsync/pipelines/lipsync_pipeline.py` (submodule)
> **NUNCA EDITAR:** `src/lipsync_pipeline.py` (código morto, não usado pelo render)

## Máscara da Boca

| Regra | Detalhe |
|---|---|
| Device | **CPU** sempre. NUNCA usar `.to(device=cuda)`. A máscara original fica em CPU. |
| Shape | `(3, h, w)` — 3 canais. Usar `np.stack([mask_np]*3, axis=0)` para replicar. |
| Kernel | Padrão `(3,3)` MORPH_ELLIPSE. Se distorcer: `(1,1)`. Se não resolver: `(5,5)`. |
| Operação | `cv2.erode` expande boca. `cv2.dilate` encolhe boca (causa borrão). |

## Imports

```python
from einops import rearrange  # NUNCA einops.rearrange
import numpy as np             # necessário
```

## Código Padrão (após `load_fixed_mask`)

```python
mask_image = load_fixed_mask(height, mask_image_path)
mask_np = mask_image[0].cpu().numpy()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask_np = cv2.erode(mask_np, kernel, iterations=1)
mask_np = np.stack([mask_np] * 3, axis=0)
mask_image = torch.from_numpy(mask_np)
```

## Deploy

```bash
# scp do submodule (caminho completo) + docker cp + restart
gcloud compute scp latentsync/latentsync/pipelines/lipsync_pipeline.py GPU_VM:/tmp/
gcloud compute ssh GPU_VM --command="sudo docker cp /tmp/lipsync_pipeline.py lana-engine:/workspace/latentsync/latentsync/pipelines/lipsync_pipeline.py"
gcloud compute ssh GPU_VM --command="sudo docker restart lana-engine"
```

## Rollback

```bash
git checkout -- latentsync/latentsync/pipelines/lipsync_pipeline.py
```

## Parâmetros de Render

| Parâmetro | CLI arg | Original | Testado | Efeito |
|---|---|---|---|---|
| guidance_scale | `--guidance_scale` | 1.0 | 1.5 / 3.0 | Maior = mais fiel ao áudio |
| inference_steps | `--inference_steps` | 20 | 20 / 50 | Mais passos = mais qualidade |
| seed | `--seed` | 1247 | remover (aleatório) | Fixo = sempre mesmo ruído |
| deepcache | `--enable_deepcache` | off | on | Melhor qualidade com menos VRAM |

## Erros Conhecidos

| Erro | Causa | Correção |
|---|---|---|
| `einops has no attribute rearrange` | Import errado | `from einops import rearrange` |
| `Expected cuda:0 and cpu` | Máscara na GPU | Manter CPU (não usar `.to(cuda)`) |
| `shape mismatch` | Shape da máscara errado | Usar `(3, h, w)` com `np.stack` |
