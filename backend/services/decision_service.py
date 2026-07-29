import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.models.models import SalesRecord
from backend.services.forecasting_service import ForecastingService

class DecisionService:

    @classmethod
    def generate_recommendations(cls, db: Session, dataset_id: str) -> list:
        """
        Rule-based commercial decision intelligence engine.
        Evaluates data trends and baseline forecasts to produce actionable recommendations.
        """
        records = db.query(SalesRecord).filter(SalesRecord.dataset_id == dataset_id).all()
        if not records:
            raise ValueError("No sales data available for recommendations.")

        df = pd.DataFrame([{
            "date": pd.to_datetime(r.date),
            "product_name": r.product_name,
            "region": r.region,
            "sales_units": r.sales_units,
            "unit_price": r.unit_price,
            "marketing_spend": r.marketing_spend,
            "revenue": r.revenue
        } for r in records])

        recommendations = []

        # -------------------------------------------------------------
        # Rule 1: Inventory Buffer Optimization (Forecast vs Baseline)
        # -------------------------------------------------------------
        forecast_res = ForecastingService.run_forecast(db, dataset_id, model_name="XGBoost", horizon_months=6)
        pred_units_sum = sum(p["predicted_units"] for p in forecast_res["predictions"])
        avg_monthly_pred = pred_units_sum / 6.0

        recent_3m = df[df["date"] >= df["date"].max() - pd.DateOffset(months=3)]
        recent_monthly_avg = recent_3m["sales_units"].sum() / 3.0

        if recent_monthly_avg > 0:
            growth_ratio = (avg_monthly_pred - recent_monthly_avg) / recent_monthly_avg
            if growth_ratio > 0.05:
                buffer_pct = min(30, int(growth_ratio * 100) + 5)
                recommendations.append({
                    "category": "Inventory Management",
                    "recommendation": f"Increase safety stock & inventory by {buffer_pct}% over the next 6 months.",
                    "reasoning": f"Projected monthly demand averaging {int(avg_monthly_pred):,} units reflects a {round(growth_ratio*100, 1)}% increase over recent baseline.",
                    "impact": "Mitigates stockouts and prevents lost revenue during peak demand periods.",
                    "priority": "High"
                })
            elif growth_ratio < -0.05:
                recommendations.append({
                    "category": "Inventory Management",
                    "recommendation": f"Reduce inventory purchasing by {abs(int(growth_ratio * 100))}% to prevent excess stock.",
                    "reasoning": f"Projected demand indicates a {abs(round(growth_ratio*100, 1))}% softening in monthly volume.",
                    "impact": "Minimizes holding costs and working capital tie-up.",
                    "priority": "Medium"
                })

        # -------------------------------------------------------------
        # Rule 2: Product Portfolio Demand Trajectory Analysis
        # -------------------------------------------------------------
        prod_trends = []
        for prod, prod_df in df.groupby("product_name"):
            sorted_p = prod_df.groupby("date")["sales_units"].sum().reset_index().sort_values("date")
            if len(sorted_p) >= 6:
                recent_half = sorted_p.tail(6)["sales_units"].values
                slope = (recent_half[-1] - recent_half[0]) / max(recent_half[0], 1)
                prod_trends.append({"product": prod, "slope": slope, "recent_volume": recent_half[-1]})

        declining_prods = [p for p in prod_trends if p["slope"] < -0.10]
        growing_prods = [p for p in prod_trends if p["slope"] > 0.15]

        if declining_prods:
            top_declining = sorted(declining_prods, key=lambda x: x["slope"])[0]
            recommendations.append({
                "category": "Product Portfolio",
                "recommendation": f"Demand for '{top_declining['product']}' is declining ({round(top_declining['slope']*100, 1)}% trend drop). Review pricing or promotional strategy.",
                "reasoning": "Sustained downward volume trend observed over recent 6 months.",
                "impact": "Protects gross margin and informs product lifecycle phase-out or repositioning.",
                "priority": "High"
            })

        if growing_prods:
            top_growing = sorted(growing_prods, key=lambda x: x["slope"], reverse=True)[0]
            recommendations.append({
                "category": "Product Portfolio",
                "recommendation": f"Prioritize supply allocation for top-growth product '{top_growing['product']}' (+{round(top_growing['slope']*100, 1)}% trend expansion).",
                "reasoning": "Strong positive demand trajectory across key market segments.",
                "impact": "Capitalizes on market momentum and maximizes commercial market share.",
                "priority": "High"
            })

        # -------------------------------------------------------------
        # Rule 3: Regional Growth Potential
        # -------------------------------------------------------------
        reg_df = df.groupby("region").agg({"sales_units": "sum", "revenue": "sum"}).reset_index()
        reg_df["share"] = reg_df["revenue"] / reg_df["revenue"].sum()
        top_region = reg_df.sort_values("revenue", ascending=False).iloc[0]

        recommendations.append({
            "category": "Regional Commercial Strategy",
            "recommendation": f"Region '{top_region['region']}' displays highest commercial contribution ({round(top_region['share']*100, 1)}% of revenue). Expand distribution channels.",
            "reasoning": f"Generates ${top_region['revenue']:,.2f} total revenue with consistent prescription volume.",
            "impact": "Directs sales force deployment to high-yield commercial territories.",
            "priority": "Medium"
        })

        # -------------------------------------------------------------
        # Rule 4: Marketing Efficiency & ROI Efficiency Check
        # -------------------------------------------------------------
        df["year_month"] = df["date"].dt.to_period("M")
        mkt_trend = df.groupby("year_month").agg({"marketing_spend": "sum", "revenue": "sum"}).reset_index()
        mkt_trend["roi_ratio"] = mkt_trend["revenue"] / np.maximum(mkt_trend["marketing_spend"], 1.0)

        if len(mkt_trend) >= 6:
            recent_roi = mkt_trend.tail(3)["roi_ratio"].mean()
            earlier_roi = mkt_trend.iloc[-6:-3]["roi_ratio"].mean()
            if recent_roi < earlier_roi * 0.85:
                recommendations.append({
                    "category": "Marketing Effectiveness",
                    "recommendation": "Marketing ROI efficiency is decreasing. Reallocate ad spend to top-performing digital & HCP channels.",
                    "reasoning": f"Revenue generated per marketing dollar decreased from ${round(earlier_roi, 2)} to ${round(recent_roi, 2)} in recent quarters.",
                    "impact": "Optimizes commercial expenditure and improves operating margin.",
                    "priority": "High"
                })

        # -------------------------------------------------------------
        # Rule 5: Seasonal Pre-Q4 Stocking Warning
        # -------------------------------------------------------------
        df["month_num"] = df["date"].dt.month
        q4_share = df[df["month_num"].isin([10, 11, 12])]["sales_units"].sum() / max(df["sales_units"].sum(), 1.0)

        if q4_share > 0.28:
            recommendations.append({
                "category": "Supply Chain & Seasonal Stocking",
                "recommendation": "Initiate Q4 seasonal inventory buildup by end of August/September.",
                "reasoning": f"Historical data shows Q4 accounts for {round(q4_share*100, 1)}% of annual sales volume due to year-end healthcare budget fulfillment.",
                "impact": "Eliminates Q4 supply bottleneck risk and ensures fulfillment of peak customer orders.",
                "priority": "Medium"
            })

        return recommendations
