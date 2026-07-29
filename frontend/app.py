import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add root directory to sys.path for direct service imports if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.database import SessionLocal, Base, engine
from backend.services.ingestion_service import IngestionService
from backend.services.eda_service import EDAService
from backend.services.forecasting_service import ForecastingService
from backend.services.scenario_service import ScenarioService
from backend.services.decision_service import DecisionService
from backend.services.report_service import ReportService
from backend.models.models import Dataset

# Auto-initialize database tables on launch
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Pharma Sales Forecasting Platform",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive Theme CSS
st.markdown("""
    <style>
    .main {
        background-color: #F8FAFC;
    }
    .stApp header {
        background-color: #1E3A8A;
    }
    h1, h2, h3 {
        color: #1E3A8A;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

def get_db_session():
    return SessionLocal()

# Initialize session state for selected dataset
if "selected_dataset_id" not in st.session_state:
    st.session_state["selected_dataset_id"] = None

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/000000/pill.png", width=60)
st.sidebar.title("Pharma Analytics Platform")
st.sidebar.caption("Commercial Forecasting & Decision Intelligence")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Dataset Ingestion",
        "2. Exploratory Data Analysis",
        "3. Demand Forecasting",
        "4. Model Explainability",
        "5. Scenario Analysis",
        "6. Decision Intelligence",
        "7. Executive PDF Report"
    ]
)

db = get_db_session()

# Dataset Selector in Sidebar (if datasets exist)
datasets = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()

if datasets:
    dataset_options = {d.id: f"{d.filename} ({d.total_records} records)" for d in datasets}
    
    # Auto select first if none selected
    if not st.session_state["selected_dataset_id"] or st.session_state["selected_dataset_id"] not in dataset_options:
        st.session_state["selected_dataset_id"] = datasets[0].id

    st.sidebar.markdown("---")
    st.sidebar.subheader("Active Dataset")
    selected_id = st.sidebar.selectbox(
        "Choose dataset:",
        options=list(dataset_options.keys()),
        format_func=lambda x: dataset_options[x],
        index=list(dataset_options.keys()).index(st.session_state["selected_dataset_id"])
    )
    st.session_state["selected_dataset_id"] = selected_id
else:
    st.sidebar.warning("No datasets uploaded yet.")


# =====================================================================
# PAGE 1: DATASET INGESTION
# =====================================================================
if page == "1. Dataset Ingestion":
    st.title("📁 Dataset Ingestion & Validation")
    st.markdown("Upload pharmaceutical sales CSV datasets or load sample commercial sales data.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Upload CSV Dataset")
        uploaded_file = st.file_uploader("Select a pharmaceutical sales CSV file", type=["csv"])

        if uploaded_file is not None:
            if st.button("Upload & Ingest Dataset"):
                with st.spinner("Validating and parsing dataset..."):
                    try:
                        content = uploaded_file.read()
                        dataset = IngestionService.process_csv_file(db, content, uploaded_file.filename)
                        st.session_state["selected_dataset_id"] = dataset.id
                        st.success(f"Successfully ingested '{dataset.filename}' with {dataset.total_records} records!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ingestion failed: {str(e)}")

    with col2:
        st.subheader("Quick Start Sample Data")
        st.write("Click below to auto-load the included sample 3-year commercial sales dataset.")
        if st.button("Load Sample Dataset"):
            if os.path.exists("data/sample_pharma_sales.csv"):
                with open("data/sample_pharma_sales.csv", "rb") as f:
                    content = f.read()
                dataset = IngestionService.process_csv_file(db, content, "sample_pharma_sales.csv")
                st.session_state["selected_dataset_id"] = dataset.id
                st.success(f"Sample dataset loaded ({dataset.total_records} rows).")
                st.rerun()
            else:
                st.error("Sample dataset file not found at data/sample_pharma_sales.csv.")

    if datasets:
        st.markdown("---")
        st.subheader("Ingested Datasets Summary")
        ds_summary = [{
            "ID": d.id[:8],
            "Filename": d.filename,
            "Total Records": d.total_records,
            "Uploaded At": d.uploaded_at.strftime("%Y-%m-%d %H:%M")
        } for d in datasets]
        st.dataframe(pd.DataFrame(ds_summary), use_container_width=True)


# =====================================================================
# PAGE 2: EXPLORATORY DATA ANALYSIS (EDA)
# =====================================================================
elif page == "2. Exploratory Data Analysis":
    st.title("📊 Exploratory Data Analysis (EDA)")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first from Page 1.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]
        eda = EDAService.get_eda_metrics(db, dataset_id)

        # Top Executive KPI Cards
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Revenue", f"${eda['total_revenue']:,.2f}")
        kpi2.metric("Total Sales Volume", f"{int(eda['total_sales_units']):,} units")
        kpi3.metric("Date Horizon", f"{eda['date_range']['start']} to {eda['date_range']['end']}")
        kpi4.metric("Active Products", f"{len(eda['products'])} Products")

        st.markdown("---")

        # Row 1 Charts: Monthly Trend & Seasonality
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Monthly Revenue & Sales Unit Trend")
            monthly_df = pd.DataFrame(eda["monthly_sales"])
            fig_trend = px.line(
                monthly_df, 
                x="month_str", 
                y=["revenue", "sales_units"], 
                labels={"month_str": "Month", "value": "Amount"},
                title="Historical Monthly Sales Curve",
                color_discrete_sequence=["#1E3A8A", "#0D9488"]
            )
            fig_trend.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)

        with c2:
            st.subheader("Seasonal Patterns (Average Monthly Volume)")
            season_df = pd.DataFrame(eda["seasonality"])
            fig_season = px.bar(
                season_df,
                x="month_name",
                y="sales_units",
                color="sales_units",
                title="Annual Seasonality Distribution",
                color_continuous_scale="Blues"
            )
            fig_season.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_season, use_container_width=True)

        # Row 2 Charts: Product & Region Share
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Product Revenue Share")
            prod_df = pd.DataFrame(eda["product_sales"])
            fig_prod = px.pie(
                prod_df,
                values="revenue",
                names="product_name",
                hole=0.4,
                title="Revenue Contribution by Product",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_prod.update_layout(template="plotly_white")
            st.plotly_chart(fig_prod, use_container_width=True)

        with c4:
            st.subheader("Regional Sales Performance")
            reg_df = pd.DataFrame(eda["region_sales"])
            fig_reg = px.bar(
                reg_df,
                x="region",
                y="revenue",
                text="share_pct",
                color="revenue",
                title="Geographic Region Revenue ($)",
                color_continuous_scale="Teal"
            )
            fig_reg.update_layout(template="plotly_white")
            st.plotly_chart(fig_reg, use_container_width=True)

        # Row 3: Basic Statistics & Missing Values
        st.markdown("---")
        col_stat1, col_stat2 = st.columns([3, 1])
        with col_stat1:
            st.subheader("Basic Statistical Summary")
            st.dataframe(pd.DataFrame(eda["basic_stats"]), use_container_width=True)

        with col_stat2:
            st.subheader("Missing Values Check")
            st.write(pd.DataFrame(list(eda["missing_values"].items()), columns=["Column", "Missing Count"]))


# =====================================================================
# PAGE 3: DEMAND FORECASTING
# =====================================================================
elif page == "3. Demand Forecasting":
    st.title("📈 Demand Forecasting Studio")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 1])
        with col_ctrl1:
            model_choice = st.selectbox("Select Model:", ["XGBoost", "Prophet"])
        with col_ctrl2:
            horizon_choice = st.selectbox("Forecast Horizon:", [3, 6, 12], index=1)
        with col_ctrl3:
            st.write("")
            st.write("")
            run_btn = st.button("Run Forecast Model", use_container_width=True)

        tab1, tab2 = st.tabs(["Single Model Forecast", "Model Performance Comparison"])

        with tab1:
            if run_btn or "last_forecast" not in st.session_state:
                with st.spinner(f"Training {model_choice} model for {horizon_choice} months horizon..."):
                    res = ForecastingService.run_forecast(db, dataset_id, model_choice, horizon_choice)
                    st.session_state["last_forecast"] = res

            if "last_forecast" in st.session_state:
                fc = st.session_state["last_forecast"]

                # Display Metrics Cards
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Selected Model", fc["model_name"])
                m2.metric("Mean Absolute Error (MAE)", f"{fc['mae']}")
                m3.metric("Root Mean Squared Error (RMSE)", f"{fc['rmse']}")
                m4.metric("MAPE Error %", f"{fc['mape']}%")

                # Plot Forecast Curve
                pred_df = pd.DataFrame(fc["predictions"])
                pred_df["date"] = pd.to_datetime(pred_df["date"])

                # Fetch historical for graph context
                eda = EDAService.get_eda_metrics(db, dataset_id)
                hist_df = pd.DataFrame(eda["monthly_sales"])
                hist_df["date"] = pd.to_datetime(hist_df["month_str"])

                fig_fc = go.Figure()
                # Historical line
                fig_fc.add_trace(go.Scatter(
                    x=hist_df["date"], y=hist_df["sales_units"],
                    name="Historical Sales", line=dict(color="#1E3A8A", width=2.5)
                ))

                # Forecast line
                fig_fc.add_trace(go.Scatter(
                    x=pred_df["date"], y=pred_df["predicted_units"],
                    name=f"{fc['model_name']} Forecast", line=dict(color="#0D9488", width=3, dash="dash")
                ))

                # Confidence Interval (Upper & Lower Bounds)
                if pred_df["upper_bound_units"].notna().any():
                    fig_fc.add_trace(go.Scatter(
                        x=pd.concat([pred_df["date"], pred_df["date"][::-1]]),
                        y=pd.concat([pred_df["upper_bound_units"], pred_df["lower_bound_units"][::-1]]),
                        fill='toself',
                        fillcolor='rgba(13, 148, 136, 0.15)',
                        line=dict(color='rgba(255,255,255,0)'),
                        name='95% Confidence Interval'
                    ))

                fig_fc.update_layout(
                    title=f"{fc['model_name']} Projected Demand Curve ({fc['horizon_months']} Months Horizon)",
                    xaxis_title="Date",
                    yaxis_title="Sales Volume (Units)",
                    template="plotly_white"
                )
                st.plotly_chart(fig_fc, use_container_width=True)

                st.subheader("Monthly Projected Output Table")
                st.dataframe(pred_df, use_container_width=True)

        with tab2:
            st.subheader("Prophet vs. XGBoost Side-by-Side Model Comparison")
            if st.button("Run Model Comparison"):
                with st.spinner("Training Prophet & XGBoost models side-by-side..."):
                    comp = ForecastingService.compare_models(db, dataset_id, horizon_choice)
                    
                    st.dataframe(pd.DataFrame(comp["models"]), use_container_width=True)

                    hist_df = pd.DataFrame(comp["historical"])
                    p_df = pd.DataFrame(comp["prophet_forecast"])
                    x_df = pd.DataFrame(comp["xgboost_forecast"])

                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Scatter(x=hist_df["date"], y=hist_df["sales_units"], name="Historical", line=dict(color="black", width=2)))
                    fig_comp.add_trace(go.Scatter(x=p_df["date"], y=p_df["predicted_units"], name="Prophet Forecast", line=dict(color="#3B82F6", width=2.5, dash="dot")))
                    fig_comp.add_trace(go.Scatter(x=x_df["date"], y=x_df["predicted_units"], name="XGBoost Forecast", line=dict(color="#10B981", width=2.5, dash="dash")))

                    fig_comp.update_layout(title="Prophet vs. XGBoost Demand Projection Comparison", template="plotly_white")
                    st.plotly_chart(fig_comp, use_container_width=True)


# =====================================================================
# PAGE 4: MODEL EXPLAINABILITY
# =====================================================================
elif page == "4. Model Explainability":
    st.title("💡 Model Explainability & Feature Importance")
    st.markdown("Inspect key factors driving sales predictions generated by XGBoost.")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]
        res = ForecastingService.run_forecast(db, dataset_id, model_name="XGBoost", horizon_months=6)

        if res.get("feature_importance"):
            fi_dict = res["feature_importance"]
            fi_df = pd.DataFrame(list(fi_dict.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)

            c1, c2 = st.columns([3, 2])
            with c1:
                fig_fi = px.bar(
                    fi_df,
                    x="Importance",
                    y="Feature",
                    orientation="h",
                    title="XGBoost Feature Importance",
                    color="Importance",
                    color_continuous_scale="Blues"
                )
                fig_fi.update_layout(template="plotly_white")
                st.plotly_chart(fig_fi, use_container_width=True)

            with c2:
                st.subheader("Feature Impact Explanation")
                st.write("""
                - **`lag_1` / `rolling_3_mean`**: Prior sales trajectory is the strongest baseline indicator of near-term pharmaceutical refill volume.
                - **`marketing_spend`**: Commercial promotional expenditures directly expand HCP prescription velocity.
                - **`month` / `quarter`**: Captures strong annual seasonality (e.g. Q4 year-end insurance deductible fulfillment).
                - **`unit_price`**: Reflects price elasticity dynamics influencing purchasing volume.
                """)
        else:
            st.warning("Please run XGBoost model on Page 3 to extract feature importance.")


# =====================================================================
# PAGE 5: SCENARIO ANALYSIS
# =====================================================================
elif page == "5. Scenario Analysis":
    st.title("🎛️ What-If Scenario Analysis")
    st.markdown("Simulate how changes in unit pricing and marketing spend impact revenue and sales volume.")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            price_change = st.slider("Price Adjustment (%)", min_value=-20.0, max_value=30.0, value=5.0, step=1.0)
        with col_s2:
            marketing_change = st.slider("Marketing Spend Adjustment (%)", min_value=-50.0, max_value=50.0, value=15.0, step=5.0)

        scenario = ScenarioService.run_scenario(
            db, dataset_id, model_name="XGBoost", horizon_months=6,
            price_change_pct=price_change, marketing_change_pct=marketing_change
        )

        st.markdown("---")
        st.subheader("Projected Impact Summary")

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Baseline Units", f"{int(scenario['baseline_units']):,}")
        sc2.metric("Recalculated Units", f"{int(scenario['recalculated_units']):,}", delta=f"{scenario['units_pct_change']}%")
        sc3.metric("Baseline Revenue", f"${scenario['baseline_revenue']:,.2f}")
        sc4.metric("Recalculated Revenue", f"${scenario['recalculated_revenue']:,.2f}", delta=f"{scenario['revenue_pct_change']}%")

        comp_df = pd.DataFrame(scenario["forecast_comparison"])

        fig_sc = go.Figure()
        fig_sc.add_trace(go.Scatter(x=comp_df["date"], y=comp_df["baseline_revenue"], name="Baseline Revenue ($)", line=dict(color="#64748B", width=2)))
        fig_sc.add_trace(go.Scatter(x=comp_df["date"], y=comp_df["recalculated_revenue"], name="Scenario Revenue ($)", line=dict(color="#10B981", width=3)))
        fig_sc.update_layout(title="Baseline vs. Scenario Revenue Curve", template="plotly_white")

        st.plotly_chart(fig_sc, use_container_width=True)


# =====================================================================
# PAGE 6: DECISION INTELLIGENCE
# =====================================================================
elif page == "6. Decision Intelligence":
    st.title("🧠 Decision Intelligence & Recommendations")
    st.markdown("Rule-based explainable commercial insights automatically generated from sales patterns.")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]
        recommendations = DecisionService.generate_recommendations(db, dataset_id)

        for rec in recommendations:
            priority_color = "#EF4444" if rec["priority"] == "High" else "#F59E0B"
            st.markdown(f"""
                <div style="background-color: white; border-left: 6px solid {priority_color}; padding: 16px; border-radius: 6px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #1E3A8A;">{rec['category']}</h4>
                        <span style="background-color: {priority_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{rec['priority']} Priority</span>
                    </div>
                    <p style="font-size: 16px; font-weight: 600; margin-top: 8px; color: #1F2937;">👉 {rec['recommendation']}</p>
                    <p style="margin: 4px 0; color: #4B5563; font-size: 14px;"><b>Reasoning:</b> {rec['reasoning']}</p>
                    <p style="margin: 4px 0; color: #059669; font-size: 14px;"><b>Business Impact:</b> {rec['impact']}</p>
                </div>
            """, unsafe_allow_html=True)


# =====================================================================
# PAGE 7: EXECUTIVE PDF REPORT
# =====================================================================
elif page == "7. Executive PDF Report":
    st.title("📄 Executive PDF Report Generator")
    st.markdown("Generate and download a professional PDF executive report containing KPIs, forecasts, and recommendations.")

    if not st.session_state["selected_dataset_id"]:
        st.info("Please upload or select a dataset first.")
    else:
        dataset_id = st.session_state["selected_dataset_id"]

        if st.button("Generate Executive PDF Report"):
            with st.spinner("Assembling executive PDF report document..."):
                report = ReportService.generate_pdf_report(db, dataset_id, model_name="XGBoost", horizon_months=6)
                st.success(f"Report generated successfully!")

                with open(report.file_path, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=os.path.basename(report.file_path),
                    mime="application/pdf"
                )

db.close()
