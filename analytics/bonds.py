from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BondSpec:
    face_value: float = 1_000_000.0
    coupon_rate: float = 0.04
    maturity_years: float = 5.0
    yield_to_maturity: float = 0.045
    frequency: int = 2

    def validate(self) -> None:
        if self.face_value <= 0:
            raise ValueError("Face value must be positive.")
        if self.coupon_rate < 0:
            raise ValueError("Coupon rate cannot be negative.")
        if self.maturity_years <= 0:
            raise ValueError("Maturity must be positive.")
        if self.yield_to_maturity <= -0.95:
            raise ValueError("Yield is too low for discounting.")
        if int(self.frequency) not in {1, 2, 4, 12}:
            raise ValueError("Frequency must be one of: 1, 2, 4, 12.")


def _periods(spec: BondSpec) -> np.ndarray:
    n_periods = max(1, int(round(spec.maturity_years * spec.frequency)))
    return np.arange(1, n_periods + 1, dtype=float)


def cashflow_table(spec: BondSpec) -> pd.DataFrame:
    spec.validate()
    periods = _periods(spec)
    coupon = spec.face_value * spec.coupon_rate / spec.frequency
    cashflows = np.full(len(periods), coupon, dtype=float)
    cashflows[-1] += spec.face_value
    y_periodic = spec.yield_to_maturity / spec.frequency
    discount_factors = 1 / (1 + y_periodic) ** periods
    present_values = cashflows * discount_factors
    return pd.DataFrame(
        {
            "Period": periods.astype(int),
            "Time": periods / spec.frequency,
            "Cash Flow": cashflows,
            "Discount Factor": discount_factors,
            "Present Value": present_values,
        }
    )


def bond_price(spec: BondSpec) -> float:
    return float(cashflow_table(spec)["Present Value"].sum())


def price_per_100(spec: BondSpec) -> float:
    return float(bond_price(spec) / spec.face_value * 100)


def macaulay_duration(spec: BondSpec) -> float:
    cf = cashflow_table(spec)
    price = cf["Present Value"].sum()
    return float((cf["Time"] * cf["Present Value"]).sum() / price)


def modified_duration(spec: BondSpec) -> float:
    return float(macaulay_duration(spec) / (1 + spec.yield_to_maturity / spec.frequency))


def convexity(spec: BondSpec) -> float:
    cf = cashflow_table(spec)
    periods = cf["Period"].to_numpy(dtype=float)
    cashflows = cf["Cash Flow"].to_numpy(dtype=float)
    y_periodic = spec.yield_to_maturity / spec.frequency
    price = cf["Present Value"].sum()
    convexity_periodic = np.sum(cashflows * periods * (periods + 1) / (1 + y_periodic) ** (periods + 2)) / price
    return float(convexity_periodic / spec.frequency**2)


def dv01(spec: BondSpec) -> float:
    return float(bond_price(spec) * modified_duration(spec) / 10_000)


def price_from_yield(spec: BondSpec, ytm: float) -> float:
    return bond_price(
        BondSpec(
            face_value=spec.face_value,
            coupon_rate=spec.coupon_rate,
            maturity_years=spec.maturity_years,
            yield_to_maturity=ytm,
            frequency=spec.frequency,
        )
    )


def solve_ytm(
    target_price: float,
    face_value: float,
    coupon_rate: float,
    maturity_years: float,
    frequency: int,
    lower: float = -0.50,
    upper: float = 1.50,
    tolerance: float = 1e-10,
    max_iter: int = 300,
) -> float:
    if target_price <= 0:
        raise ValueError("Target price must be positive.")
    low, high = lower, upper
    for _ in range(max_iter):
        mid = (low + high) / 2
        mid_price = bond_price(BondSpec(face_value, coupon_rate, maturity_years, mid, frequency))
        if abs(mid_price - target_price) < tolerance:
            return float(mid)
        if mid_price > target_price:
            low = mid
        else:
            high = mid
    return float((low + high) / 2)


def rate_scenario_analysis(spec: BondSpec, shocks_bps: Iterable[float]) -> pd.DataFrame:
    base_price = bond_price(spec)
    mod_dur = modified_duration(spec)
    conv = convexity(spec)
    rows = []
    for shock in shocks_bps:
        dy = shock / 10_000
        shocked_yield = spec.yield_to_maturity + dy
        exact_price = price_from_yield(spec, shocked_yield)
        duration_pnl = -base_price * mod_dur * dy
        duration_convexity_pnl = base_price * (-mod_dur * dy + 0.5 * conv * dy**2)
        rows.append(
            {
                "Shock bps": float(shock),
                "Shocked Yield": shocked_yield,
                "Exact Price": exact_price,
                "Exact P&L": exact_price - base_price,
                "Exact Return": exact_price / base_price - 1,
                "Duration P&L": duration_pnl,
                "Duration + Convexity P&L": duration_convexity_pnl,
                "Approximation Error": duration_convexity_pnl - (exact_price - base_price),
            }
        )
    return pd.DataFrame(rows)


def two_factor_stress(spec: BondSpec, rate_shocks_bps: Iterable[float], spread_shocks_bps: Iterable[float]) -> pd.DataFrame:
    base = bond_price(spec)
    rows = []
    for rate_shock in rate_shocks_bps:
        for spread_shock in spread_shocks_bps:
            total_shock = (rate_shock + spread_shock) / 10_000
            stressed = price_from_yield(spec, spec.yield_to_maturity + total_shock)
            rows.append(
                {
                    "Rate Shock bps": float(rate_shock),
                    "Spread Shock bps": float(spread_shock),
                    "Total Shock bps": float(rate_shock + spread_shock),
                    "Stressed Price": stressed,
                    "P&L": stressed - base,
                    "Return": stressed / base - 1,
                }
            )
    return pd.DataFrame(rows)


def bond_metric_summary(spec: BondSpec) -> dict[str, float]:
    price = bond_price(spec)
    return {
        "Market Value": price,
        "Clean Price per 100": price / spec.face_value * 100,
        "Macaulay Duration": macaulay_duration(spec),
        "Modified Duration": modified_duration(spec),
        "Convexity": convexity(spec),
        "DV01": dv01(spec),
        "Yield": spec.yield_to_maturity,
        "Coupon Rate": spec.coupon_rate,
    }
