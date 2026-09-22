
# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

from auditor.architectures import get_architectures
from auditor.lifecycle_math import calculate_lifecycle_impact
from auditor.gemini_auditor import run_lifecycle_audit


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SustainaByte",
    page_icon="🍃",
    layout="wide"
)


# --------------------------------------------------
# TITLE AND INTRODUCTION
# --------------------------------------------------

st.title("🍃 SustainaByte")
st.subheader("Sustainable AI Lifecycle Auditor")

st.write(
    """
    Estimate the environmental impact of AI architectures
    and compare them against accuracy and latency requirements.
    """
)

st.divider()


# --------------------------------------------------
# SIDEBAR: USER INPUTS
# --------------------------------------------------

st.sidebar.header("Enterprise Requirements")

requests = st.sidebar.number_input(
    "Number of AI requests",
    min_value=1,
    value=100000,
    step=10000
)

workload_hours = st.sidebar.number_input(
    "Workload duration (hours)",
    min_value=1.0,
    value=100.0,
    step=10.0
)

maximum_latency = st.sidebar.number_input(
    "Maximum latency (ms)",
    min_value=1.0,
    value=80.0,
    step=5.0
)

minimum_accuracy = st.sidebar.number_input(
    "Minimum accuracy (%)",
    min_value=0.0,
    max_value=100.0,
    value=88.0,
    step=1.0
)

pue = st.sidebar.number_input(
    "Power Usage Effectiveness (PUE)",
    min_value=1.0,
    value=1.4,
    step=0.1
)

workload_desc = st.sidebar.text_input(
    "Workload description",
    value="Customer Support Bot"
)


# --------------------------------------------------
# LOAD ARCHITECTURES
# --------------------------------------------------

architectures = get_architectures()


# --------------------------------------------------
# SLA REQUIREMENT DISPLAY
# --------------------------------------------------

st.header("📋 Enterprise SLA Requirements")

sla_col1, sla_col2, sla_col3 = st.columns(3)

with sla_col1:
    st.metric(
        "Maximum Latency",
        f"{maximum_latency:.0f} ms"
    )

with sla_col2:
    st.metric(
        "Minimum Accuracy",
        f"{minimum_accuracy:.1f}%"
    )

with sla_col3:
    st.metric(
        "Total Requests",
        f"{requests:,}"
    )


st.divider()


# --------------------------------------------------
# CALCULATE IMPACTS
# --------------------------------------------------

results_list = []

for name, architecture in architectures.items():

    impact = calculate_lifecycle_impact(
        architecture=architecture,
        requests=requests,
        workload_hours=workload_hours,
        pue=pue
    )

    is_eligible = (
        architecture["latency_ms"] <= maximum_latency
        and architecture["accuracy"] >= minimum_accuracy
    )

    # Build enriched model dict with all keys needed by gemini_auditor + UI
    enriched = {
        "name": name,
        "accuracy": architecture["accuracy"],
        "latency_ms": architecture["latency_ms"],
        "description": architecture.get("description", ""),
        "hardware_carbon_kg": impact["hardware_carbon_kg"],
        "inference_energy_kwh": impact["inference_energy_kwh"],
        "inference_carbon_kg": impact["inference_carbon_kg"],
        "storage_impact_gb_hours": impact["storage_impact_gb_hours"],
        "networking_energy_kwh": impact["networking_energy_kwh"],
        "retraining_energy_kwh": impact["retraining_energy_kwh"],
        "total_energy_kwh": impact["total_energy_kwh"],
        "total_carbon_kg": impact["total_carbon_kg"],
        "eligible": is_eligible,
    }

    results_list.append(enriched)


# --------------------------------------------------
# FIND WINNER (lowest carbon among eligible)
# --------------------------------------------------

eligible_models = [m for m in results_list if m["eligible"]]
winner_name = None

if eligible_models:
    winner = min(eligible_models, key=lambda m: m["total_carbon_kg"])
    winner_name = winner["name"]


# --------------------------------------------------
# BUILD DISPLAY DATAFRAME
# --------------------------------------------------

display_rows = []
for m in results_list:
    if m["name"] == winner_name:
        status = "✅ Winner"
    elif m["eligible"]:
        status = "✔️ Eligible"
    else:
        status = "❌ Disqualified"

    display_rows.append({
        "Status": status,
        "Architecture": m["name"],
        "Latency (ms)": m["latency_ms"],
        "Accuracy (%)": m["accuracy"],
        "Hardware Carbon (kg)": m["hardware_carbon_kg"],
        "Inference Energy (kWh)": m["inference_energy_kwh"],
        "Storage (GB-hours)": m["storage_impact_gb_hours"],
        "Networking Energy (kWh)": m["networking_energy_kwh"],
        "Retraining Energy (kWh)": m["retraining_energy_kwh"],
        "Total Energy (kWh)": m["total_energy_kwh"],
        "Total Carbon (kg)": m["total_carbon_kg"],
    })

