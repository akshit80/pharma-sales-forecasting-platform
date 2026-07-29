import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_sample_dataset(output_path: str):
    """
    Generates a realistic 3-year monthly pharmaceutical sales dataset across
    multiple products, therapeutic areas, and geographical regions.
    """
    np.random.seed(42)
    start_date = datetime(2021, 1, 1)
    months = 36
    
    dates = [start_date + timedelta(days=30 * i) for i in range(months)]
    dates = [d.replace(day=1) for d in dates]
    
    products = [
        {"name": "CardioVasc-X", "area": "Cardiology", "base_price": 120.0, "base_volume": 5000},
        {"name": "OncoShield-A", "area": "Oncology", "base_price": 450.0, "base_volume": 1200},
        {"name": "NeuroCalm", "area": "Neurology", "base_price": 85.0, "base_volume": 8000},
        {"name": "ImmunoFlex", "area": "Immunology", "base_price": 230.0, "base_volume": 3500},
        {"name": "DiabeCare", "area": "Endocrinology", "base_price": 65.0, "base_volume": 11000}
    ]
    
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    
    records = []
    
    for date_idx, dt in enumerate(dates):
        month_num = dt.month
        seasonality = 1.0 + 0.15 * np.sin(2 * np.pi * (month_num - 1) / 12) + (0.1 if month_num in [10, 11, 12] else 0.0)
        trend = 1.0 + (date_idx / months) * 0.25
        
        for prod in products:
            for region in regions:
                region_factor = {
                    "North America": 1.4,
                    "Europe": 1.1,
                    "Asia Pacific": 0.9,
                    "Latin America": 0.6
                }[region]
                
                marketing_spend = np.round(np.random.normal(15000, 3000) * region_factor * trend, 2)
                marketing_spend = max(marketing_spend, 2000.0)
                
                price_noise = np.random.uniform(-0.05, 0.05)
                unit_price = np.round(prod["base_price"] * (1.0 + price_noise), 2)
                
                marketing_lift = 1.0 + (marketing_spend / 100000.0)
                noise = np.random.normal(1.0, 0.08)
                
                sales_volume = int(prod["base_volume"] * region_factor * seasonality * trend * marketing_lift * noise)
                sales_volume = max(sales_volume, 10)
                
                revenue = np.round(sales_volume * unit_price, 2)
                
                records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "product_name": prod["name"],
                    "therapeutic_area": prod["area"],
                    "region": region,
                    "sales_units": sales_volume,
                    "unit_price": unit_price,
                    "marketing_spend": marketing_spend,
                    "revenue": revenue
                })
                
    df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Sample dataset generated successfully with {len(df)} rows at {output_path}")

if __name__ == "__main__":
    generate_sample_dataset("data/sample_pharma_sales.csv")
