import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.models.models import Dataset, SalesRecord

class EDAService:

    @staticmethod
    def get_eda_metrics(db: Session, dataset_id: str) -> dict:
        """
        Calculates comprehensive Exploratory Data Analysis metrics for a given dataset.
        """
        records = db.query(SalesRecord).filter(SalesRecord.dataset_id == dataset_id).all()
        if not records:
            raise ValueError("Dataset not found or contains no records.")

        data = [{
            "date": str(r.date),
            "product_name": r.product_name,
            "therapeutic_area": r.therapeutic_area,
            "region": r.region,
            "sales_units": r.sales_units,
            "unit_price": r.unit_price,
            "marketing_spend": r.marketing_spend,
            "revenue": r.revenue
        } for r in records]

        df = pd.DataFrame(data)
        df["dt"] = pd.to_datetime(df["date"])

        # Summary KPIs
        total_records = len(df)
        min_date = df["date"].min()
        max_date = df["date"].max()
        total_revenue = float(df["revenue"].sum())
        total_sales_units = float(df["sales_units"].sum())

        products = sorted(df["product_name"].unique().tolist())
        regions = sorted(df["region"].unique().tolist())

        # Monthly aggregation
        df["month_str"] = df["dt"].dt.strftime("%Y-%m")
        monthly_df = df.groupby("month_str").agg({
            "sales_units": "sum",
            "revenue": "sum",
            "marketing_spend": "sum"
        }).reset_index()

        monthly_sales = monthly_df.to_dict(orient="records")

        # Product-wise aggregation
        prod_df = df.groupby("product_name").agg({
            "sales_units": "sum",
            "revenue": "sum"
        }).reset_index()
        prod_df["share_pct"] = (prod_df["revenue"] / total_revenue * 100).round(2)
        product_sales = prod_df.sort_values("revenue", ascending=False).to_dict(orient="records")

        # Region-wise aggregation
        reg_df = df.groupby("region").agg({
            "sales_units": "sum",
            "revenue": "sum"
        }).reset_index()
        reg_df["share_pct"] = (reg_df["revenue"] / total_revenue * 100).round(2)
        region_sales = reg_df.sort_values("revenue", ascending=False).to_dict(orient="records")

        # Basic statistical distribution
        numeric_cols = ["sales_units", "unit_price", "revenue", "marketing_spend"]
        basic_stats = {}
        for col in numeric_cols:
            basic_stats[col] = {
                "mean": round(float(df[col].mean()), 2),
                "std": round(float(df[col].std()), 2),
                "min": round(float(df[col].min()), 2),
                "median": round(float(df[col].median()), 2),
                "max": round(float(df[col].max()), 2)
            }

        # Seasonality decomposition (month of year average)
        df["month_num"] = df["dt"].dt.month
        seasonality_df = df.groupby("month_num").agg({
            "sales_units": "mean",
            "revenue": "mean"
        }).reset_index()
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        seasonality_df["month_name"] = seasonality_df["month_num"].apply(lambda m: month_names[m-1])
        seasonality = seasonality_df.to_dict(orient="records")

        # Missing values check
        missing_values = {col: int(df[col].isna().sum()) for col in numeric_cols}

        return {
            "dataset_id": dataset_id,
            "total_records": total_records,
            "date_range": {"start": min_date, "end": max_date},
            "total_revenue": round(total_revenue, 2),
            "total_sales_units": round(total_sales_units, 2),
            "products": products,
            "regions": regions,
            "monthly_sales": monthly_sales,
            "product_sales": product_sales,
            "region_sales": region_sales,
            "missing_values": missing_values,
            "basic_stats": basic_stats,
            "seasonality": seasonality
        }
