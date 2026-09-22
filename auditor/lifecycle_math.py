
# auditor/lifecycle_math.py

GRID_CARBON_INTENSITY = 0.45
NETWORK_ENERGY_PER_GB = 0.05


def calculate_hardware_carbon(
    embodied_carbon_kg,
    lifespan_hours,
    workload_hours
):
    """Estimate the allocated embodied hardware carbon."""

    if lifespan_hours <= 0:
        return 0

    return (
        embodied_carbon_kg / lifespan_hours
    ) * workload_hours


def calculate_inference_energy(
    tdp_watts,
    pue,
    latency_ms,
    requests
):
    """Estimate inference energy in kWh."""

    latency_seconds = latency_ms / 1000

    energy_kwh = (
        tdp_watts
        * pue
        * latency_seconds
        * requests
    ) / (1000 * 3600)

    return energy_kwh


def calculate_carbon(energy_kwh):
    """Convert energy consumption into kg CO2e."""

    return energy_kwh * GRID_CARBON_INTENSITY


def calculate_storage_impact(
    model_size_gb,
    storage_overhead,
    storage_hours
):
    """Estimate storage footprint in GB-hours."""

    return model_size_gb * storage_overhead * storage_hours


def calculate_networking_impact(
    network_gb,
    requests
):
    """Estimate networking energy in kWh."""

    total_data_gb = network_gb * requests

    return total_data_gb * NETWORK_ENERGY_PER_GB


def calculate_retraining_impact(
    retraining_hours,
    retraining_frequency,
    training_power_watts,
    pue
):
    """Estimate energy consumed during retraining."""

    training_energy_kwh = (
        retraining_hours
        * training_power_watts
        * pue
        / 1000
    )

    total_energy_kwh = (
        training_energy_kwh
        * retraining_frequency
    )

    return total_energy_kwh


def calculate_lifecycle_impact(
    architecture,
    requests,
    workload_hours,
    pue=1.4,
    storage_overhead=1.2,
    storage_hours=8760,
    training_power_watts=300
):
    """Calculate the six lifecycle impact pillars."""

    hardware_carbon = calculate_hardware_carbon(
        architecture["embodied_carbon_kg"],
        architecture["lifespan_hours"],
        workload_hours
    )

    inference_energy = calculate_inference_energy(
        architecture["tdp_watts"],
        pue,
        architecture["latency_ms"],
        requests
    )

    inference_carbon = calculate_carbon(inference_energy)

    storage_impact = calculate_storage_impact(
        architecture["model_size_gb"],
        storage_overhead,
        storage_hours
    )

    networking_energy = calculate_networking_impact(
        architecture["network_gb_per_request"],
        requests
    )

    retraining_energy = calculate_retraining_impact(
        architecture["retraining_hours"],
        architecture["retraining_frequency"],
        training_power_watts,
        pue
    )

    total_energy = (
        inference_energy
        + networking_energy
        + retraining_energy
    )

    total_carbon = (
        inference_carbon
        + hardware_carbon
        + calculate_carbon(networking_energy)
        + calculate_carbon(retraining_energy)
    )

    return {
        "hardware_carbon_kg": hardware_carbon,
        "inference_energy_kwh": inference_energy,
        "inference_carbon_kg": inference_carbon,
        "storage_impact_gb_hours": storage_impact,
        "networking_energy_kwh": networking_energy,
        "retraining_energy_kwh": retraining_energy,
        "total_energy_kwh": total_energy,
        "total_carbon_kg": total_carbon
    }
