
from auditor.architectures import get_architectures
from auditor.lifecycle_math import calculate_lifecycle_impact


architectures = get_architectures()

selected_architecture = architectures["Quantized Core"]

results = calculate_lifecycle_impact(
    architecture=selected_architecture,
    requests=100000,
    workload_hours=100
)

print("Architecture:", "Quantized Core")
print("Latency:", selected_architecture["latency_ms"], "ms")
print("Accuracy:", selected_architecture["accuracy"], "%")
print("Lifecycle results:")

for key, value in results.items():
    print(f"{key}: {value:.4f}")
