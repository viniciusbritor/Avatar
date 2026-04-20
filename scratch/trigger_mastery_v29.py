import sys
import os
import cv2
import torch
from lipsync_pipeline import LipsyncPipeline

def main():
    print("Iniciando Restauração Elite Mastery v29...")
    # Configurações do V29 Mastery
    video_path = "outputs/v29_synced_audio.mp4"
    output_path = "outputs/CRIS_SOBERANA_MASTERY_V29.mp4"
    
    # O LipsyncPipeline já foi atualizado com o Reset V29 (paste_back=True)
    pipeline = LipsyncPipeline()
    
    # Carrega os frames sincronizados
    video = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = video.read()
        if not ret: break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    video.release()
    
    # Processa a restauração Mastery sem bordas
    print(f"Restaurando {len(frames)} frames com lógica Sub-Pixel...")
    # No V29, o synced_video_frames e video_frames serão os mesmos pois já temos o lipsync
    # Mas o pipeline espera os dois.
    restored_video = pipeline.restore_video(frames, frames)
    
    # Salva o resultado final incorporando o áudio original
    pipeline.save_video(restored_video, video_path, output_path)
    print(f"ENTREGA DEFINITIVA CONCLUÍDA: {output_path}")

if __name__ == "__main__":
    main()
