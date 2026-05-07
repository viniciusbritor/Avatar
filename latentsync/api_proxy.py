import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI(title="LatentSync Proxy")

L4_URL = os.environ.get("L4_URL", "http://localhost:8000")
TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "600"))


@app.post("/process")
async def process(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    inference_steps: int = 20,
    guidance_scale: float = 1.5,
    seed: int = 1247,
):
    video_bytes = await video.read()
    audio_bytes = await audio.read()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{L4_URL}/render",
                data={
                    "inference_steps": inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed,
                },
                files={
                    "video": (video.filename or "input.mp4", video_bytes, video.content_type or "video/mp4"),
                    "audio": (audio.filename or "input.wav", audio_bytes, audio.content_type or "audio/wav"),
                },
            )
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Render timed out")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Render unreachable: {e}")

    return StreamingResponse(
        resp.iter_bytes(),
        media_type="video/mp4",
        headers={"Content-Disposition": "attachment; filename=output.mp4"},
    )


@app.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{L4_URL}/health")
            return {"status": "ok", "l4": r.json()}
        except Exception:
            return {"status": "degraded", "l4": "unreachable"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
