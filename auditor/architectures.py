
# auditor/architectures.py

ARCHITECTURES = {
    "Cloud Monolith": {
        "latency_ms": 185,
        "accuracy": 94.2,
        "tdp_watts": 300,
        "embodied_carbon_kg": 1500,
        "lifespan_hours": 43800,
        "model_size_gb": 15,
        "network_gb_per_request": 0.002,
        "retraining_hours": 100,
        "retraining_frequency": 12,
        "description": "A centralized cloud-based AI model."
    },

    "Edge Micro": {
        "latency_ms": 12,
        "accuracy": 78.5,
        "tdp_watts": 15,
        "embodied_carbon_kg": 150,
        "lifespan_hours": 43800,
        "model_size_gb": 2,
        "network_gb_per_request": 0.0005,
        "retraining_hours": 30,
        "retraining_frequency": 24,
        "description": "A lightweight AI model deployed on edge hardware."
    },

    "Quantized Core": {
        "latency_ms": 42,
        "accuracy": 91.1,
        "tdp_watts": 75,
        "embodied_carbon_kg": 500,
        "lifespan_hours": 43800,
        "model_size_gb": 6,
        "network_gb_per_request": 0.001,
        "retraining_hours": 60,
        "retraining_frequency": 12,
        "description": "A quantized model balancing accuracy and efficiency."
    }
}


def get_architectures():
    """Return all available architecture presets."""
    return ARCHITECTURES
