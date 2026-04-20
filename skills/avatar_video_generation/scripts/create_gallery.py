import json
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os

def create_gallery(json_path):
    with open(json_path, 'r', encoding='utf-16') as f:
        data = json.load(f)
    
    women = [p for p in data['presenters'] if p.get('gender') == 'female']
    
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body { 
                background-color: #0f172a; 
                color: #f8fafc; 
                font-family: 'Inter', system-ui, sans-serif; 
                margin: 0; 
                padding: 40px;
            }
            h1 { text-align: center; margin-bottom: 40px; color: #38bdf8; }
            .gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 24px;
                max-width: 1400px;
                margin: 0 auto;
            }
            .card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                overflow: hidden;
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                flex-direction: column;
            }
            .card:hover {
                transform: translateY(-4px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
                border-color: #38bdf8;
            }
            .info { padding: 16px; }
            .name { 
                font-size: 18px; 
                font-weight: 600; 
                margin-bottom: 4px; 
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .id { 
                font-size: 12px; 
                color: #94a3b8; 
                margin-bottom: 12px; 
                word-break: break-all;
                font-family: monospace;
            }
            video { width: 100%; aspect-ratio: 16/9; background: #000; }
        </style>
    </head>
    <body>
        <h1>Catálogo de Avatares D-ID (Feminino)</h1>
        <div class="gallery">
    """
    
    for p in women:
        html += f"""
            <div class="card">
                <video controls preload="none">
                    <source src="{p['talking_preview_url']}" type="video/mp4">
                    Seu navegador não suporta vídeos.
                </video>
                <div class="info">
                    <div class="name">{p['name']}</div>
                    <div class="id">ID: {p['presenter_id']}</div>
                </div>
            </div>
        """
        
    html += """
        </div>
    </body>
    </html>
    """
    
    with open('avatar_gallery.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Galeria criada: avatar_gallery.html")

if __name__ == "__main__":
    create_gallery('c:/Users/vinic/workspace_antigravity/youtube/presenters.json')

