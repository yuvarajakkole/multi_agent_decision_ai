from pydantic import BaseModel


class FinancialAnalysis(BaseModel):

    expected_roi_percent: float

    projected_year1_revenue: float

    projected_year2_revenue: float

    payback_period_months: float

    risk_score: float

    financial_attractiveness: str

    macro_sector_sentiment: str