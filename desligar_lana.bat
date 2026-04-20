@echo off
echo Desligando Motor Lana para economizar custos...
gcloud compute instances stop lana-engine-industrial --project=brasili-ia-news --zone=us-east4-a
echo Motor LANA em repouso.
pause
