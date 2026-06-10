from __future__ import annotations

import io
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
except Exception:  # graceful fallback if Plotly is not installed
    px = None
    go = None

from analytics.bonds import (
    BondSpec,
    bond_metric_summary,
    cashflow_table,
    rate_scenario_analysis,
    solve_ytm,
    two_factor_stress,
)
from analytics.curves import (
    apply_curve_scenario,
    corporate_curve,
    credit_spread_table,
    curve_statistics,
    government_curve,
    implied_forward_rates,
)
from analytics.portfolio import (
    default_portfolio,
    enrich_portfolio,
    exposure_table,
    portfolio_rate_scenarios,
    portfolio_summary,
    portfolio_two_factor_stress,
)

st.set_page_config(page_title="Fixed Income Analytics Suite", page_icon="FI", layout="wide")

CUSTOM_CSS = """
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2rem;}
.main-header {
    padding: 1.35rem 1.55rem;
    border-radius: 22px;
    background: linear-gradient(135deg, #101828 0%, #1D2939 48%, #344054 100%);
    color: white;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.08);
}
.main-header h1 {margin: 0; font-size: 2.35rem; letter-spacing: -0.03em;}
.main-header p {margin: 0.35rem 0 0 0; color: #EAECF0; max-width: 980px;}
.section-card {
    padding: 1rem 1.1rem;
    border-radius: 18px;
    background: #FFFFFF;
    border: 1px solid #EAECF0;
    box-shadow: 0 1px 2px rgba(16,24,40,0.05);
    margin-bottom: 0.7rem;
}
.small-muted {font-size: 0.88rem; color: #667085;}
.metric-note {font-size: 0.82rem; color: #667085; margin-top: -0.55rem;}
hr {margin-top: 0.7rem; margin-bottom: 1.1rem;}
[data-testid="stMetricValue"] {font-size: 1.55rem;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def pct(x: float) -> str:
    return f"{x:.2%}"


def bps_from_decimal(x: float) -> str:
    return f"{x * 10_000:,.0f} bps"


def bps(x: float) -> str:
    return f"{x:,.0f} bps"


def money(x: float) -> str:
    return f"{x:,.0f}"


def money2(x: float) -> str:
    return f"{x:,.2f}"


def plot_line(df: pd.DataFrame, x: str, y: list[str] | str, title: str = ""):
    if px is not None:
        fig = px.line(df, x=x, y=y, markers=True, title=title)
        fig.update_layout(margin=dict(l=10, r=10, t=48, b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.line_chart(df.set_index(x)[y], width="stretch")


def plot_bar(df: pd.DataFrame, x: str, y: str, title: str = ""):
    if px is not None:
        fig = px.bar(df, x=x, y=y, title=title)
        fig.update_layout(margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.bar_chart(df.set_index(x)[y], width="stretch")


def export_buttons(tables: dict[str, pd.DataFrame], base_name: str) -> None:
    if not tables:
        return
    first_df = next(iter(tables.values()))
    st.download_button(
        "Download main table as CSV",
        first_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{base_name}.csv",
        mime="text/csv",
    )
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for sheet_name, df in tables.items():
                clean_sheet = sheet_name[:31].replace("/", "-")
                df.to_excel(writer, index=False, sheet_name=clean_sheet)
        st.download_button(
            "Download full Excel report",
            buffer.getvalue(),
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        st.caption("Excel export unavailable because openpyxl is not installed. CSV export remains available.")


def header():
    st.markdown(
        """
        <div class="main-header">
            <h1>Fixed Income Analytics Suite</h1>
            <p>Bond pricing, duration, convexity, DV01, yield-curve scenarios, credit spreads, portfolio risk attribution and stress testing in one Streamlit application.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_portfolio_from_sidebar() -> pd.DataFrame:
    st.sidebar.subheader("Portfolio source")
    uploaded = st.sidebar.file_uploader("Upload CSV portfolio", type=["csv"])
    if uploaded is not None:
        return pd.read_csv(uploaded)
    return default_portfolio()


header()

with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "Module",
        [
            "Executive Dashboard",
            "Bond Pricing Lab",
            "Yield Curve Studio",
            "Credit Spread Monitor",
            "Portfolio Risk Workbench",
            "Stress Testing Matrix",
        ],
    )
    st.divider()
    st.caption("Synthetic default data. Educational analytics project, not investment advice.")

