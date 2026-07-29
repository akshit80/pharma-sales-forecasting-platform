import os
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.models import Report
from backend.services.eda_service import EDAService
from backend.services.forecasting_service import ForecastingService
from backend.services.decision_service import DecisionService

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None or not os.access(".", os.W_OK)

class ReportService:

    @classmethod
    def generate_pdf_report(cls, db: Session, dataset_id: str, model_name: str = "XGBoost", horizon_months: int = 6) -> Report:
        """
        Generates a professional executive PDF commercial analytics & forecast report.
        """
        eda = EDAService.get_eda_metrics(db, dataset_id)
        forecast = ForecastingService.run_forecast(db, dataset_id, model_name, horizon_months)
        recommendations = DecisionService.generate_recommendations(db, dataset_id)

        target_dir = "/tmp/reports" if IS_VERCEL else "data/reports"
        os.makedirs(target_dir, exist_ok=True)
        report_filename = f"executive_report_{dataset_id[:8]}_{int(datetime.utcnow().timestamp())}.pdf"
        output_path = os.path.join(target_dir, report_filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        primary_color = colors.HexColor("#1E3A8A")
        secondary_color = colors.HexColor("#0D9488")
        dark_text = colors.HexColor("#1F2937")

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=primary_color,
            spaceAfter=6
        )

        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=secondary_color,
            spaceBefore=12,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=dark_text
        )

        elements = []

        elements.append(Paragraph("Pharmaceutical Demand Forecast & Executive Strategy Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%B %d, %Y')} | Dataset ID: {dataset_id}", subtitle_style))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph("1. Executive Summary KPIs", h2_style))

        kpi_data = [
            [
                Paragraph("<b>Total Historical Revenue</b>", body_style),
                Paragraph(f"${eda['total_revenue']:,.2f}", body_style),
                Paragraph("<b>Total Volume Sold</b>", body_style),
                Paragraph(f"{int(eda['total_sales_units']):,} units", body_style)
            ],
            [
                Paragraph("<b>Active Portfolio Products</b>", body_style),
                Paragraph(f"{len(eda['products'])} Products", body_style),
                Paragraph("<b>Geographic Regions</b>", body_style),
                Paragraph(f"{len(eda['regions'])} Regions", body_style)
            ]
        ]

        kpi_table = Table(kpi_data, colWidths=[130, 130, 130, 130])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph(f"2. Demand Forecast Projections ({model_name} Model - {horizon_months} Months)", h2_style))
        
        metrics_text = f"<b>Model Performance:</b> MAE = {forecast['mae']} | RMSE = {forecast['rmse']} | <b>MAPE = {forecast['mape']}%</b>"
        elements.append(Paragraph(metrics_text, body_style))
        elements.append(Spacer(1, 6))

        fc_table_data = [["Forecast Date", "Predicted Units", "Lower Bound", "Upper Bound", "Est. Revenue ($)"]]
        for p in forecast["predictions"]:
            fc_table_data.append([
                p["date"],
                f"{int(p['predicted_units']):,}",
                f"{int(p['lower_bound_units']):,}" if p['lower_bound_units'] is not None else "-",
                f"{int(p['upper_bound_units']):,}" if p['upper_bound_units'] is not None else "-",
                f"${p['predicted_revenue']:,.2f}"
            ])

        fc_table = Table(fc_table_data, colWidths=[100, 100, 100, 100, 120])
        fc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        elements.append(fc_table)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph("3. Commercial Decision Intelligence & Recommendations", h2_style))

        rec_table_data = [["Category", "Priority", "Strategic Recommendation", "Expected Impact"]]
        for r in recommendations:
            rec_table_data.append([
                Paragraph(f"<b>{r['category']}</b>", body_style),
                Paragraph(f"<font color='{'red' if r['priority']=='High' else 'orange'}'><b>{r['priority']}</b></font>", body_style),
                Paragraph(f"{r['recommendation']}<br/><font color='#4B5563'><i>Reason: {r['reasoning']}</i></font>", body_style),
                Paragraph(r['impact'], body_style)
            ])

        rec_table = Table(rec_table_data, colWidths=[110, 60, 210, 140])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(KeepTogether(rec_table))

        doc.build(elements)

        report = Report(
            dataset_id=dataset_id,
            file_path=output_path
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return report
