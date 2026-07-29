import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.services.forecasting_service import ForecastingService

class ScenarioService:

    PRICE_ELASTICITY = -0.85        # % volume change per 1% price change
    MARKETING_ELASTICITY = 0.25     # % volume change per 1% marketing spend change

    @classmethod
    def run_scenario(
        cls, 
        db: Session, 
        dataset_id: str, 
        model_name: str = "XGBoost", 
        horizon_months: int = 6,
        price_change_pct: float = 0.0,
        marketing_change_pct: float = 0.0
    ) -> dict:
        """
        Calculates baseline forecast and simulates modified forecast based on price & marketing changes.
        """
        # Run baseline forecast
        baseline = ForecastingService.run_forecast(db, dataset_id, model_name, horizon_months)
        predictions = baseline["predictions"]

        monthly_df = ForecastingService._prepare_monthly_time_series(db, dataset_id)
        base_unit_price = float(monthly_df["unit_price"].mean())
        new_unit_price = base_unit_price * (1.0 + (price_change_pct / 100.0))

        # Net volume multiplier from elasticity inputs
        volume_multiplier = (1.0 + (price_change_pct * cls.PRICE_ELASTICITY / 100.0)) * \
                            (1.0 + (marketing_change_pct * cls.MARKETING_ELASTICITY / 100.0))
        volume_multiplier = max(0.1, volume_multiplier)

        comparison_list = []
        tot_base_units = 0.0
        tot_base_rev = 0.0
        tot_recalc_units = 0.0
        tot_recalc_rev = 0.0

        for p in predictions:
            b_units = float(p["predicted_units"])
            b_rev = float(p["predicted_revenue"])

            r_units = round(b_units * volume_multiplier, 2)
            r_rev = round(r_units * new_unit_price, 2)

            tot_base_units += b_units
            tot_base_rev += b_rev
            tot_recalc_units += r_units
            tot_recalc_rev += r_rev

            comparison_list.append({
                "date": p["date"],
                "baseline_units": b_units,
                "recalculated_units": r_units,
                "baseline_revenue": b_rev,
                "recalculated_revenue": r_rev
            })

        units_diff = round(tot_recalc_units - tot_base_units, 2)
        revenue_diff = round(tot_recalc_rev - tot_base_rev, 2)
        units_pct_change = round((units_diff / max(tot_base_units, 1.0)) * 100, 2)
        revenue_pct_change = round((revenue_diff / max(tot_base_rev, 1.0)) * 100, 2)

        return {
            "dataset_id": dataset_id,
            "price_change_pct": price_change_pct,
            "marketing_change_pct": marketing_change_pct,
            "baseline_units": round(tot_base_units, 2),
            "baseline_revenue": round(tot_base_rev, 2),
            "recalculated_units": round(tot_recalc_units, 2),
            "recalculated_revenue": round(tot_recalc_rev, 2),
            "units_diff": units_diff,
            "revenue_diff": revenue_diff,
            "units_pct_change": units_pct_change,
            "revenue_pct_change": revenue_pct_change,
            "forecast_comparison": comparison_list
        }
