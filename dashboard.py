import streamlit as st
import pandas as pd
import json
import plotly.express as px
import ollama

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Visualization & Explainability Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# ====================== HEADER ======================
st.title("🛡️ Visualization & Explainability Dashboard")

st.markdown("""
## Motivation
- Security tools generate large, complex outputs that are hard to interpret  
- Visualization helps understand attacks, model responses, and vulnerabilities  

## Expected Impact
- Enables intuitive vulnerability assessment  
- Supports education and research on attack effectiveness in real time  

## Implementation
- Lightweight Streamlit dashboard  
- Visualize: attack coverage, prompt types, success/failure, risk metrics  
- Compatible with PromptMap / security JSON outputs  

## Evaluation Method
- User study with 3–5 security researchers/developers  
- Compare comprehension before vs after dashboard usage  
- Metrics: ability to identify top 5 most effective attacks  
""")

# ====================== FILE UPLOAD ======================
uploaded_file = st.file_uploader("Upload results.json", type=["json"])

if not uploaded_file:
    st.info("Upload a PromptMap / security evaluation JSON file to begin.")
    st.stop()

data = json.load(uploaded_file)

# ====================== DATA PARSING ======================
records = []

for rule, result in data.items():
    pass_rate = result.get("pass_rate", "0/0")

    try:
        if "/" in str(pass_rate):
            s, t = map(int, pass_rate.split("/"))
            success_rate = s / t if t > 0 else 0
        else:
            success_rate = 1.0 if result.get("passed") else 0.0
    except:
        success_rate = 0.0

    records.append({
        "rule": rule,
        "type": result.get("type", "unknown"),
        "severity": result.get("severity", "medium"),
        "passed": result.get("passed", False),
        "success_rate": success_rate,
        "prompt": result.get("prompt", ""),
        "response": result.get("failed_result", {}).get("response", "")
    })

df = pd.DataFrame(records)

# ====================== SIDEBAR FILTERS ======================
st.sidebar.header("Filters")

types = st.sidebar.multiselect(
    "Attack Types",
    options=df["type"].unique(),
    default=df["type"].unique()
)

severity = st.sidebar.multiselect(
    "Severity",
    options=["high", "medium", "low"],
    default=["high", "medium", "low"]
)

df = df[(df["type"].isin(types)) & (df["severity"].isin(severity))]

# ====================== KEY METRICS ======================
st.subheader("📊 Summary Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Attacks", len(df))
col2.metric("Successful Attacks", int(df["passed"].sum()))
col3.metric("Avg Success Rate", f"{df['success_rate'].mean():.1%}")
col4.metric("High Severity", len(df[df["severity"] == "high"]))

st.divider()

# ====================== VISUALIZATION ======================
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Attack Types", "Top Attacks", "Raw Data"]
)

# ---------------------- OVERVIEW ----------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            df.groupby("severity")["success_rate"].mean().reset_index(),
            x="severity",
            y="success_rate",
            title="Success Rate by Severity",
            color="severity"
        )
        fig1.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(
            df.groupby("type")["success_rate"].mean().reset_index(),
            x="type",
            y="success_rate",
            title="Success Rate by Attack Type",
            color="success_rate",
            color_continuous_scale="Reds"
        )
        fig2.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------- ATTACK TYPES ----------------------
with tab2:
    fig = px.pie(
        df,
        names="type",
        title="Attack Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------- TOP ATTACKS ----------------------
with tab3:
    st.subheader("🔥 Top 5 Most Effective Attacks")

    top5 = df.sort_values("success_rate", ascending=False).head(5)
    st.dataframe(top5[["rule", "type", "severity", "success_rate"]])

# ---------------------- RAW DATA ----------------------
with tab4:
    st.subheader("Full Dataset")
    st.dataframe(df, use_container_width=True)

# ====================== OPTIONAL LIVE OLLAMA TEST ======================
st.divider()
st.subheader("🔴 Live Model Test (Ollama)")

try:
    models = [m["name"] for m in ollama.list().get("models", [])]
    model = st.selectbox("Select Model", models)

    prompt = st.text_area("Test Prompt")

    if st.button("Run"):
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        st.success("Response")
        st.write(response["message"]["content"])

except:
    st.warning("Ollama not running. Start with: ollama serve")