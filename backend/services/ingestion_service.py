import pandas as pd
import io
from sqlalchemy.orm import Session
from backend.models.models import Dataset, SalesRecord

REQUIRED_COLUMNS = {"date", "product_name", "region", "sales_units", "unit_price", "revenue"}

class IngestionService:

    @staticmethod
    def process_csv_file(db: Session, file_content: bytes, filename: str) -> Dataset:
        """
        Parses, validates, and stores sales CSV dataset into database.
        """
        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {str(e)}")

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Convert date
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Fill defaults
        if "therapeutic_area" not in df.columns:
            df["therapeutic_area"] = "General"
        else:
            df["therapeutic_area"] = df["therapeutic_area"].fillna("General")

        if "marketing_spend" not in df.columns:
            df["marketing_spend"] = 0.0
        else:
            df["marketing_spend"] = df["marketing_spend"].fillna(0.0)

        df["sales_units"] = pd.to_numeric(df["sales_units"], errors="coerce").fillna(0.0)
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(df["sales_units"] * df["unit_price"])

        # Create Dataset entry
        dataset = Dataset(
            filename=filename,
            file_path=f"data/uploads/{filename}",
            total_records=len(df)
        )
        db.add(dataset)
        db.flush()

        # Batch insert sales records
        records = []
        for _, row in df.iterrows():
            records.append(
                SalesRecord(
                    dataset_id=dataset.id,
                    date=row["date"],
                    product_name=str(row["product_name"]),
                    therapeutic_area=str(row["therapeutic_area"]),
                    region=str(row["region"]),
                    sales_units=float(row["sales_units"]),
                    unit_price=float(row["unit_price"]),
                    marketing_spend=float(row["marketing_spend"]),
                    revenue=float(row["revenue"])
                )
            )

        db.bulk_save_objects(records)
        db.commit()
        db.refresh(dataset)
        return dataset
