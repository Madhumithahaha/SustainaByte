"""Streamlit dashboard backed by SustainaByte's deterministic Math & Data API."""

import pandas as pd
import plotly.express as px
import streamlit as st

from auditor.lifecycle_math import Workload, compare_architectures
from auditor.connectivity import is_internet_available
from auditor.offline_store import (
    get_pending_count,
    get_recent_audits,
    initialize_database,
    save_audit,
    sync_pending_audits,
)


st.set_page_config(page_title="SustainaByte", page_icon="🍃", layout="wide")
st.title("🍃 SustainaByte")
st.subheader("Sustainable AI Lifecycle Auditor")
st.write("Estimate the environmental impact of AI architectures and compare them against accuracy and latency requirements.")
st.divider()

st.sidebar.header("Enterprise Requirements")
requests = st.sidebar.number_input("Number of AI requests", min_value=1, value=100000, step=10000)
workload_hours = st.sidebar.number_input("Workload duration (training hours)", min_value=1.0, value=100.0, step=10.0)
maximum_latency = st.sidebar.number_input("Maximum latency (ms)", min_value=1.0, value=80.0, step=5.0)
minimum_accuracy = st.sidebar.number_input("Minimum accuracy (%)", min_value=0.0, max_value=100.0, value=88.0, step=1.0)
workload_desc = st.sidebar.text_input("Workload description", value="Customer Support Bot")
simulate_offline = st.sidebar.toggle("Demo: Simulate Offline Mode", value=False)
st.sidebar.caption("Energy and carbon assumptions use the deterministic defaults defined by the Math & Data layer.")

try:
    initialize_database()
    connection_available = is_internet_available()
    sync_result = sync_pending_audits(online=connection_available) if connection_available and not simulate_offline else None
    pending_count = get_pending_count()
except Exception as error:  # Database failure must be visible, never silent.
    st.error(f"Offline audit storage is unavailable: {error}")
    connection_available = False
    sync_result = None
    pending_count = None

# The UI controls provide the workload-specific inputs; all formulas remain in
# lifecycle_math.py.  The remaining Workload fields intentionally use its
# documented deterministic defaults.
workload = Workload(training_hours=float(workload_hours), inference_count=int(requests))
comparisons = compare_architectures(
    workload,
    minimum_accuracy=float(minimum_accuracy) / 100.0,
    maximum_latency_ms=float(maximum_latency),
)

st.header("📋 Enterprise SLA Requirements")
sla_col1, sla_col2, sla_col3 = st.columns(3)
sla_col1.metric("Maximum Latency", f"{maximum_latency:.0f} ms")
sla_col2.metric("Minimum Accuracy", f"{minimum_accuracy:.1f}%")
sla_col3.metric("Total Requests", f"{requests:,}")
st.divider()

# Data contract: compare_architectures -> impact's six named pillars.  Values
# below only select and label returned fields; no lifecycle formula is repeated.
results_list = []
for comparison in comparisons:
    architecture = comparison["architecture"]
    impact = comparison["impact"]
    energy = impact["energy"]
    carbon = impact["carbon"]
    storage = impact["storage"]
    networking = impact["networking"]
    hardware = impact["hardware"]
    retraining = impact["retraining"]
    results_list.append({
        "name": architecture.name,
        "model_type": architecture.model_type,
        "parameter_count": architecture.parameter_count,
        "model_size_mb": architecture.model_size_mb,
        "accuracy": architecture.estimated_accuracy * 100.0,
        "latency_ms": architecture.estimated_latency_ms,
        "energy_kwh": energy["total_energy_kwh"],
        "carbon_kg": carbon["total_carbon_kg"],
        "storage_gb": storage["total_storage_gb"],
        "networking_gb": networking["total_network_gb"],
        "networking_energy_kwh": networking["network_energy_kwh"],
        "hardware_carbon_kg": hardware["embodied_carbon_kg"],
        "retraining_energy_kwh": retraining["retraining_energy_kwh"],
        "total_lifecycle_carbon_kg": impact["total_lifecycle_carbon_kg"],
        # Gemini expects this existing key; it is the Math API's total carbon.
        "total_carbon_kg": impact["total_lifecycle_carbon_kg"],
        "eligible": comparison["feasible"],
    })

eligible_models = [model for model in results_list if model["eligible"]]
winner_name = min(eligible_models, key=lambda model: model["total_lifecycle_carbon_kg"])["name"] if eligible_models else None

display_rows = []
for model in results_list:
    status = "✅ Winner" if model["name"] == winner_name else "✔️ Eligible" if model["eligible"] else "❌ Disqualified"
    display_rows.append({
        "Status": status,
        "Architecture": model["name"],
        "Model Type": model["model_type"],
        "Parameters": model["parameter_count"],
        "Model Size (MB)": model["model_size_mb"],
        "Latency (ms)": model["latency_ms"],
        "Accuracy (%)": model["accuracy"],
        "Energy (kWh)": model["energy_kwh"],
        "Carbon (kg CO2e)": model["carbon_kg"],
        "Storage (GB)": model["storage_gb"],
        "Networking (GB)": model["networking_gb"],
        "Hardware (kg CO2e)": model["hardware_carbon_kg"],
        "Retraining (kWh)": model["retraining_energy_kwh"],
        "Total Lifecycle Impact (kg CO2e)": model["total_lifecycle_carbon_kg"],
    })
results_df = pd.DataFrame(display_rows)

st.header("📡 Offline-First Audit Status")
if pending_count is None:
    st.error("Local persistence is unavailable; audit results are still displayed but cannot be queued.")
