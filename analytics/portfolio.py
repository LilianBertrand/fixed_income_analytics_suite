from __future__ import annotations

import pandas as pd

from .bonds import BondSpec, bond_metric_summary, bond_price, convexity, modified_duration, rate_scenario_analysis


REQUIRED_COLUMNS = ["Name", "Issuer Type", "Rating", "Face Value", "Coupon Rate", "Maturity", "Yield", "Frequency"]


def default_portfolio() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Name": "French OAT 2029", "Issuer Type": "Government", "Country": "France", "Sector": "Sovereign", "Rating": "AA", "Face Value": 1_200_000, "Coupon Rate": 0.030, "Maturity": 3.2, "Yield": 0.032, "Frequency": 1, "Credit Spread bps": 0},
            {"Name": "German Bund 2034", "Issuer Type": "Government", "Country": "Germany", "Sector": "Sovereign", "Rating": "AAA", "Face Value": 1_000_000, "Coupon Rate": 0.026, "Maturity": 8.1, "Yield": 0.029, "Frequency": 1, "Credit Spread bps": 0},
            {"Name": "US Treasury 10Y", "Issuer Type": "Government", "Country": "United States", "Sector": "Sovereign", "Rating": "AAA", "Face Value": 850_000, "Coupon Rate": 0.041, "Maturity": 9.5, "Yield": 0.043, "Frequency": 2, "Credit Spread bps": 0},
            {"Name": "Bank Senior Preferred", "Issuer Type": "Corporate", "Country": "France", "Sector": "Financials", "Rating": "A", "Face Value": 700_000, "Coupon Rate": 0.052, "Maturity": 5.0, "Yield": 0.058, "Frequency": 2, "Credit Spread bps": 140},
            {"Name": "Utility Green Bond", "Issuer Type": "Corporate", "Country": "Spain", "Sector": "Utilities", "Rating": "BBB", "Face Value": 600_000, "Coupon Rate": 0.047, "Maturity": 7.0, "Yield": 0.061, "Frequency": 1, "Credit Spread bps": 220},
            {"Name": "Industrial Corporate", "Issuer Type": "Corporate", "Country": "Germany", "Sector": "Industrials", "Rating": "BBB", "Face Value": 520_000, "Coupon Rate": 0.055, "Maturity": 6.2, "Yield": 0.064, "Frequency": 2, "Credit Spread bps": 250},
            {"Name": "Telecom Hybrid", "Issuer Type": "Corporate", "Country": "Netherlands", "Sector": "Telecom", "Rating": "BB", "Face Value": 400_000, "Coupon Rate": 0.073, "Maturity": 4.5, "Yield": 0.088, "Frequency": 2, "Credit Spread bps": 510},
            {"Name": "High Yield Consumer", "Issuer Type": "Corporate", "Country": "Italy", "Sector": "Consumer", "Rating": "B", "Face Value": 300_000, "Coupon Rate": 0.092, "Maturity": 3.5, "Yield": 0.119, "Frequency": 2, "Credit Spread bps": 790},
        ]
    )


