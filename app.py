
# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

from auditor.architectures import get_architectures
from auditor.lifecycle_math import calculate_lifecycle_impact


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

    results_list.append({
        "Architecture": name,
        "Latency (ms)": architecture["latency_ms"],
        "Accuracy (%)": architecture["accuracy"],
        "Eligible": "Yes" if is_eligible else "No",
        "Hardware Carbon (kg)": impact["hardware_carbon_kg"],
        "Inference Energy (kWh)": impact["inference_energy_kwh"],
        "Storage (GB-hours)": impact["storage_impact_gb_hours"],
        "Networking Energy (kWh)": impact["networking_energy_kwh"],
        "Retraining Energy (kWh)": impact["retraining_energy_kwh"],
        "Total Energy (kWh)": impact["total_energy_kwh"],
        "Total Carbon (kg)": impact["total_carbon_kg"]
    })


results_df = pd.DataFrame(results_list)


# --------------------------------------------------
# ARCHITECTURE COMPARISON
# --------------------------------------------------

st.header("🏗️ Architecture Comparison")

display_columns = [
    "Architecture",
    "Latency (ms)",
    "Accuracy (%)",
    "Eligible",
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

eligible_df = results_df[
    results_df["Eligible"] == "Yes"
]

st.header("🌱 Architecture Recommendation")

if eligible_df.empty:

    st.warning(
        "No architecture satisfies both the latency and accuracy requirements."
    )

    st.info(
        "Try relaxing the SLA requirements or adding another architecture."
    )

else:

    recommended_row = eligible_df.loc[
        eligible_df["Total Carbon (kg)"].idxmin()
    ]

    recommended_name = recommended_row["Architecture"]

    st.success(
        f"Lowest-carbon eligible architecture: {recommended_name}"
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
# SIX-PILLAR IMPACT CHART
# --------------------------------------------------

st.header("🌍 Lifecycle Impact Breakdown")

pillar_columns = [
    "Hardware Carbon (kg)",
    "Inference Energy (kWh)",
    "Storage (GB-hours)",
    "Networking Energy (kWh)",
    "Retraining Energy (kWh)"
]

selected_pillars = results_df[
    ["Architecture"] + pillar_columns
]

pillars_long = selected_pillars.melt(
    id_vars="Architecture",
    var_name="Impact Category",
    value_name="Estimated Value"
)

pillar_chart = px.bar(
    pillars_long,
    x="Architecture",
    y="Estimated Value",
    color="Impact Category",
    barmode="group",
    title="Lifecycle Impact Categories"
)

st.plotly_chart(
    pillar_chart,
    use_container_width=True
)


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
