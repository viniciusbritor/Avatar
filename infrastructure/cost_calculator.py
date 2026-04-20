import time

# Tabela de precos estimada (GCP Standard Rates)
# L4 (G2) ~ $0.69/hr
# T4 (N1) ~ $0.35/hr
GPU_PRICES = {
    "nvidia-l4": 0.69,
    "nvidia-tesla-t4": 0.35
}

def estimate_cost(gpu_type, duration_seconds):
    """Calcula o custo baseando-se no tipo de GPU e tempo de uptime."""
    hourly_rate = GPU_PRICES.get(gpu_type, 0.50) # Fallback para 0.50 se desconhecido
    duration_hours = duration_seconds / 3600
    
    # Arredondamos para cima se for menos de 1 min (GCP faturamento minimo)
    duration_hours = max(duration_hours, 1/60)
    
    return round(hourly_rate * duration_hours, 4)

def get_region_priority():
    """Retorna as regiões ordenadas por custo (historicamente mais baratas no topo)."""
    return [
        {"zone": "us-central1-a", "gpu": "nvidia-l4", "family": "g2-standard-12", "disk": "lana-engine-industrial"},
        {"zone": "us-east1-c", "gpu": "nvidia-l4", "family": "g2-standard-12", "disk": "lana-engine-industrial"},
        {"zone": "us-west1-b", "gpu": "nvidia-l4", "family": "g2-standard-12", "disk": "lana-engine-industrial"},
        {"zone": "us-east4-a", "gpu": "nvidia-l4", "family": "g2-standard-12", "disk": "lana-engine-industrial-a"},
        {"zone": "us-central1-a", "gpu": "nvidia-tesla-t4", "family": "n1-standard-8", "disk": "lana-engine-industrial"},
    ]
