import argparse
import time
import sys
import subprocess
import requests
from datetime import datetime
import os

# Força o caminho do cofre central local
os.environ["DB_PATH"] = r"C:\Users\vinic\brasil_ai.db"

# Adiciona a pasta src ao path para importar o secrets_manager
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from secrets_manager import get_secret

GITHUB_REPO = "viniciusbritor/Avatar"
WORKFLOW_NAME = "produce_avatar.yml"

def get_latest_run(token, start_time):
    """Busca a última execução do workflow iniciada após o start_time."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_NAME}/runs"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        runs = res.json().get("workflow_runs", [])
        
        # Filtra execuções criadas após o script começar
        # A API retorna em UTC: 2026-04-29T04:22:58Z
        valid_runs = []
        for r in runs:
            # Simplificação: assume que a primeira execução "in_progress" ou recém-criada é a nossa
            created_dt = datetime.strptime(r["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            if created_dt >= start_time:
                valid_runs.append(r)
                
        if valid_runs:
            # Retorna a mais recente
            return valid_runs[0]
    except Exception as e:
        print(f"Erro ao consultar runs: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Dispara a Action na nuvem e baixa o resultado localmente.")
    parser.add_argument("--text", type=str, required=True, help="Texto para o avatar falar.")
    parser.add_argument("--job-id", type=str, default="local-n8n", help="ID do Job.")
    args = parser.parse_args()

    # 1. Obter Token
    token = get_secret("GITHUB_TOKEN")
    if not token:
        print("❌ Erro: GITHUB_TOKEN não encontrado no secrets_manager.")
        sys.exit(1)

    start_time = datetime.utcnow()
    
    # 2. Disparar Action
    print(f"🚀 Disparando pipeline na nuvem para o texto: '{args.text[:50]}...'")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_NAME}/dispatches"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    data = {
        "ref": "master",
        "inputs": {
            "text": args.text,
            "job_id": args.job_id
        }
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 204:
        print(f"❌ Falha ao disparar Action: {res.status_code} - {res.text}")
        sys.exit(1)
        
    print("✅ Gatilho enviado com sucesso. Aguardando inicialização...")
    
    # 3. Descobrir o Run ID
    run_id = None
    status = None
    for _ in range(12): # Tenta por 1 minuto
        time.sleep(5)
        run_info = get_latest_run(token, start_time)
        if run_info:
            run_id = run_info["id"]
            status = run_info["status"]
            print(f"🔗 Run ID encontrado: {run_id} (Status: {status})")
            break
            
    if not run_id:
        print("⚠️ Não foi possível identificar o Run ID, mas o gatilho foi enviado. Prosseguindo para o modo de escuta cega...")
    
    # 4. Polling detalhado com barras de progresso
    if run_id:
        print("⏳ Iniciando monitoramento detalhado (atualização a cada 10s)...")
        while True:
            time.sleep(10)
            url_jobs = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/jobs"
            try:
                r_jobs = requests.get(url_jobs, headers=headers).json()
                jobs = r_jobs.get("jobs", [])
                
                # Limpa o terminal para redesenhar as barras
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"--- [BRASIL AI] Status do Pipeline (Run ID: {run_id}) ---")
                print(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')}\n")
                
                all_completed = True
                success = True
                
                if not jobs:
                    print("⏳ Aguardando alocação de runner...")
                    all_completed = False
                else:
                    for job in jobs:
                        for step in job.get("steps", []):
                            step_name = step.get("name", "Unknown")
                            status = step.get("status")
                            conclusion = step.get("conclusion")
                            
                            # Ignora steps de configuração muito técnicos do github
                            if step_name.startswith("Post ") or step_name == "Set up job":
                                continue
                                
                            if status == "completed":
                                if conclusion == "success":
                                    bar = "[██████████] 100%"
                                else:
                                    bar = "[░░░░░░░░░░] Erro!"
                                    success = False
                            elif status == "in_progress":
                                bar = "[████░░░░░░]  40%"
                                all_completed = False
                            else:
                                bar = "[░░░░░░░░░░]   0%"
                                all_completed = False
                                
                            print(f"{bar} - {step_name}")
                
                print("\n" + "-"*50)
                
                # Checa o status global do run
                url_run = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}"
                run_status = requests.get(url_run, headers=headers).json()
                
                if run_status.get("status") == "completed":
                    if run_status.get("conclusion") == "success":
                        print("✅ Action concluída com sucesso na nuvem!")
                    else:
                        print(f"❌ Action concluída com erro (conclusion: {run_status.get('conclusion')}).")
                        sys.exit(1)
                    break
                    
            except Exception as e:
                print(f"Erro ao fazer polling: {e}")
                
    # 5. Download GCS -> Local
    print("\n📦 Sincronizando resultados do bucket GCS para a pasta local 'outputs/'...")
    
    # Garante que a pasta local existe
    os.makedirs("outputs", exist_ok=True)
    
    # Roda gsutil rsync
    try:
        result = subprocess.run(
            ["gsutil", "-m", "rsync", "-r", "gs://brasil-ai-avatars-vault/outputs/", "outputs/"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Sincronização concluída com sucesso! Os arquivos estão na sua pasta 'outputs'.")
            print(result.stdout)
        else:
            print("❌ Erro na sincronização gsutil:")
            print(result.stderr)
    except FileNotFoundError:
        print("❌ Erro: Comando 'gsutil' não encontrado no PATH local. Certifique-se que o Google Cloud SDK está instalado.")

if __name__ == "__main__":
    main()