elif simulate_offline:
    st.warning(f"🟠 OFFLINE DEMO MODE — Local sustainability auditing is active. Pending architecture audit records: {pending_count}.")
elif connection_available:
    if sync_result and sync_result["synced"]:
        st.success(f"🟢 CONNECTION RESTORED — {sync_result['synced']} pending record(s) reconciled to the {sync_result['target'].replace('_', ' ')}.")
    else:
        st.success(f"🟢 ONLINE — Local sustainability auditing is active. Synchronization target: {(sync_result or {'target': 'local_demo_sink'})['target'].replace('_', ' ')}. Pending records: {pending_count}.")
else:
    st.warning(f"🟠 OFFLINE MODE — Local sustainability auditing is still fully operational. Pending architecture audit records: {pending_count}.")

if st.button("Save Current Audit Locally and Sync", type="secondary"):
    try:
        for model in results_list:
            save_audit({
                "monthly_queries": int(requests),
                "architecture_name": model["name"],
                "model_type": model["model_type"],
                "accuracy": model["accuracy"],
                "latency_ms": model["latency_ms"],
                "energy": model["energy_kwh"],
                "carbon": model["carbon_kg"],
                "storage": model["storage_gb"],
                "networking": model["networking_gb"],
                "hardware": model["hardware_carbon_kg"],
                "retraining": model["retraining_energy_kwh"],
            })
        if connection_available and not simulate_offline:
            saved_sync = sync_pending_audits(online=True)
            st.success(f"Audit saved locally first; {saved_sync['synced']} record(s) reconciled to the {saved_sync['target'].replace('_', ' ')}.")
        else:
            st.success("Audit saved locally. It remains queued safely until connectivity is restored or demo offline mode is disabled.")
        pending_count = get_pending_count()
    except Exception as error:
        st.error(f"Audit results were calculated but could not be saved locally: {error}")

if pending_count:
    pending_rows = get_recent_audits(8)
    pending_rows = [row for row in pending_rows if row["sync_status"] == "pending"]
    if pending_rows:
        st.caption(f"Pending audits: {pending_count}")
        st.dataframe(pd.DataFrame(pending_rows)[["audit_id", "timestamp", "architecture_name", "carbon", "sync_status"]], use_container_width=True, hide_index=True)

st.header("🏗️ Architecture Comparison")
st.dataframe(results_df.round(3), use_container_width=True, hide_index=True)

st.header("🌱 Architecture Recommendation")
if not eligible_models:
    st.warning("No architecture satisfies both the latency and accuracy requirements.")
    st.info("Try relaxing the SLA requirements or adding another architecture.")
else:
    recommended_row = results_df.loc[results_df["Status"] == "✅ Winner"].iloc[0]
    st.success(f"Lowest-carbon eligible architecture: **{recommended_row['Architecture']}**")
    recommendation_col1, recommendation_col2, recommendation_col3 = st.columns(3)
    recommendation_col1.metric("Recommended Architecture", recommended_row["Architecture"])
    recommendation_col2.metric("Total Lifecycle Impact", f"{recommended_row['Total Lifecycle Impact (kg CO2e)']:.2f} kg CO2e")
    recommendation_col3.metric("Total Energy", f"{recommended_row['Energy (kWh)']:.2f} kWh")

st.header("🍃 AI Eco-Nutrition Label")
if st.button("Generate Eco-Nutrition Label", type="primary"):
    with st.spinner("Auditing lifecycle impact with Gemini..."):
        # Gemini is optional for the Math & Data dashboard.  Importing it on
        # demand lets the lifecycle UI run when no Gemini key is configured.
        from auditor.gemini_auditor import run_lifecycle_audit
        label_md = run_lifecycle_audit(workload_desc, minimum_accuracy, maximum_latency, results_list)
    with st.expander("Eco-Nutrition Label", expanded=True):
        st.markdown(label_md)

st.header("📊 Total Carbon Comparison")
carbon_chart = px.bar(results_df, x="Architecture", y="Total Lifecycle Impact (kg CO2e)", color="Architecture", title="Estimated Lifecycle Carbon by Architecture")
st.plotly_chart(carbon_chart, use_container_width=True)

st.header("🌍 Lifecycle Impact Breakdown")
pillar_columns = ["Energy (kWh)", "Carbon (kg CO2e)", "Storage (GB)", "Networking (GB)", "Hardware (kg CO2e)", "Retraining (kWh)"]
pillar_long = results_df[["Architecture"] + pillar_columns].melt(id_vars="Architecture", var_name="Impact Category", value_name="Raw Value")
pillar_long["Normalized (%)"] = pillar_long.groupby("Impact Category")["Raw Value"].transform(lambda values: values / values.max() * 100 if values.max() > 0 else 0)
pillar_chart = px.bar(pillar_long, x="Architecture", y="Normalized (%)", color="Impact Category", barmode="group", title="Lifecycle Impact Breakdown (normalized to 0–100% per pillar)", hover_data={"Raw Value": ":.4f", "Normalized (%)": ":.1f"})
pillar_chart.update_yaxes(title_text="Relative Impact (%)", range=[0, 105])
st.plotly_chart(pillar_chart, use_container_width=True)

with st.expander("View detailed calculation results"):
    st.dataframe(results_df.round(4), use_container_width=True, hide_index=True)

st.divider()
st.caption("Results use illustrative architecture presets and deterministic lifecycle assumptions; they are estimates rather than direct production measurements.")
