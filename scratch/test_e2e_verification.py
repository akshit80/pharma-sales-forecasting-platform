import requests
import os

BASE_URL = "http://localhost:8000/api/v1"

def run_e2e_test():
    print("=== Starting End-to-End Verification ===")
    
    # 1. Test Dataset Upload
    print("\n1. Testing Dataset Upload...")
    csv_path = "data/sample_pharma_sales.csv"
    with open(csv_path, "rb") as f:
        files = {"file": ("sample_pharma_sales.csv", f, "text/csv")}
        res = requests.post(f"{BASE_URL}/datasets/upload", files=files)
    
    assert res.status_code == 200, f"Upload failed: {res.text}"
    dataset_data = res.json()
    dataset_id = dataset_data["id"]
    print(f"   [SUCCESS] Uploaded dataset ID: {dataset_id} ({dataset_data['total_records']} rows)")
    
    # 2. Test EDA Endpoint
    print("\n2. Testing EDA Endpoint...")
    res = requests.get(f"{BASE_URL}/eda/{dataset_id}")
    assert res.status_code == 200, f"EDA failed: {res.text}"
    eda_data = res.json()
    print(f"   [SUCCESS] Total Revenue: ${eda_data['total_revenue']:,.2f}")
    print(f"   [SUCCESS] Total Sales Units: {eda_data['total_sales_units']:,}")
    print(f"   [SUCCESS] Active Products: {', '.join(eda_data['products'])}")
    
    # 3. Test Forecast Execution (XGBoost & Prophet)
    print("\n3. Testing Forecasting Engine...")
    forecast_req = {"dataset_id": dataset_id, "model_name": "XGBoost", "horizon_months": 6}
    res = requests.post(f"{BASE_URL}/forecast/run", json=forecast_req)
    assert res.status_code == 200, f"XGBoost forecast failed: {res.text}"
    xgb_fc = res.json()
    print(f"   [SUCCESS] XGBoost Forecast - MAE: {xgb_fc['mae']}, RMSE: {xgb_fc['rmse']}, MAPE: {xgb_fc['mape']}%")
    print(f"   [SUCCESS] Top XGBoost Features: {list(xgb_fc['feature_importance'].keys())[:3]}")

    forecast_req_p = {"dataset_id": dataset_id, "model_name": "Prophet", "horizon_months": 6}
    res = requests.post(f"{BASE_URL}/forecast/run", json=forecast_req_p)
    assert res.status_code == 200, f"Prophet forecast failed: {res.text}"
    p_fc = res.json()
    print(f"   [SUCCESS] Prophet Forecast - MAE: {p_fc['mae']}, RMSE: {p_fc['rmse']}, MAPE: {p_fc['mape']}%")

    # 4. Test Model Comparison
    print("\n4. Testing Model Comparison Endpoint...")
    res = requests.get(f"{BASE_URL}/forecast/compare/{dataset_id}?horizon_months=6")
    assert res.status_code == 200, f"Comparison failed: {res.text}"
    comp_data = res.json()
    print(f"   [SUCCESS] Compared {len(comp_data['models'])} models successfully.")

    # 5. Test What-If Scenario Analysis
    print("\n5. Testing What-If Scenario Analysis...")
    scenario_req = {
        "dataset_id": dataset_id,
        "model_name": "XGBoost",
        "horizon_months": 6,
        "price_change_pct": 10.0,
        "marketing_change_pct": 15.0
    }
    res = requests.post(f"{BASE_URL}/scenarios/run", json=scenario_req)
    assert res.status_code == 200, f"Scenario failed: {res.text}"
    sc_data = res.json()
    print(f"   [SUCCESS] Revenue Diff: ${sc_data['revenue_diff']:,.2f} ({sc_data['revenue_pct_change']}%)")

    # 6. Test Decision Intelligence Recommendations
    print("\n6. Testing Decision Intelligence Engine...")
    res = requests.get(f"{BASE_URL}/forecast/decision_intelligence/{dataset_id}")
    assert res.status_code == 200, f"Decision Intelligence failed: {res.text}"
    di_data = res.json()
    print(f"   [SUCCESS] Generated {len(di_data['recommendations'])} rule-based commercial recommendations:")
    for rec in di_data['recommendations']:
        print(f"     - [{rec['priority']} Priority] {rec['category']}: {rec['recommendation']}")

    # 7. Test Executive PDF Report Generation
    print("\n7. Testing PDF Executive Report Generator...")
    res = requests.post(f"{BASE_URL}/reports/generate?dataset_id={dataset_id}&model_name=XGBoost&horizon_months=6")
    assert res.status_code == 200, f"Report generation failed: {res.text}"
    report_data = res.json()
    report_id = report_data["id"]
    print(f"   [SUCCESS] Generated PDF Report ID: {report_id} at {report_data['file_path']}")

    # Download report check
    res_dl = requests.get(f"{BASE_URL}/reports/download/{report_id}")
    assert res_dl.status_code == 200 and len(res_dl.content) > 0, "PDF download failed"
    print(f"   [SUCCESS] Verified PDF download stream ({len(res_dl.content):,} bytes)")

    print("\n=== ALL END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_e2e_test()
