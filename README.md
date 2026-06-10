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


## Live Demo

https://fixedincomeanalyticssuite-pruq7q69rh2rxajeyyopax.streamlit.app/
