import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

class APIClient:

    @staticmethod
    def get_datasets():
        try:
            res = requests.get(f"{API_BASE_URL}/datasets/")
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
        return None

    @staticmethod
    def upload_dataset(file_bytes, filename):
        files = {"file": (filename, file_bytes, "text/csv")}
        res = requests.post(f"{API_BASE_URL}/datasets/upload", files=files)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_eda(dataset_id):
        res = requests.get(f"{API_BASE_URL}/eda/{dataset_id}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def run_forecast(dataset_id, model_name, horizon_months):
        payload = {
            "dataset_id": dataset_id,
            "model_name": model_name,
            "horizon_months": horizon_months
        }
        res = requests.post(f"{API_BASE_URL}/forecast/run", json=payload)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def compare_models(dataset_id, horizon_months):
        res = requests.get(f"{API_BASE_URL}/forecast/compare/{dataset_id}?horizon_months={horizon_months}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def run_scenario(dataset_id, model_name, horizon_months, price_change_pct, marketing_change_pct):
        payload = {
            "dataset_id": dataset_id,
            "model_name": model_name,
            "horizon_months": horizon_months,
            "price_change_pct": price_change_pct,
            "marketing_change_pct": marketing_change_pct
        }
        res = requests.post(f"{API_BASE_URL}/scenarios/run", json=payload)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_decision_intelligence(dataset_id):
        res = requests.get(f"{API_BASE_URL}/forecast/decision_intelligence/{dataset_id}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def generate_report(dataset_id, model_name="XGBoost", horizon_months=6):
        res = requests.post(f"{API_BASE_URL}/reports/generate?dataset_id={dataset_id}&model_name={model_name}&horizon_months={horizon_months}")
        res.raise_for_status()
        return res.json()

    @staticmethod
    def download_report_url(report_id):
        return f"{API_BASE_URL}/reports/download/{report_id}"
