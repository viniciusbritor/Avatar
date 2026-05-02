import requests, time, os, sys
from datetime import datetime

token = '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'
run_id = sys.argv[1] if len(sys.argv) > 1 else '25179373439'
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

def get_progress_bar(status, conclusion):
    if status == "completed":
        return "[##########] 100%" if conclusion == "success" else "[  FAILED  ]"
    elif status == "in_progress":
        return "[ RUNNING  ]"
    else:
        return "[  QUEUED  ]"

def monitor():
    url_jobs = f"https://api.github.com/repos/viniciusbritor/Avatar/actions/runs/{run_id}/jobs"
    try:
        res = requests.get(url_jobs, headers=headers).json()
        jobs = res.get("jobs", [])
        if not jobs:
            print("⏳ Aguardando alocação de runner...")
            return False

        print(f"--- [BRASIL AI] Monitoramento de Pipeline (Run: {run_id}) ---")
        print(f"Status em: {datetime.now().strftime('%H:%M:%S')}\n")
        
        all_done = True
        for job in jobs:
            for step in job.get("steps", []):
                name = step.get("name")
                if name.startswith("Post ") or name in ["Set up job", "Complete job"]: continue
                
                bar = get_progress_bar(step.get("status"), step.get("conclusion"))
                print(f"{bar} - {name}")
                if step.get("status") != "completed": all_done = False
        
        print("\n" + "-"*50)
        return all_done
    except Exception as e:
        print(f"Erro: {e}")
        return False

# Executa uma vez e sai (o agente chamará repetidamente)
monitor()
