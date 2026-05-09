# Adapted from latentsync/scripts/inference.py — V1 (progress tracking)
# Override via Dockerfile COPY: infra/docker/inference.py -> /workspace/latentsync/scripts/inference.py

import argparse
import json
import math
import os
from omegaconf import OmegaConf
import torch
from diffusers import AutoencoderKL, DDIMScheduler
from latentsync.models.unet import UNet3DConditionModel
from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline
from accelerate.utils import set_seed
from latentsync.whisper.audio2feature import Audio2Feature
from DeepCache import DeepCacheSDHelper


def _write_progress(progress_file, phase, current, total, message):
    """Escreve progresso da renderizacao em JSON para dashboard near-real-time."""
    if not progress_file:
        return
    try:
        pct = round(100 * current / total) if total > 0 else 0
        with open(progress_file, 'w') as f:
            json.dump({"phase": phase, "current": current, "total": total, "percent": pct, "message": message}, f)
    except Exception:
        pass


def main(config, args):
    progress_file = getattr(args, 'progress_file', None)
    _write_progress(progress_file, "loading", 0, 100, "Carregando modelos e assets...")
    if not os.path.exists(args.video_path):
        raise RuntimeError(f"Video path '{args.video_path}' not found")
    if not os.path.exists(args.audio_path):
        raise RuntimeError(f"Audio path '{args.audio_path}' not found")

    # Check if the GPU supports float16
    is_fp16_supported = torch.cuda.is_available() and torch.cuda.get_device_capability()[0] > 7
    dtype = torch.float16 if is_fp16_supported else torch.float32

    print(f"Input video path: {args.video_path}")
    print(f"Input audio path: {args.audio_path}")
    print(f"Loaded checkpoint path: {args.inference_ckpt_path}")

    scheduler = DDIMScheduler.from_pretrained("configs")
    _write_progress(progress_file, "loading", 15, 100, "Scheduler carregado")

    if config.model.cross_attention_dim == 768:
        whisper_model_path = "checkpoints/whisper/small.pt"
    elif config.model.cross_attention_dim == 384:
        whisper_model_path = "checkpoints/whisper/tiny.pt"
    else:
        raise NotImplementedError("cross_attention_dim must be 768 or 384")

    audio_encoder = Audio2Feature(
        model_path=whisper_model_path,
        device="cuda",
        num_frames=config.data.num_frames,
        audio_feat_length=config.data.audio_feat_length,
    )
    _write_progress(progress_file, "loading", 30, 100, "Whisper audio encoder carregado")

    vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype)
    vae.config.scaling_factor = 0.18215
    vae.config.shift_factor = 0
    _write_progress(progress_file, "loading", 50, 100, "VAE carregado")

    unet, _ = UNet3DConditionModel.from_pretrained(
        OmegaConf.to_container(config.model),
        args.inference_ckpt_path,
        device="cpu",
    )
    _write_progress(progress_file, "loading", 70, 100, "UNet carregado")

    unet = unet.to(dtype=dtype)

    pipeline = LipsyncPipeline(
        vae=vae,
        audio_encoder=audio_encoder,
        unet=unet,
        scheduler=scheduler,
    ).to("cuda")
    _write_progress(progress_file, "loading", 90, 100, "Pipeline montada na GPU")

    # use DeepCache
    if args.enable_deepcache:
        helper = DeepCacheSDHelper(pipe=pipeline)
        helper.set_params(cache_interval=3, cache_branch_id=0)
        helper.enable()
    _write_progress(progress_file, "face_detect", 0, 100, "Detectando rostos e extraindo features de audio...")

    if args.seed != -1:
        set_seed(args.seed)
    else:
        torch.seed()

    print(f"Initial seed: {torch.initial_seed()}")
    _write_progress(progress_file, "inference", 0, 100, "Renderizando... chunks: calculando")

    pipeline(
        video_path=args.video_path,
        audio_path=args.audio_path,
        video_out_path=args.video_out_path,
        num_frames=config.data.num_frames,
        num_inference_steps=args.inference_steps,
        guidance_scale=args.guidance_scale,
        weight_dtype=dtype,
        width=config.data.resolution,
        height=config.data.resolution,
        mask_image_path=config.data.mask_image_path,
        temp_dir=args.temp_dir,
    )

    _write_progress(progress_file, "restore", 0, 100, "Restaurando video (GFPGAN)...")
    _write_progress(progress_file, "encoding", 0, 100, "Codificando video final...")
    _write_progress(progress_file, "done", 100, 100, "Renderizacao concluida")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--unet_config_path", type=str, default="configs/unet.yaml")
    parser.add_argument("--inference_ckpt_path", type=str, required=True)
    parser.add_argument("--video_path", type=str, required=True)
    parser.add_argument("--audio_path", type=str, required=True)
    parser.add_argument("--video_out_path", type=str, required=True)
    parser.add_argument("--inference_steps", type=int, default=20)
    parser.add_argument("--guidance_scale", type=float, default=1.0)
    parser.add_argument("--temp_dir", type=str, default="temp")
    parser.add_argument("--seed", type=int, default=1247)
    parser.add_argument("--enable_deepcache", action="store_true")
    parser.add_argument("--progress_file", type=str, default=None, help="JSON file for real-time progress tracking")
    args = parser.parse_args()

    config = OmegaConf.load(args.unet_config_path)

    main(config, args)