results_df = pd.DataFrame(display_rows)


# --------------------------------------------------
# ARCHITECTURE COMPARISON
# --------------------------------------------------

st.header("🏗️ Architecture Comparison")

display_columns = [
    "Status",
    "Architecture",
    "Latency (ms)",
    "Accuracy (%)",
    "Total Energy (kWh)",
    "Total Carbon (kg)"
]

st.dataframe(
    results_df[display_columns].round(3),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# RECOMMENDATION
# --------------------------------------------------

st.header("🌱 Architecture Recommendation")

if not eligible_models:

    st.warning(
        "No architecture satisfies both the latency and accuracy requirements."
    )

    st.info(
        "Try relaxing the SLA requirements or adding another architecture."
    )

else:

    recommended_row = results_df.loc[
        results_df["Status"] == "✅ Winner"
    ].iloc[0]

    recommended_name = recommended_row["Architecture"]

    st.success(
        f"Lowest-carbon eligible architecture: **{recommended_name}**"
    )

    recommendation_col1, recommendation_col2, recommendation_col3 = (
        st.columns(3)
    )

    with recommendation_col1:
        st.metric(
            "Recommended Architecture",
            recommended_name
        )

    with recommendation_col2:
        st.metric(
            "Total Carbon",
            f"{recommended_row['Total Carbon (kg)']:.2f} kg"
        )

    with recommendation_col3:
        st.metric(
            "Total Energy",
            f"{recommended_row['Total Energy (kWh)']:.2f} kWh"
        )


# --------------------------------------------------
# ECO-NUTRITION LABEL (Gemini)
# --------------------------------------------------

st.header("🍃 AI Eco-Nutrition Label")

if st.button("Generate Eco-Nutrition Label", type="primary"):
    with st.spinner("Auditing lifecycle impact with Gemini..."):
        label_md = run_lifecycle_audit(
            workload_desc=workload_desc,
            target_acc=minimum_accuracy,
            max_lat=maximum_latency,
            audited_models=results_list,
        )
    with st.expander("Eco-Nutrition Label", expanded=True):
        st.markdown(label_md)


# --------------------------------------------------
# CARBON COMPARISON CHART
# --------------------------------------------------

st.header("📊 Total Carbon Comparison")

carbon_chart = px.bar(
    results_df,
    x="Architecture",
    y="Total Carbon (kg)",
    color="Architecture",
    title="Estimated Lifecycle Carbon by Architecture"
)

st.plotly_chart(
    carbon_chart,
    use_container_width=True
)


# --------------------------------------------------
# LIFECYCLE IMPACT BREAKDOWN
# --------------------------------------------------

st.header("🌍 Lifecycle Impact Breakdown")

# ── Normalize each pillar to 0–100% across architectures ─────────────
pillar_columns = [
    "Hardware Carbon (kg)",
    "Inference Energy (kWh)",
    "Storage (GB-hours)",
    "Networking Energy (kWh)",
    "Retraining Energy (kWh)"
]

pillar_data = results_df[["Architecture"] + pillar_columns].copy()

# Melt to long form first (raw values)
pillar_long = pillar_data.melt(
    id_vars="Architecture",
    var_name="Impact Category",
    value_name="Raw Value"
)

# Normalize: for each pillar, divide by its max across all architectures
pillar_long["Normalized (%)"] = pillar_long.groupby("Impact Category")["Raw Value"].transform(
    lambda col: (col / col.max() * 100) if col.max() > 0 else 0
)

# Format raw value for tooltip
pillar_long["Raw Label"] = pillar_long["Raw Value"].apply(lambda v: f"{v:,.4f}")

pillar_chart = px.bar(
    pillar_long,
    x="Architecture",
    y="Normalized (%)",
    color="Impact Category",
    barmode="group",
    title="Lifecycle Impact Breakdown (normalized to 0–100% per pillar)",
    hover_data={"Raw Value": ":.4f", "Normalized (%)": ":.1f"},
)

pillar_chart.update_yaxes(title_text="Relative Impact (%)", range=[0, 105])

st.plotly_chart(pillar_chart, use_container_width=True)


# --------------------------------------------------
# RAW DATA
# --------------------------------------------------

with st.expander("View detailed calculation results"):

    st.dataframe(
        results_df.round(4),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# ASSUMPTIONS
# --------------------------------------------------

st.divider()

st.caption(
    """
    Note: Results are estimates based on simplified assumptions and
    illustrative architecture presets. They are not direct measurements
    of actual hardware or production infrastructure.
    """
)
