from __future__ import annotations

import numpy as np
import pandas as pd


MATURITIES = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]


def government_curve() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Maturity": MATURITIES,
            "Government Yield": [0.0310, 0.0320, 0.0330, 0.0345, 0.0355, 0.0375, 0.0390, 0.0410, 0.0435, 0.0445],
        }
    )


def credit_spread_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Maturity": MATURITIES,
            "AAA": [18, 20, 23, 28, 32, 38, 43, 48, 55, 60],
            "AA": [28, 32, 38, 45, 52, 60, 67, 75, 85, 92],
            "A": [45, 52, 62, 75, 87, 102, 115, 130, 150, 165],
            "BBB": [85, 95, 110, 135, 155, 180, 205, 235, 270, 300],
            "BB": [180, 205, 240, 290, 340, 410, 470, 550, 650, 730],
            "B": [350, 390, 440, 520, 610, 720, 830, 950, 1120, 1280],
        }
    )


def corporate_curve(rating: str = "BBB") -> pd.DataFrame:
    rating = rating.upper()
    spreads = credit_spread_table()
    if rating not in spreads.columns:
        rating = "BBB"
    curve = government_curve().merge(spreads[["Maturity", rating]], on="Maturity")
    curve = curve.rename(columns={rating: "Credit Spread bps"})
    curve["Corporate Yield"] = curve["Government Yield"] + curve["Credit Spread bps"] / 10_000
    curve["Rating"] = rating
    return curve


def interpolate_yield(curve: pd.DataFrame, maturity: float, column: str) -> float:
    clean = curve[["Maturity", column]].dropna().sort_values("Maturity")
    return float(np.interp(float(maturity), clean["Maturity"], clean[column]))


def curve_statistics(curve: pd.DataFrame, column: str) -> dict[str, float]:
    y3m = interpolate_yield(curve, 0.25, column)
    y2 = interpolate_yield(curve, 2, column)
    y5 = interpolate_yield(curve, 5, column)
    y10 = interpolate_yield(curve, 10, column)
    y30 = interpolate_yield(curve, 30, column)
    return {
        "3M": y3m,
        "2Y": y2,
        "5Y": y5,
        "10Y": y10,
        "30Y": y30,
        "10Y-2Y": y10 - y2,
        "30Y-3M": y30 - y3m,
        "5Y-2Y": y5 - y2,
        "Level": float(curve[column].mean()),
    }


def apply_curve_scenario(curve: pd.DataFrame, parallel_bps: float = 0, slope_bps: float = 0, curvature_bps: float = 0, columns: list[str] | None = None) -> pd.DataFrame:
    columns = columns or ["Government Yield"]
    out = curve.copy()
    m = out["Maturity"].astype(float)
    scaled = (m - m.min()) / (m.max() - m.min())
    slope_component = (scaled - 0.5) * 2 * slope_bps
    curvature_component = -4 * (scaled - 0.5) ** 2 * curvature_bps + curvature_bps
    shift = (parallel_bps + slope_component + curvature_component) / 10_000
    for col in columns:
        if col in out.columns:
            out[col] = out[col] + shift
    return out


def implied_forward_rates(curve: pd.DataFrame, column: str = "Government Yield") -> pd.DataFrame:
    clean = curve[["Maturity", column]].dropna().sort_values("Maturity").copy()
    mats = clean["Maturity"].to_numpy(dtype=float)
    zero = clean[column].to_numpy(dtype=float)
    forwards = []
    for i in range(len(mats)):
        if i == 0:
            forwards.append(zero[i])
        else:
            fwd = ((1 + zero[i]) ** mats[i] / (1 + zero[i - 1]) ** mats[i - 1]) ** (1 / (mats[i] - mats[i - 1])) - 1
            forwards.append(float(fwd))
    return pd.DataFrame({"Maturity": mats, "Zero Yield": zero, "Implied Forward Rate": forwards})
