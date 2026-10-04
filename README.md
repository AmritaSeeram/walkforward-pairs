# walkforward-pairs

A research-grade equity pairs trading framework built around honest walk-forward evaluation,
realistic transaction costs, and statistical discipline.

The purpose of this project is not to produce a flashy backtest number. It is to implement a
methodology that stays robust to look-ahead bias, multiple-testing error, and over-optimistic
execution assumptions.

## Overview

This project:

- finds cointegrated stock pairs using a walk-forward setup
- trades the spread with a mean-reversion signal
- enforces out-of-sample evaluation only
- accounts for trading frictions and borrow costs
- reports uncertainty around key performance metrics
- includes deterministic tests that do not rely on live market data

## Methodology

1. **Walk-forward windows**
   - Pairs are selected on a formation window and traded on the next evaluation window.
   - Every reported return is out-of-sample by design.

2. **Pair selection**
   - Restricts candidate pairs to within-sector names.
   - Uses Engle-Granger cointegration testing in both directions.
   - Applies Benjamini-Hochberg FDR control across the candidate set.
   - Filters by spread half-life to keep the signal economically sensible.

3. **Trading signal**
   - Forms the spread as `log(y) - beta * log(x)`.
   - Standardizes the spread using the formation-window mean and standard deviation.
   - Enters on `|z| >= 2`, exits on `|z| <= 0.5`, and stops out on `|z| >= 4`.

4. **Execution**
   - Trades at the next close (`exec_lag=1`).
   - Uses dollar-neutral positions.
   - Includes cost assumptions for per-side spread, short borrow, and forced flattening of positions.

5. **Evaluation**
   - Reports Sharpe ratio with block-bootstrap confidence intervals.
   - Computes the Probabilistic Sharpe Ratio.
   - Regresses returns against SPY to assess market neutrality.
   - Sweeps entry thresholds and cost assumptions to show sensitivity.

## Project structure

```text
.
├── README.md
├── requirements.txt
├── pytest.ini
├── run_backtest.py
├── conftest.py
├── alphalab/
│   ├── __init__.py
│   ├── backtest.py
│   ├── data.py
│   ├── metrics.py
│   ├── pairs.py
│   ├── report.py
│   ├── strategy.py
│   └── ...
├── tests/
│   ├── helpers.py
│   └── test_core.py
└── results/
    └── generated after running the backtest
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick start

```bash
pytest
python run_backtest.py --synthetic
python run_backtest.py --start 2012-01-01
```

The real backtest downloads price data from Yahoo Finance and writes result artifacts such as:

- `results/RESULTS.md`
- `equity_curve.png`
- `sensitivity.png`
- `pair_log.csv`
- `summary.json`

## What the tests validate

- no look-ahead leakage in the evaluation pipeline
- recovery of planted cointegrated pairs in simulated data
- half-life estimation behavior in a known AR(1) structure
- FDR behavior against textbook examples
- cost sensitivity that does not reward unrealistic assumptions

## Important limitations

- Survivorship bias is present because the universe is based on current large-cap names.
- The model uses adjusted close prices and a simplified cost framework.
- Regime shifts inside the trading window are only partially visible via stop-loss logic.
- Statistical arbitrage is heavily competed away, so weak or negative results are not uncommon.

## License

This project is provided for research and educational use.

## Results

Run the project to generate the latest evaluation artifacts in the `results/` folder.
