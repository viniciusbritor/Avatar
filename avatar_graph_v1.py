import os
import time
import subprocess
import requests
import json
import sqlite3
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# --- CONFIGURAÇÕES INDUSTRIAIS ---
PROJECT_ID = "brasili-ia-news"
ZONE = "us-east4-a"
INSTANCE_NAME = "lana-engine-v25-final-industrial"
MACHINE_IMAGE = "lana-engine-master-v31-gold-standard"
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah Original (Gold)

class AvatarState(TypedDict):
    texto: str
    vm_ip: str
    audio_path: str
    video_path: str
    status_history: List[str]
    error: str

# --- DASHBOARD VISUAL ---
def print_dashboard(state: AvatarState, current_step: str, progress: int):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print(">>> AVATAR ORCHESTRATOR V1.2 (LANGGRAPH)")
    print("="*60)
    print(f"TEXTO: {state['texto'][:50]}...")
    print(f"IP VM: {state.get('vm_ip', 'Offline')}")
    print(f"PASSO ATUAL: {current_step}")
    
    # Barra de Progresso
    bar = "[" + "#" * (progress // 10) + "-" * (10 - (progress // 10)) + "]"
    print(f"PROGRESSO: {bar} {progress}%")
    print("-" * 60)
    for log in state['status_history'][-5:]:
        print(f"* {log}")
    print("="*60)

# --- NÓS DO GRAFO ---

def node_prepare_infra(state: AvatarState):
    state['status_history'].append("Auditando Infraestrutura GCP via JSON...")
    
    try:
        # Consulta robusta via JSON
        cmd = f"gcloud compute instances describe {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --format=json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Caso a VM realmente não exista
            state['status_history'].append("VM nao encontrada. Criando nova do Snapshot...")
            create_cmd = f"gcloud compute instances create {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --source-machine-image={MACHINE_IMAGE} --metadata startup-script=\"\" --quiet"
            subprocess.run(create_cmd, shell=True, check=True)
            # Re-consulta para pegar os dados novos
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        data = json.loads(result.stdout)
        vm_status = data.get("status", "").upper()
        
        if vm_status == "RUNNING":
            state['status_history'].append("VM estabilizada em modo RUNNING.")
        elif vm_status == "TERMINATED":
            state['status_history'].append("VM em repouso. Acionando ignicao...")
            subprocess.run(f"gcloud compute instances start {INSTANCE_NAME} --project {PROJECT_ID} --zone {ZONE} --quiet", shell=True, check=True)
        
        # Extração de IP Dinâmico
        state['vm_ip'] = data["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        state['status_history'].append(f"Infra pronta: {state['vm_ip']}")
        
    except Exception as e:
        state['error'] = f"Falha na Gestao de Infra: {str(e)}"
        state['status_history'].append(f"ERRO CRITICO: {str(e)}")
        
    return state

def node_health_check(state: AvatarState):
    state['status_history'].append("Aguardando motor neural (Warm-up)...")
    ready = False
    for i in range(60):
        try:
            r = requests.get(f"http://{state['vm_ip']}:8080/health", timeout=5)
            if r.status_code == 200:
                ready = True
                break
        except:
            pass
        time.sleep(5)
        print_dashboard(state, "Health Check", (i * 100 // 60))
        
    if not ready:
        state['error'] = "Timeout no Warm-up da GPU"
        return END
    
    state['status_history'].append("Motor Neural Online!")
    return state

def node_render_video(state: AvatarState):
    state['status_history'].append("Sintetizando Voz e Iniciando Render...")
    # Aqui chamariamos o run_production refatorado
    # Para agilizar e manter o isolamento, vamos invocar o motor via API
    endpoint = f"http://{state['vm_ip']}:8080/render"
    payload = {"text": state['texto'], "voice_id": VOICE_ID}
    
    response = requests.post(endpoint, json=payload)
    job_id = response.json().get("job_id")
    
    state['status_history'].append(f"Job disparado: {job_id}")
    
    # Monitoramento de conclusão
    while True:
        status_req = requests.get(f"http://{state['vm_ip']}:8080/status/{job_id}")
        data = status_req.json()
        if data['status'] == "COMPLETED":
            break
        elif data['status'] == "ERROR":
            state['error'] = "Erro na renderização neural"
            return state
        time.sleep(10)
        print_dashboard(state, "Renderizando", 50)
        
    state['status_history'].append("Renderização concluída na nuvem.")
    return state

def node_download_result(state: AvatarState):
    state['status_history'].append("Iniciando Download Blindado (SCP)...")
    local_path = os.path.abspath(f"outputs/AVATAR_GRAPH_{int(time.time())}.mp4")
    
    # Comando SCP sem prompt
    scp_cmd = f"gcloud compute scp {INSTANCE_NAME}:/workspace/latentsync/outputs/video_out.mp4 {local_path} --project {PROJECT_ID} --zone {ZONE} --tunnel-through-iap --quiet"
    subprocess.run(scp_cmd, shell=True, check=True)
    
    if os.path.exists(local_path):
        state['video_path'] = local_path
        state['status_history'].append("Vídeo resgatado com sucesso!")
    else:
        state['error'] = "Falha no download local"
        
    return state

# --- DEFINIÇÃO DO GRAFO ---
def build_avatar_graph():
    workflow = StateGraph(AvatarState)
    
    workflow.add_node("prepare_infra", node_prepare_infra)
    workflow.add_node("health_check", node_health_check)
    workflow.add_node("render_video", node_render_video)
    workflow.add_node("download_result", node_download_result)
    
    workflow.set_entry_point("prepare_infra")
    workflow.add_edge("prepare_infra", "health_check")
    workflow.add_edge("health_check", "render_video")
    workflow.add_edge("render_video", "download_result")
    workflow.add_edge("download_result", END)
    
    return workflow.compile()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Texto para a Cris falar")
    args = parser.parse_args()
    
    initial_state = {
        "texto": args.prompt,
        "status_history": ["Iniciando Grafo de Orquestração..."],
        "error": ""
    }
    
    app = build_avatar_graph()
    app.invoke(initial_state)