def validate_portfolio(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError("Portfolio is empty.")


def row_to_spec(row: pd.Series) -> BondSpec:
    return BondSpec(
        face_value=float(row["Face Value"]),
        coupon_rate=float(row["Coupon Rate"]),
        maturity_years=float(row["Maturity"]),
        yield_to_maturity=float(row["Yield"]),
        frequency=int(row["Frequency"]),
    )


def enrich_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    validate_portfolio(df)
    rows = []
    for _, row in df.iterrows():
        spec = row_to_spec(row)
        metrics = bond_metric_summary(spec)
        out = row.to_dict()
        out.update(metrics)
        out["Price per 100"] = metrics["Clean Price per 100"]
        out["Market Value"] = metrics["Market Value"]
        out["DV01"] = metrics["DV01"]
        out["Yield Contribution"] = 0.0
        rows.append(out)
    enriched = pd.DataFrame(rows)
    total = enriched["Market Value"].sum()
    enriched["Weight"] = enriched["Market Value"] / total if total else 0.0
    enriched["Duration Contribution"] = enriched["Weight"] * enriched["Modified Duration"]
    enriched["Convexity Contribution"] = enriched["Weight"] * enriched["Convexity"]
    enriched["DV01 Contribution"] = enriched["DV01"] / enriched["DV01"].sum() if enriched["DV01"].sum() else 0.0
    enriched["Yield Contribution"] = enriched["Weight"] * enriched["Yield"]
    if "Credit Spread bps" not in enriched.columns:
        enriched["Credit Spread bps"] = 0
    enriched["Spread Contribution bps"] = enriched["Weight"] * enriched["Credit Spread bps"]
    return enriched


def portfolio_summary(df: pd.DataFrame) -> dict[str, float]:
    e = enrich_portfolio(df)
    return {
        "Market Value": float(e["Market Value"].sum()),
        "Weighted Yield": float(e["Yield Contribution"].sum()),
        "Weighted Duration": float(e["Duration Contribution"].sum()),
        "Weighted Convexity": float(e["Convexity Contribution"].sum()),
        "Portfolio DV01": float(e["DV01"].sum()),
        "Average Spread bps": float(e["Spread Contribution bps"].sum()),
        "Corporate Weight": float(e.loc[e["Issuer Type"].str.lower().eq("corporate"), "Weight"].sum()),
        "High Yield Weight": float(e.loc[e["Rating"].isin(["BB", "B", "CCC"]), "Weight"].sum()),
    }


def portfolio_rate_scenarios(df: pd.DataFrame, shocks_bps: list[float]) -> pd.DataFrame:
    rows = []
    for shock in shocks_bps:
        base = 0.0
        stressed = 0.0
        for _, row in df.iterrows():
            spec = row_to_spec(row)
            scenario = rate_scenario_analysis(spec, [shock]).iloc[0]
            base += scenario["Exact Price"] - scenario["Exact P&L"]
            stressed += scenario["Exact Price"]
        rows.append({"Shock bps": shock, "Portfolio Value": stressed, "P&L": stressed - base, "Return": stressed / base - 1})
    return pd.DataFrame(rows)


def portfolio_two_factor_stress(df: pd.DataFrame, rate_shocks_bps: list[float], spread_shocks_bps: list[float]) -> pd.DataFrame:
    rows = []
    base_value = enrich_portfolio(df)["Market Value"].sum()
    for rate_shock in rate_shocks_bps:
        for spread_shock in spread_shocks_bps:
            stressed_value = 0.0
            for _, row in df.iterrows():
                issuer_type = str(row.get("Issuer Type", "")).lower()
                total_shock = rate_shock + (spread_shock if issuer_type == "corporate" else 0)
                spec = row_to_spec(row)
                shocked_yield = float(row["Yield"]) + total_shock / 10_000
                stressed_value += bond_price(BondSpec(spec.face_value, spec.coupon_rate, spec.maturity_years, shocked_yield, spec.frequency))
            rows.append(
                {
                    "Rate Shock bps": rate_shock,
                    "Spread Shock bps": spread_shock,
                    "Portfolio Value": stressed_value,
                    "P&L": stressed_value - base_value,
                    "Return": stressed_value / base_value - 1,
                }
            )
    return pd.DataFrame(rows)


def exposure_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    e = enrich_portfolio(df)
    if group_col not in e.columns:
        return pd.DataFrame(columns=[group_col, "Market Value", "Weight", "DV01", "Duration Contribution"])
    out = (
        e.groupby(group_col, dropna=False)
        .agg(
            Market_Value=("Market Value", "sum"),
            Weight=("Weight", "sum"),
            DV01=("DV01", "sum"),
            Duration_Contribution=("Duration Contribution", "sum"),
            Average_Yield=("Yield", lambda s: float((s * e.loc[s.index, "Weight"]).sum() / e.loc[s.index, "Weight"].sum()) if e.loc[s.index, "Weight"].sum() else 0),
        )
        .reset_index()
    )
    return out.sort_values("Market_Value", ascending=False)
