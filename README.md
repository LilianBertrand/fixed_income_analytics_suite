# Fixed Income Analytics Suite

A professional Streamlit dashboard for fixed-income analytics: bond pricing, duration, convexity, DV01, yield curves, credit spreads, portfolio attribution and stress testing.

This project is designed as a clean finance-oriented GitHub project for students interested in market finance, risk management, asset management, and fixed income.

## Features

### Executive Dashboard

- Portfolio market value
- Weighted yield
- Weighted modified duration
- Portfolio DV01
- Average credit spread
- Rating exposure
- Duration contribution by instrument
- DV01 contribution by instrument
- Parallel rate-shock P&L scenarios

### Bond Pricing Lab

- Fixed-rate bond pricing from discounted cash flows
- Price per 100
- Yield-to-maturity solver
- Macaulay duration
- Modified duration
- Convexity
- DV01
- Exact P&L under rate shocks
- Duration-only approximation
- Duration + convexity approximation
- Two-factor stress test: rate shock + spread shock

### Yield Curve Studio

- Synthetic government yield curve
- Parallel shifts
- Slope changes
- Curvature / belly shocks
- 2Y, 10Y, 30Y curve metrics
- 10Y-2Y and 30Y-3M slopes
- Implied forward rate calculation

### Credit Spread Monitor

- Corporate spread curves by rating
- AAA, AA, A, BBB, BB, B curves
- Government vs corporate yield comparison
- Credit spread term structure
- 10Y credit spread monitor

### Portfolio Risk Workbench

- Editable bond portfolio
- CSV upload
- Bond-level pricing and risk metrics
- Exposure by issuer type, rating, sector or country
- Market value attribution
- DV01 attribution
- Rate shock scenarios
- CSV and Excel export

### Stress Testing Matrix

- Rate shocks applied to all bonds
- Corporate spread shocks applied only to corporate bonds
- Portfolio P&L heatmap
- Worst-case and best-case scenario summary
- Exportable stress-test report

## Why this project is relevant

Most student finance dashboards focus on equities or generic portfolio charts. This project focuses on fixed income, where the analytics are more technical and closer to work done in asset management, risk management and market finance.

It demonstrates the ability to translate financial concepts into Python code:

- discounted cash-flow pricing;
- yield-to-maturity solving;
- duration and convexity risk;
- DV01 as a money-risk measure;
- rate and spread stress testing;
- portfolio risk attribution.

## Project Structure

```text
fixed_income_analytics_suite_pro_v2/
├── app.py
├── analytics/
│   ├── bonds.py
│   ├── curves.py
│   └── portfolio.py
├── data/
│   └── sample_bond_portfolio.csv
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

```bash
pip3 install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

## CSV Portfolio Format

You can upload your own bond portfolio with the following required columns:

```text
Name, Issuer Type, Rating, Face Value, Coupon Rate, Maturity, Yield, Frequency
```

Recommended optional columns:

```text
Country, Sector, Credit Spread bps
```

Example:

```csv
Name,Issuer Type,Country,Sector,Rating,Face Value,Coupon Rate,Maturity,Yield,Frequency,Credit Spread bps
French OAT 2029,Government,France,Sovereign,AA,1200000,0.03,3.2,0.032,1,0
Bank Senior Preferred,Corporate,France,Financials,A,700000,0.052,5,0.058,2,140
```

## Main Financial Concepts

### Bond Price

The bond price is the present value of future coupons and principal repayment.

### Modified Duration

Modified duration estimates the percentage price change of a bond for a small change in yield.

### Convexity

Convexity captures the curvature of the bond price/yield relationship and improves the accuracy of larger rate-shock approximations.

### DV01

DV01 measures the change in bond price for a one basis point move in yield.

### Credit Spread

Credit spread represents the additional yield demanded by investors for holding a corporate bond instead of a government bond of similar maturity.

## Disclaimer

The default data is synthetic and used for educational purposes only. This application is not investment advice and should not be used for real trading or portfolio decisions without independent validation.
