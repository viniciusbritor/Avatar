@echo off
echo Acionando Motor Lana (GCP GCE)...
gcloud compute instances start lana-engine-industrial --project=brasili-ia-news --zone=us-east4-a
echo Aguardando inicializacao do IP e Docker (60s)...
timeout /t 60
echo Motor LANA pronto para uso no Canal Brasil AI.
pause
