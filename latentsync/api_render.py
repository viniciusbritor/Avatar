import os
import tempfile
import shutil
import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from omegaconf import OmegaConf
from diffusers import AutoencoderKL, DDIMScheduler
from latentsync.models.unet import UNet3DConditionModel
from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline
from latentsync.whisper.audio2feature import Audio2Feature
from accelerate.utils import set_seed
from DeepCache import DeepCacheSDHelper

app = FastAPI(title="LatentSync Render")

CONFIG_PATH = os.environ.get("UNET_CONFIG_PATH", "configs/unet/stage2_512.yaml")
CHECKPOINT_PATH = os.environ.get("CHECKPOINT_PATH", "checkpoints/latentsync_unet.pt")
WHISPER_DIR = os.environ.get("WHISPER_DIR", "checkpoints/whisper")

pipeline = None
config = None
dtype = None


def load_pipeline():
    global pipeline, config, dtype

    config = OmegaConf.load(CONFIG_PATH)
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    scheduler = DDIMScheduler.from_pretrained("configs")

    if config.model.cross_attention_dim == 768:
        whisper_path = os.path.join(WHISPER_DIR, "small.pt")
    elif config.model.cross_attention_dim == 384:
        whisper_path = os.path.join(WHISPER_DIR, "small.pt")
    else:
        raise ValueError("cross_attention_dim must be 768 or 384")

    audio_encoder = Audio2Feature(
        model_path=whisper_path,
        device="cuda",
        num_frames=config.data.num_frames,
        audio_feat_length=config.data.audio_feat_length,
    )

    whisper_projection = None
    if config.model.cross_attention_dim == 384:
        whisper_projection = torch.nn.Linear(768, 384).to(device="cuda", dtype=dtype)

    vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype)
    vae.config.scaling_factor = 0.18215
    vae.config.shift_factor = 0

    unet, _ = UNet3DConditionModel.from_pretrained(
        OmegaConf.to_container(config.model),
        CHECKPOINT_PATH,
        device="cpu",
    )
    unet = unet.to(dtype=dtype)

    pipeline = LipsyncPipeline(
        vae=vae,
        audio_encoder=audio_encoder,
        unet=unet,
        scheduler=scheduler,
    ).to("cuda")

    if whisper_projection is not None:
        pipeline.whisper_projection = whisper_projection

    helper = DeepCacheSDHelper(pipe=pipeline)
    helper.set_params(cache_interval=3, cache_branch_id=0)
    helper.enable()

    print("[API] Pipeline carregado com sucesso.")


@app.on_event("startup")
def startup():
    load_pipeline()


@app.post("/render")
def render(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    inference_steps: int = 20,
    guidance_scale: float = 1.5,
    seed: int = 1247,
):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline nao inicializado")

    work_dir = tempfile.mkdtemp(prefix="latentsync_")
    try:
        video_path = os.path.join(work_dir, "input.mp4")
        audio_path = os.path.join(work_dir, "input.wav")
        output_path = os.path.join(work_dir, "output.mp4")

        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

        if seed != -1:
            set_seed(seed)
        else:
            torch.seed()

        pipeline(
            video_path=video_path,
            audio_path=audio_path,
            video_out_path=output_path,
            num_frames=config.data.num_frames,
            num_inference_steps=inference_steps,
            guidance_scale=guidance_scale,
            weight_dtype=dtype,
            width=config.data.resolution,
            height=config.data.resolution,
            mask_image_path=config.data.mask_image_path,
            temp_dir=os.path.join(work_dir, "temp"),
        )

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Falha ao gerar video")

        return FileResponse(output_path, media_type="video/mp4", filename="output.mp4")

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        torch.cuda.empty_cache()


@app.get("/health")
def health():
    return {"status": "ok", "gpu_available": torch.cuda.is_available()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
