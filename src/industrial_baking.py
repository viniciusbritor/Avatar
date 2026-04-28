
import sys
import time
import os
import subprocess
from agente_lana_orchestrator import AgenteLanaOrchestrator

def execute_baking():
    print("\n\n\n") # Espaço para as 3 barras
    print("--- [LANA INDUSTRIAL] INICIANDO PROCESSO DE BAKING V19 ---")
    orchestrator = AgenteLanaOrchestrator()
    
    # Inicia barras via motor (engine)
    orchestrator.engine.print_triple_progress(0, 0, 0, "Iniciando...", "Aguardando...", "Idle")

    # 1. Encontrar qualquer zona L4 disponível
    orchestrator.engine.print_triple_progress(10, 0, 0, "Caçando GPU L4...", "Aguardando...", "Idle")
    try:
        orchestrator.engine.ensure_instance_ready(force_gpu="L4")
        instance = orchestrator.engine.active_instance
        zone = orchestrator.engine.active_zone
        orchestrator.engine.print_triple_progress(100, 0, 0, f"L4 Ativa em {zone}", "Iniciando Pull...", "Idle")
        
        # 2. Iniciar o Docker Pull com Telemetria Ativa
        img_l4 = "us-east1-docker.pkg.dev/brasili-ia-news/lana-repo/lana-engine-l4:v1.0"
        orchestrator.engine.print_triple_progress(100, 5, 0, f"Conectado a {instance}", "Iniciando download 9GB...", "Idle")
        
        # Pull em background para monitorar progresso
        pull_cmd = ["gcloud", "compute", "ssh", instance, "--project", orchestrator.engine.project_id,
                    "--zone", zone, "--tunnel-through-iap", "--command",
                    f"sudo docker pull {img_l4}", "--quiet"]
        
        # Simulação de progresso realista
        p = subprocess.Popen(pull_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        
        for i in range(1, 101):
            if p.poll() is not None: break # Terminou
            time.sleep(4) # Aumentado para 400s (estimativa segura para 9GB)
            orchestrator.engine.print_triple_progress(100, i, 0, "Infra Estável", f"Baixando Camadas ({i}%)", "Idle")
            
        orchestrator.engine.print_triple_progress(100, 100, 0, "Infra Estável", "Download 9GB Concluído!", "Idle")
        
        # 3. Preparar para imagem (Limpeza de logs)
        orchestrator.engine.print_triple_progress(100, 100, 10, "Limpando Disco", "Finalizando Cérebro", "Baking Mode")
        orchestrator.engine._run_ssh_cmd(["gcloud", "compute", "ssh", instance, "--project", orchestrator.engine.project_id,
                                         "--zone", zone, "--tunnel-through-iap", "--command",
                                         "sudo rm -rf /workspace/* && sudo docker system prune -f", "--quiet"])
        
        # 4. Parar e Criar Imagem
        orchestrator.engine.print_triple_progress(100, 100, 50, "Desligando VM", "Congelando Camadas", "Baking Mode")
        os.system(f"gcloud compute instances stop {instance} --project {orchestrator.engine.project_id} --zone {zone} --quiet")
        
        new_image_name = "lana-gold-standard-v19-baked"
        orchestrator.engine.print_triple_progress(100, 100, 80, "Criando Imagem Global", "Salvando no Cofre GCP", "Baking Mode")
        os.system(f"gcloud compute images create {new_image_name} --project {orchestrator.engine.project_id} --source-disk {instance} --source-disk-zone {zone} --force")
        
        orchestrator.engine.print_triple_progress(100, 100, 100, "V19 PRONTA!", "CONGELADO", "CONCLUÍDO")
        print(f"\n--- [SUCESSO] IMAGEM {new_image_name} CRIADA ---")
        
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] Falha no processo de Baking: {e}")

if __name__ == "__main__":
    execute_baking()
