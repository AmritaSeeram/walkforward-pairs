# walkforward-pairs: walk-forward pairs trading with honest evaluation

A research framework that finds statistically related US stocks, trades their mean-reverting
spread, and evaluates the result the way a quant researcher would: out-of-sample only,
with realistic costs, and with uncertainty on every headline number.

The point of the project is not a big backtest number. It is the methodology: every step is
designed so the result cannot be flattered by look-ahead bias, multiple-testing luck, or free trading.

## How it works

1. **Walk-forward windows.** Pairs are selected on 252 days of history, then traded on the *next* 63
days, then everything is re-selected. Every reported return is out-of-sample.
2. **Pair selection.** Within-sector pairs only. Engle-Granger cointegration test in both directions
   (p-value doubled for the direction choice), then **Benjamini-Hochberg false-discovery-rate control**
   across all pairs tested in the window, then a half-life filter on the spread (2 to 40 days).
3. **Signal.** The spread `log(y) - beta * log(x)` is z-scored with the *formation-window* mean and
   std. Enter at |z| >= 2, exit at |z| <= 0.5, stop out at |z| >= 4 and stay flat until the
   spread re-enters the exit band.
4. **Execution.** A signal at close *t* is traded at the next close (`exec_lag=1`). Positions are
   dollar-neutral. Costs: 5 bps per side, 50 bps annualised borrow on the short leg, forced
   flatten at the end of each window.
5. **Evaluation.** Sharpe with a block-bootstrap confidence interval, Probabilistic Sharpe Ratio
   (adjusts for skew and fat tails), regression on SPY (is it really market-neutral?), and a
   sensitivity grid of net Sharpe against entry threshold and trading costs.

## Run it

```bash
pip install -r requirements.txt
pytest                                  # 9 tests, no network needed
python run_backtest.py --synthetic      # offline smoke test on simulated data
python run_backtest.py --start 2012-01-01
```

The real run downloads prices from Yahoo Finance and takes a few minutes, mostly the cointegration
tests. It writes `results/RESULTS.md`, `equity_curve.png`, `sensitivity.png`, `pair_log.csv` and
`summary.json`, all generated from the run.

## What the tests prove

- **No look-ahead:** randomly shocking all prices after a cut-off date leaves every return before
the cut-off byte-for-byte unchanged.
- Selection recovers planted cointegrated pairs and rejects unrelated random walks.
- Half-life estimator recovers a known AR(1); Benjamini-Hochberg matches a textbook example.
- Higher costs never increase profit; the strategy profits on planted cointegration before costs.

## Limitations (read these before trusting any number)

- **Survivorship bias:** the universe is today's large caps, which flatters historical results.
- Adjusted close prices only: no bid/ask spreads, market impact, or short-availability data. The
  cost model is an assumption, which is why the sensitivity grid sweeps it.
- Stats for each pair are fixed from the formation window; a regime change inside the trading
  window is only caught by the stop-loss.
- Statistical arbitrage on liquid US equities is heavily competed away. A weak or negative
  result is plausible and is reported as is.

## Results

See `results/RESULTS.md` after running.
