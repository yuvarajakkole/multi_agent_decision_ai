import json
from langchain.tools import tool
from pathlib import Path
from functools import lru_cache
from config.settings import DATASET_PATH


# ---------------------------------------------------------
# LOAD DATASET
# ---------------------------------------------------------

@tool
@lru_cache(maxsize=2)
def load_company_dataset():

    """
    Load RA Groups internal dataset.
    """

    with open(DATASET_PATH, "r", encoding="utf-8") as f:

        data = json.load(f)

    return data


# ---------------------------------------------------------
# COMPANY STRENGTH ANALYSIS
# ---------------------------------------------------------

@tool
def extract_company_strengths(dataset: dict):
    """Extract key company strengths based on core segments."""

    profile = dataset.get("company_profile", {})

    segments = profile.get("core_segments", [])

    strengths = []

    if "Retail lending" in segments:
        strengths.append("Strong retail lending capabilities")

    if "SME working capital loans" in segments:
        strengths.append("Strong SME lending platform")

    if "Embedded finance partnerships" in segments:
        strengths.append("Embedded finance integration experience")

    return strengths


# ---------------------------------------------------------
# PAST EXPANSION ANALYSIS
# ---------------------------------------------------------

@tool
def analyze_past_expansions(dataset: dict):
    """Analyze past expansion efforts to identify patterns of success and failure."""

    expansions = dataset.get("past_expansions", [])

    markets = []

    success_count = 0

    for exp in expansions:

        markets.append(exp.get("market"))

        if exp.get("status") == "Success":
            success_count += 1

    return {
        "markets": markets,
        "success_count": success_count
    }


# ---------------------------------------------------------
# RESOURCE CAPACITY
# ---------------------------------------------------------

@tool
def evaluate_resource_capacity(dataset: dict):
    """Evaluate current resource capacity to support expansion efforts."""

    resources = dataset.get("resources", {})

    engineers = resources.get("engineering_headcount", 0)
    data_science = resources.get("data_science_headcount", 0)

    score = 0

    score += engineers * 0.5
    score += data_science * 1.0

    score = min(score, 100)

    return round(score, 2)


# ---------------------------------------------------------
# FINANCIAL HEALTH
# ---------------------------------------------------------

@tool
def analyze_financial_history(dataset: dict):
    """Analyze financial history to assess stability and growth trajectory."""

    history = dataset.get("financial_history", [])

    if not history:
        return "No financial history available."

    latest = history[-1]

    revenue = latest.get("total_revenue_usd")
    margin = latest.get("ebit_margin_percent")

    return f"Latest revenue ${revenue} with EBIT margin {margin}%"