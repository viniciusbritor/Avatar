"""
sync_bridge.py — Brasil AI Avatar Local Bridge (v2.0)
--------------------------------------------------------
Agente de entrega que faz polling no Firestore para detectar
vídeos concluídos e baixa automaticamente para a máquina local.

Modos:
    python sync_bridge.py           # Polling contínuo (5s)
    python sync_bridge.py --once    # Executa uma vez e sai
    python sync_bridge.py --watch 30  # Polling com intervalo customizado (segundos)

Fluxo:
    1. Consulta Firestore: jobs com status="completed" sem downloaded_at
    2. Download do GCS via Storage SDK
    3. Salva em sucesso/
    4. Marca job com downloaded_at no Firestore
"""

import os
import sys
import time
import argparse
from datetime import datetime, timezone

from google.cloud import firestore
from google.cloud import storage

PROJECT_ID = "brasili-ia-news"
BUCKET_NAME = "brasil-ai-avatars-vault"
LOCAL_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sucesso"
)

os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)


def download_video(job_id: str, gcs_blob_name: str) -> str:
    """Baixa o vídeo do GCS para a máquina local."""
    filename = os.path.basename(gcs_blob_name)
    local_path = os.path.join(LOCAL_OUTPUT_DIR, filename)

    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    parts = gcs_blob_name.replace(f"gs://{BUCKET_NAME}/", "").split("/", 1)
    blob_path = parts[1] if len(parts) > 1 else parts[0]

    blob = bucket.blob(blob_path)
    blob.download_to_filename(local_path)

    return local_path


def mark_downloaded(db: firestore.Client, job_id: str):
    """Marca o job como baixado no Firestore."""
    db.collection("avatar_jobs").document(job_id).update({
        "downloaded_at": datetime.now(timezone.utc).isoformat()
    })


def process_pending(db: firestore.Client) -> int:
    """Processa todos os jobs completados pendentes de download. Retorna quantos foram baixados."""
    jobs_ref = db.collection("avatar_jobs")
    
    all_completed = list(
        jobs_ref.where("status", "==", "completed").stream()
    )

    pending = [
        doc for doc in all_completed
        if "downloaded_at" not in doc.to_dict()
    ]

    if not pending:
        return 0

    downloaded = 0
    for doc in pending:
        job = doc.to_dict()
        job_id = job.get("job_id", doc.id)
        video_path = job.get("video_path", "")

        if not video_path:
            print(f"[BRIDGE] Job {job_id} sem video_path, pulando.")
            continue

        print(f"[BRIDGE] Novo video detectado: {job_id}")
        print(f"[BRIDGE] Origem: {video_path}")

        try:
            local_path = download_video(job_id, video_path)
            file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
            print(f"[BRIDGE] Download concluido: {local_path} ({file_size_mb:.1f} MB)")
            mark_downloaded(db, job_id)
            print(f"[BRIDGE] Job {job_id} marcado como baixado no Firestore.")
            downloaded += 1
        except Exception as e:
            print(f"[BRIDGE] ERRO ao baixar job {job_id}: {e}")

    return downloaded


def run_once():
    """Modo one-shot: processa pendentes e sai."""
    db = firestore.Client(project=PROJECT_ID)
    downloaded = process_pending(db)

    if downloaded > 0:
        print(f"SUCESSO: {downloaded} video(s) baixado(s) para {LOCAL_OUTPUT_DIR}")
    else:
        print("Nenhum video pendente de download.")
    db.close()


def run_watch(interval: int = 5):
    """Modo watch: polling contínuo no Firestore."""
    db = firestore.Client(project=PROJECT_ID)

    print(f"[BRIDGE] Modo Watch ativado. Polling a cada {interval}s.")
    print(f"[BRIDGE] Pasta de destino: {LOCAL_OUTPUT_DIR}")
    print(f"[BRIDGE] Aguardando videos concluidos...")

    try:
        while True:
            downloaded = process_pending(db)
            if downloaded > 0:
                print(f"[BRIDGE] Baixados: {downloaded}. Aguardando proximo...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[BRIDGE] Encerrado pelo usuario.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Brasil AI Avatar - Local Bridge")
    parser.add_argument(
        "--once", action="store_true",
        help="Executa uma vez (processa pendentes e sai)"
    )
    parser.add_argument(
        "--watch", type=int, nargs="?", const=5, default=None,
        help="Polling continuo com intervalo em segundos (default: 5s)"
    )

    args = parser.parse_args()

    if args.once:
        run_once()
    elif args.watch is not None:
        run_watch(interval=args.watch)
    else:
        run_watch(interval=5)


if __name__ == "__main__":
    main()
