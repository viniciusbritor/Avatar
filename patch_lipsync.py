import torch
import torch.nn.functional as F
from gfpgan import GFPGANer
import numpy as np

def patched_restore_video(self, synced_video_frames, video_frames, boxes, affine_matrices):
    print("[CRYSTAL] Aplicando restauração facial GFPGAN v1.4...")
    
    # Initialize GFPGANer
    # Use the backbone checkpoint we restored
    restorer = GFPGANer(
        model_path='/workspace/latentsync/checkpoints/gfpgan/GFPGANv1.4.pth',
        upscale=1,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=None
    )

    # Transform frames to list of numpy BGR
    # synced_video_frames is [C, T, H, W] in [0, 1]
    # We need to loop over T
    
    # Change from [C, T, H, W] to [T, H, W, C]
    synced_video_frames = synced_video_frames.permute(1, 2, 3, 0).cpu().numpy()
    synced_video_frames = (synced_video_frames * 255).astype(np.uint8)
    
    restored_frames = []
    for i in range(len(synced_video_frames)):
        img = synced_video_frames[i]
        # GFPGAN expects BGR
        img_bgr = img[:, :, ::-1]
        
        _, _, restored_img = restorer.enhance(img_bgr, has_aligned=False, only_center_face=False, paste_back=True)
        
        # Back to RGB
        restored_img_rgb = restored_img[:, :, ::-1]
        restored_frames.append(restored_img_rgb)
        
    restored_frames = np.stack(restored_frames)
    # Back to Tensor [C, T, H, W] in [0, 1]
    restored_frames = torch.from_numpy(restored_frames).permute(3, 0, 1, 2).float() / 255.0
    
    return restored_frames
