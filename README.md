# SustainaByte 🍃

> **Gemini-Powered Sustainable AI Lifecycle Auditor**
> Auditing the full environmental footprint of AI models across energy, carbon, storage, networking, hardware, and retraining to recommend Pareto-optimal architectures under strict enterprise latency and accuracy constraints.
> 
> 

---

## 📌 Problem Statement: Sustainable AI Lifecycle Auditor

Modern machine learning development disproportionately optimizes for accuracy while ignoring the compounding carbon footprint across the ML lifecycle. Problem Statement S3 challenges teams to:

> "Develop an AI-based auditor that estimates the energy, carbon, storage, networking, hardware, and retraining impact of an AI system throughout its lifecycle and recommends the most sustainable architecture under accuracy and latency constraints."
> 
> 

**SustainaBYte** addresses this by pairing deterministic mathematical models for all six lifecycle pillars with an autonomous **Gemini Agentic Workflow**. Rather than offering vague suggestions, SustainaBYte functions as a closed-loop decision engine that programmatically evaluates architecture trade-offs (e.g., dense FP16 models vs. quantized INT4 models with LoRA tuning) to enforce strict enterprise Service Level Agreements (SLAs).

---

## 🧠 System Architecture & Agentic Flow

```text
[ Enterprise SLA Inputs ] 
  - Minimum Accuracy (%)
  - Maximum Latency (ms)
  - Monthly Query Volume
            │
            ▼
[ Deterministic Lifecycle Engine ]
  Calculates all 6 Pillars:
  ├── Embodied Hardware Carbon (Amortized GPU footprint)
  ├── Operational Energy & Carbon (Watts × PUE × Grid Factor)
  ├── Storage Footprint (Weights, checkpoints, vector DBs)
  ├── Networking Overhead (Ingress/egress data transmission)
  └── Retraining Impact (Continuous fine-tuning schedule)
            │
            ▼
[ Gemini 2.5 Agent (Auditor Brain) ]
  ├── Evaluates candidate models against hard SLA bounds
  ├── Disqualifies failing architectures (Too slow / Inaccurate)
  ├── Ranks valid candidates by total lifecycle CO₂e
  └── Generates AI Eco-Nutrition Label & migration trade-off analysis
            │
            ▼
[ Streamlit Interactive Decision Dashboard ]
  ├── Comparative 6-Pillar Footprint Breakdown
  ├── Latency vs. Accuracy vs. Carbon Pareto Curve
  └── Executive Sustainability Audit Report

```

---

## 📊 The 6-Pillar Lifecycle Model

SustainaBYte deterministically models every metric specified in the S3 prompt:

1. **Hardware (Embodied Carbon):** Models the embedded manufacturing footprint of datacenter accelerators (e.g., NVIDIA A100 vs. T4) amortized over duty cycle:

$$\text{Embodied CO}_2 = \left( \frac{\text{Embodied Carbon (kg)}}{\text{Lifespan Hours}} \right) \times \text{Workload Hours}$$


2. **Energy (Operational kWh):** Computes active compute draw based on Thermal Design Power (TDP), Datacenter Power Usage Effectiveness (PUE = 1.2), and inference duration:

$$\text{Energy}_{\text{infer}} = \frac{\text{TDP (W)} \times \text{PUE} \times \text{Latency (s)} \times \text{Requests}}{1000 \times 3600}$$


3. **Carbon ($kg\text{ CO}_2e$):** Translates operational energy consumption into emissions using local regional grid carbon intensity ($0.45\text{ kg CO}_2/\text{kWh}$).
4. **Storage Overhead:** Quantifies ongoing disk power consumption for model checkpoints, weight distribution, and vector database indices.
5. **Networking Impact:** Estimates data transmission energy for inference API payload transfers ($0.05\text{ kWh/GB}$).
6. **Retraining Frequency:** Compounding annual footprint scaling based on training intervals (e.g., daily full fine-tuning vs. monthly parameter-efficient LoRA updates).

---

## 🛠️ Tech Stack

* **AI Agent & Reasoning:** Google GenAI SDK (`gemini-2.5-flash` with structured prompting & tool evaluation)


* **Frontend UI & Visualization:** Streamlit, Plotly (Interactive Pareto frontiers & stacked pillar bar charts)
* **Data & Logic:** Python 3.10+, Pandas, NumPy
* **Environment:** Compatible with Antigravity IDE and VS Code



---

## 📁 Repository Structure

```text
sustainabyte/
├── app.py                     # Streamlit frontend dashboard & visual charts
├── auditor/
│   ├── __init__.py
│   ├── lifecycle_math.py      # Deterministic 6-pillar footprint formulas
│   ├── architectures.py       # Catalog of candidate AI models & specs
│   └── gemini_auditor.py      # Gemini Agent logic & SLA evaluation
├── requirements.txt           # Project dependencies
├── .env.example               # Template for API keys
└── README.md

```

---

## 🚀 Quickstart Guide

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/sustainabyte.git
cd sustainabyte

```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure API Key

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY="your_google_gemini_api_key_here"

```

### 5. Launch the Dashboard

```bash
streamlit run app.py

```

---

## 💡 Example Evaluation Scenario

| Architecture Candidate | Model Profile | Latency (ms) | Accuracy (%) | Lifetime Carbon ($kg\text{ CO}_2e$) | Auditor Status |
| --- | --- | --- | --- | --- | --- |
| **Cloud Monolith** | LLaMA-3-70B Dense (FP16) | 185 ms | 94.2% | 4,820 kg | ❌ Disqualified (Exceeds 80ms Latency SLA) |
| **Edge Micro** | TinyML ONNX (0.5B) | 12 ms | 78.5% | 120 kg | ❌ Disqualified (Fails 88% Accuracy SLA) |
| **Quantized Core** | LLaMA-3-8B (INT4 + LoRA) | 42 ms | 91.1% | 680 kg | ✅ **Recommended Architecture** |

Outcome: SustainaBYte selects the Quantized Core architecture, reducing lifecycle carbon emissions by **85.9%** while honoring all latency and accuracy SLAs.
