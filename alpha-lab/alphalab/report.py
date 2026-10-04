"""Charts and a markdown results table, generated from the actual run (never hand-edited)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .metrics import equity_curve  # noqa: E402


def plot_equity(net, gross, bench, path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(equity_curve(gross), label="Strategy, before costs", alpha=0.6)
    ax1.plot(equity_curve(net), label="Strategy, after costs", lw=2)
    if bench is not None:
        ax1.plot(equity_curve(bench.reindex(net.index).fillna(0.0)), label="SPY buy & hold", alpha=0.7)
    ax1.set_ylabel("Growth of $1")
    ax1.set_title("Walk-forward pairs trading (out-of-sample only)")
    ax1.legend()
    eq = equity_curve(net)
    ax2.fill_between(eq.index, eq / eq.cummax() - 1.0, 0, color="tab:red", alpha=0.4)
    ax2.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_heatmap(grid: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    im = ax.imshow(grid.values, cmap="RdYlGn", aspect="auto", vmin=-1.5, vmax=1.5)
    ax.set_xticks(range(grid.shape[1]), [str(c) for c in grid.columns])
    ax.set_yticks(range(grid.shape[0]), [str(i) for i in grid.index])
    ax.set_xlabel("Cost per side (bps)")
    ax.set_ylabel("Entry z-score")
    ax.set_title("Net Sharpe vs entry threshold and trading costs")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, f"{grid.values[i, j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, label="Net Sharpe")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_markdown(net_stats: dict, gross_stats: dict, bench_stats: dict | None, n_windows: int,
                   avg_pairs: float, period: str, path: Path) -> None:
    def row(name, s):
        lo, hi = s["sharpe_ci95"]
        return (f"| {name} | {s['cagr']:.1%} | {s['vol']:.1%} | {s['sharpe']:.2f} | "
                f"[{lo:.2f}, {hi:.2f}] | {s['max_drawdown']:.1%} |")

    lines = [f"# Results ({period})", "",
             f"{n_windows} walk-forward windows, {avg_pairs:.1f} pairs traded per window on average.", "",
             "| Series | CAGR | Vol | Sharpe | 95% CI (block bootstrap) | Max drawdown |",
             "|---|---|---|---|---|---|",
             row("Strategy, before costs", gross_stats), row("Strategy, after costs", net_stats)]
    if bench_stats:
        lines.append(row("SPY buy & hold", bench_stats))
    vm = net_stats.get("vs_market")
    if vm:
        lines += ["", f"Market regression (net returns on SPY): beta = {vm['beta']:.2f}, "
                      f"annualised alpha = {vm['alpha_annual']:.1%} (t = {vm['alpha_tstat']:.2f}), "
                      f"R² = {vm['r_squared']:.2f}."]
    lines += ["", f"Probability the true net Sharpe is above 0 (PSR): {net_stats['prob_sharpe_gt_0']:.1%}."]
    path.write_text("\n".join(lines) + "\n")