if page == "Executive Dashboard":
    portfolio_raw = load_portfolio_from_sidebar()
    enriched = enrich_portfolio(portfolio_raw)
    summary = portfolio_summary(portfolio_raw)

    st.subheader("Portfolio overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Market Value", money(summary["Market Value"]))
    c2.metric("Weighted Yield", pct(summary["Weighted Yield"]))
    c3.metric("Mod. Duration", f"{summary['Weighted Duration']:.2f}")
    c4.metric("DV01", money2(summary["Portfolio DV01"]))
    c5.metric("Avg Spread", bps(summary["Average Spread bps"]))

    st.markdown("<p class='metric-note'>DV01 estimates the portfolio P&L impact of a 1 bp upward move in yields.</p>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        shocks = [-200, -100, -50, 0, 50, 100, 150, 200, 300]
        scen = portfolio_rate_scenarios(portfolio_raw, shocks)
        plot_line(scen, "Shock bps", ["P&L"], "Portfolio P&L under parallel yield shocks")
    with right:
        rating_exp = exposure_table(portfolio_raw, "Rating")
        if px is not None:
            fig = px.pie(rating_exp, names="Rating", values="Market_Value", hole=0.48, title="Exposure by rating")
            fig.update_layout(margin=dict(l=10, r=10, t=48, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.dataframe(rating_exp, width="stretch")

    st.subheader("Risk attribution")
    a, b = st.columns(2)
    with a:
        duration = enriched[["Name", "Duration Contribution"]].sort_values("Duration Contribution", ascending=False)
        plot_bar(duration, "Name", "Duration Contribution", "Contribution to portfolio duration")
    with b:
        dv01 = enriched[["Name", "DV01"]].sort_values("DV01", ascending=False)
        plot_bar(dv01, "Name", "DV01", "DV01 by instrument")

    st.subheader("Detailed holdings")
    show_cols = ["Name", "Issuer Type", "Rating", "Sector", "Face Value", "Price per 100", "Market Value", "Weight", "Yield", "Modified Duration", "Convexity", "DV01", "Credit Spread bps"]
    existing = [c for c in show_cols if c in enriched.columns]
    st.dataframe(
        enriched[existing].style.format(
            {
                "Face Value": "{:,.0f}",
                "Price per 100": "{:.2f}",
                "Market Value": "{:,.0f}",
                "Weight": "{:.2%}",
                "Yield": "{:.2%}",
                "Modified Duration": "{:.2f}",
                "Convexity": "{:.2f}",
                "DV01": "{:,.2f}",
                "Credit Spread bps": "{:,.0f}",
            }
        ),
        width="stretch",
        height=360,
    )
    export_buttons({"Holdings": enriched, "Rate Scenarios": scen, "Rating Exposure": rating_exp}, "fixed_income_dashboard_report")

elif page == "Bond Pricing Lab":
    st.subheader("Single bond pricing and risk engine")
    st.markdown("This module prices a fixed-rate bond by discounted cash flows and explains the main risk measures used by rates and credit desks.")

    left, mid, right = st.columns(3)
    with left:
        face = st.number_input("Face value", min_value=1_000.0, value=1_000_000.0, step=50_000.0)
        coupon = st.number_input("Coupon rate", min_value=0.0, max_value=0.30, value=0.050, step=0.0025, format="%.4f")
    with mid:
        maturity = st.number_input("Maturity in years", min_value=0.25, max_value=50.0, value=7.0, step=0.25)
        ytm = st.number_input("Yield to maturity", min_value=-0.05, max_value=0.50, value=0.058, step=0.0025, format="%.4f")
    with right:
        frequency = st.selectbox("Coupon frequency", [1, 2, 4, 12], index=1)
        target_price = st.number_input("Market price for implied YTM", min_value=1.0, value=980_000.0, step=10_000.0)

    spec = BondSpec(face, coupon, maturity, ytm, frequency)
    metrics = bond_metric_summary(spec)
    implied_ytm = solve_ytm(target_price, face, coupon, maturity, frequency)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Market Value", money2(metrics["Market Value"]))
    c2.metric("Price per 100", f"{metrics['Clean Price per 100']:.2f}")
    c3.metric("Modified Duration", f"{metrics['Modified Duration']:.2f}")
    c4.metric("Convexity", f"{metrics['Convexity']:.2f}")
    c5.metric("Implied YTM", pct(implied_ytm))

    tab1, tab2, tab3 = st.tabs(["Cash flows", "Rate sensitivity", "2-factor stress"])
    with tab1:
        cf = cashflow_table(spec)
        plot_bar(cf, "Time", "Present Value", "Present value of bond cash flows")
        st.dataframe(
            cf.style.format({"Time": "{:.2f}", "Cash Flow": "{:,.2f}", "Discount Factor": "{:.6f}", "Present Value": "{:,.2f}"}),
            width="stretch",
            height=320,
        )
    with tab2:
        min_shock, max_shock = st.slider("Rate shock range in bps", -500, 500, (-250, 300), step=25)
        shocks = list(range(min_shock, max_shock + 1, 25))
        scen = rate_scenario_analysis(spec, shocks)
        plot_line(scen, "Shock bps", ["Exact P&L", "Duration P&L", "Duration + Convexity P&L"], "Exact vs approximated P&L")
        st.dataframe(
            scen.style.format({"Shocked Yield": "{:.2%}", "Exact Price": "{:,.2f}", "Exact P&L": "{:,.2f}", "Exact Return": "{:.2%}", "Duration P&L": "{:,.2f}", "Duration + Convexity P&L": "{:,.2f}", "Approximation Error": "{:,.2f}"}),
            width="stretch",
            height=340,
        )
    with tab3:
        rate_shocks = [-150, -50, 0, 50, 100, 200]
        spread_shocks = [-100, -25, 0, 50, 100, 200]
        stress = two_factor_stress(spec, rate_shocks, spread_shocks)
        matrix = stress.pivot(index="Spread Shock bps", columns="Rate Shock bps", values="P&L")
        if px is not None:
            fig = px.imshow(matrix, text_auto=".0f", aspect="auto", title="P&L heatmap: rates shock + credit spread shock")
            fig.update_layout(margin=dict(l=10, r=10, t=48, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.dataframe(matrix, width="stretch")
        st.caption("For a corporate bond, rates and spreads can both move. This matrix helps visualize combined market-risk and credit-spread risk.")

elif page == "Yield Curve Studio":
    st.subheader("Yield curve analytics")
    base_curve = government_curve()
    left, right = st.columns([0.9, 1.1])
    with left:
        parallel = st.slider("Parallel shift", -300, 300, 0, step=10)
        slope = st.slider("Slope change", -200, 200, 0, step=10)
        curvature = st.slider("Curvature / belly shock", -150, 150, 0, step=10)
    scenario_curve = apply_curve_scenario(base_curve, parallel, slope, curvature, ["Government Yield"])
    chart = base_curve.rename(columns={"Government Yield": "Base Curve"}).merge(
        scenario_curve.rename(columns={"Government Yield": "Scenario Curve"}), on="Maturity"
    )
    with right:
        stats = curve_statistics(scenario_curve, "Government Yield")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("2Y", pct(stats["2Y"]))
        c2.metric("10Y", pct(stats["10Y"]))
        c3.metric("10Y-2Y", bps_from_decimal(stats["10Y-2Y"]))
        c4.metric("30Y-3M", bps_from_decimal(stats["30Y-3M"]))

    plot_line(chart, "Maturity", ["Base Curve", "Scenario Curve"], "Government yield curve scenario")

    fwds = implied_forward_rates(scenario_curve, "Government Yield")
    st.subheader("Implied forward rates")
    plot_line(fwds, "Maturity", ["Zero Yield", "Implied Forward Rate"], "Zero yields vs implied forward rates")
    st.dataframe(
        fwds.style.format({"Maturity": "{:.2f}", "Zero Yield": "{:.2%}", "Implied Forward Rate": "{:.2%}"}),
        width="stretch",
    )

elif page == "Credit Spread Monitor":
    st.subheader("Credit spread analytics")
    rating = st.selectbox("Corporate rating curve", ["AAA", "AA", "A", "BBB", "BB", "B"], index=3)
    curve = corporate_curve(rating)
    spread_table = credit_spread_table()

    c1, c2 = st.columns([1.1, 0.9])
    with c1:
        plot_line(curve, "Maturity", ["Government Yield", "Corporate Yield"], f"Government vs {rating} corporate yield curve")
    with c2:
        plot_bar(curve, "Maturity", "Credit Spread bps", f"{rating} credit spread term structure")

    stats_g = curve_statistics(curve, "Government Yield")
    stats_c = curve_statistics(curve, "Corporate Yield")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("10Y Gov", pct(stats_g["10Y"]))
    k2.metric("10Y Corp", pct(stats_c["10Y"]))
    k3.metric("10Y Spread", bps_from_decimal(stats_c["10Y"] - stats_g["10Y"]))
    k4.metric("Curve Rating", rating)

    st.subheader("Spread curves by rating")
    long_spreads = spread_table.melt(id_vars="Maturity", var_name="Rating", value_name="Spread bps")
    if px is not None:
        fig = px.line(long_spreads, x="Maturity", y="Spread bps", color="Rating", markers=True, title="Credit spread curves")
        fig.update_layout(margin=dict(l=10, r=10, t=48, b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    else:
        st.line_chart(spread_table.set_index("Maturity"), width="stretch")

    st.dataframe(curve.style.format({"Government Yield": "{:.2%}", "Corporate Yield": "{:.2%}", "Credit Spread bps": "{:,.0f}"}), width="stretch")

elif page == "Portfolio Risk Workbench":
    st.subheader("Portfolio risk workbench")
    st.markdown("Edit the sample portfolio directly or upload a CSV from the sidebar. Required fields: Name, Issuer Type, Rating, Face Value, Coupon Rate, Maturity, Yield, Frequency.")
    portfolio_raw = load_portfolio_from_sidebar()
    edited = st.data_editor(portfolio_raw, num_rows="dynamic", width="stretch", height=310)

    try:
        enriched = enrich_portfolio(edited)
        summary = portfolio_summary(edited)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Market Value", money(summary["Market Value"]))
        c2.metric("Weighted Yield", pct(summary["Weighted Yield"]))
        c3.metric("Duration", f"{summary['Weighted Duration']:.2f}")
        c4.metric("DV01", money2(summary["Portfolio DV01"]))
        c5.metric("High Yield Weight", pct(summary["High Yield Weight"]))

        tabs = st.tabs(["Holdings", "Exposures", "Scenarios", "Export"])
        with tabs[0]:
            st.dataframe(
                enriched.style.format({"Coupon Rate": "{:.2%}", "Yield": "{:.2%}", "Price per 100": "{:.2f}", "Market Value": "{:,.0f}", "Weight": "{:.2%}", "Modified Duration": "{:.2f}", "Convexity": "{:.2f}", "DV01": "{:,.2f}", "Credit Spread bps": "{:,.0f}"}),
                width="stretch",
                height=420,
            )
        with tabs[1]:
            group = st.selectbox("Exposure breakdown", ["Issuer Type", "Rating", "Sector", "Country"], index=1)
            exp = exposure_table(edited, group)
            a, b = st.columns(2)
            with a:
                plot_bar(exp, group, "Market_Value", f"Market value by {group}")
            with b:
                plot_bar(exp, group, "DV01", f"DV01 by {group}")
            st.dataframe(exp.style.format({"Market_Value": "{:,.0f}", "Weight": "{:.2%}", "DV01": "{:,.2f}", "Duration_Contribution": "{:.2f}", "Average_Yield": "{:.2%}"}), width="stretch")
        with tabs[2]:
            shocks = st.multiselect("Parallel rate shocks in bps", [-300, -200, -100, -50, 0, 50, 100, 150, 200, 300, 500], default=[-100, -50, 0, 50, 100, 200])
            scen = portfolio_rate_scenarios(edited, shocks)
            plot_line(scen, "Shock bps", ["P&L"], "Portfolio P&L under parallel rate shocks")
            st.dataframe(scen.style.format({"Portfolio Value": "{:,.0f}", "P&L": "{:,.0f}", "Return": "{:.2%}"}), width="stretch")
        with tabs[3]:
            scen = portfolio_rate_scenarios(edited, [-200, -100, -50, 0, 50, 100, 200, 300])
            exp_rating = exposure_table(edited, "Rating")
            exp_sector = exposure_table(edited, "Sector")
            export_buttons({"Holdings": enriched, "Rate Scenarios": scen, "Rating Exposure": exp_rating, "Sector Exposure": exp_sector}, "fixed_income_portfolio_report")
    except Exception as exc:
        st.error(f"The portfolio could not be analyzed: {exc}")

elif page == "Stress Testing Matrix":
    st.subheader("Rates + spread stress testing")
    portfolio_raw = load_portfolio_from_sidebar()
    enriched = enrich_portfolio(portfolio_raw)
    st.markdown("This matrix applies a government-rate shock to all bonds and an additional spread shock only to corporate bonds.")

    rate_shocks = st.multiselect("Rate shocks bps", [-300, -200, -100, -50, 0, 50, 100, 150, 200, 300], default=[-100, 0, 50, 100, 200])
    spread_shocks = st.multiselect("Corporate spread shocks bps", [-200, -100, -50, 0, 50, 100, 200, 400], default=[-100, 0, 50, 100, 200])
    stress = portfolio_two_factor_stress(portfolio_raw, rate_shocks, spread_shocks)
    matrix = stress.pivot(index="Spread Shock bps", columns="Rate Shock bps", values="P&L")

    if px is not None:
        fig = px.imshow(matrix, text_auto=".0f", aspect="auto", title="Portfolio P&L heatmap")
        fig.update_layout(margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        st.dataframe(matrix, width="stretch")

    worst = stress.sort_values("P&L").iloc[0]
    best = stress.sort_values("P&L", ascending=False).iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Worst P&L", money(worst["P&L"]))
    c2.metric("Worst Return", pct(worst["Return"]))
    c3.metric("Best P&L", money(best["P&L"]))
    c4.metric("Best Return", pct(best["Return"]))

    st.dataframe(stress.style.format({"Portfolio Value": "{:,.0f}", "P&L": "{:,.0f}", "Return": "{:.2%}"}), width="stretch", height=340)
    export_buttons({"Stress Matrix": stress, "Holdings": enriched}, "fixed_income_stress_test")
