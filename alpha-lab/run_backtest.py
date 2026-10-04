"""Run the full pipeline:  python run_backtest.py --start 2012-01-01
Offline smoke test:       python run_backtest.py --synthetic
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from alphalab import metrics, report
from alphalab.backtest import select_windows, simulate
from alphalab.data import BENCHMARK, SECTORS, all_tickers, load_prices, simulate_prices
from alphalab.pairs import statsmodels_pvalue
from alphalab.strategy import Params


def main(argv=None, pvalue_fn=statsmodels_pvalue) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2012-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--synthetic", action="store_true", help="use simulated data (no download)")
    ap.add_argument("--out", default="results")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    p = Params()
    if args.synthetic:
        prices, sectors = simulate_prices(n_days=2000, seed=1)
        bench, period = None, "synthetic data"
    else:
        sectors = SECTORS
        data = load_prices(all_tickers() + [BENCHMARK], args.start, args.end)
        bench = data[BENCHMARK].pct_change().dropna()
        prices = data.drop(columns=[BENCHMARK])
        period = f"{prices.index[0].date()} to {prices.index[-1].date()}"

    print("Selecting pairs for each walk-forward window (the slow step)...")
    windows = select_windows(prices, sectors, p, pvalue_fn, verbose=True)

    res = simulate(prices, windows, p)
    b = bench.reindex(res.net.index).dropna() if bench is not None else None
    net_s = metrics.summarize(res.net, b)
    gross_s = metrics.summarize(res.gross)
    bench_s = metrics.summarize(b) if b is not None else None

    # Sensitivity: how fragile is the result? Reuses the cached pair selection.
    entries, costs = [1.5, 2.0, 2.5], [0, 5, 10, 20]
    grid = pd.DataFrame({c: [metrics.sharpe(simulate(prices, windows, replace(p, entry_z=e, cost_bps=c)).net)
                             for e in entries] for c in costs}, index=entries)

    report.plot_equity(res.net, res.gross, b, out / "equity_curve.png")
    report.plot_heatmap(grid, out / "sensitivity.png")
    avg_pairs = sum(len(w.pairs) for w in windows) / max(len(windows), 1)
    report.write_markdown(net_s, gross_s, bench_s, len(windows), avg_pairs, period, out / "RESULTS.md")
    res.pair_log.to_csv(out / "pair_log.csv", index=False)
    (out / "summary.json").write_text(json.dumps({"net": net_s, "gross": gross_s, "benchmark": bench_s,
                                                  "params": p.__dict__}, indent=2, default=float))
    print((out / "RESULTS.md").read_text())
    print("Net Sharpe grid (rows: entry z, cols: cost bps)\n", grid.round(2))


if __name__ == "__main__":
    main()
