from decimal import Decimal, localcontext
import math

import matplotlib.pyplot as plt
import numpy as np

from render_publication import COLORS, panel_label, read_csv, save_figure, style_axis


GROUPS = [
    ('DEVELOPMENT', 'DECIMAL_SOURCE', COLORS['deep'], 'o', 'Dev source'),
    ('DEVELOPMENT', 'BINARY64_OPERAND', COLORS['teal'], 's', 'Dev binary'),
    ('HOLDOUT_G2_20', 'DECIMAL_SOURCE', COLORS['blue'], '^', 'Holdout source'),
    ('HOLDOUT_G2_20', 'BINARY64_OPERAND', COLORS['amber'], 'D', 'Holdout binary'),
]


def log10_decimal(text: str) -> float:
    value = Decimal(text)
    if value <= 0:
        return math.nan
    with localcontext() as context:
        context.prec = 80
        return float(value.log10())


def percentile(values, q):
    return float(np.quantile(np.asarray(values, dtype=float), q))


def render() -> None:
    rows = read_csv('Paper2_response_route_per_case.csv')
    fig, axes = plt.subplots(2, 2, figsize=(190 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=0.085, right=0.98, top=0.89, bottom=0.12,
                        hspace=0.50, wspace=0.35)
    for label, ax in zip('abcd', axes.flat):
        panel_label(ax, label, x=-0.13, y=1.04)

    ax = axes[0, 0]
    all_logs = []
    for dataset, lane, color, marker, label in GROUPS:
        selected = [r for r in rows if r['dataset'] == dataset and r['lane'] == lane]
        x = [log10_decimal(r['error_direct']) for r in selected]
        y = [log10_decimal(r['error_response']) for r in selected]
        pairs = [(a, b) for a, b in zip(x, y) if math.isfinite(a) and math.isfinite(b)]
        if pairs:
            xp, yp = zip(*pairs)
            all_logs.extend(xp)
            all_logs.extend(yp)
            ax.scatter(xp, yp, s=10, alpha=0.38, color=color, marker=marker,
                       edgecolors='none', label=label)
    low, high = percentile(all_logs, 0.01), percentile(all_logs, 0.99)
    ax.plot([low, high], [low, high], color=COLORS['coral'],
            linestyle='--', linewidth=1.1)
    ax.set_xlim(low, high)
    ax.set_ylim(low, high)
    ax.set_xlabel(r'$\log_{10}$ direct-route error')
    ax.set_ylabel(r'$\log_{10}$ response-route error')
    style_axis(ax)
    ax.legend(loc='upper left', ncol=2, columnspacing=0.7)

    ax = axes[0, 1]
    for dataset, lane, color, _, label in GROUPS:
        selected = [r for r in rows if r['dataset'] == dataset and r['lane'] == lane]
        values = sorted(log10_decimal(r['response_to_direct_bound_ratio'])
                        for r in selected
                        if math.isfinite(log10_decimal(r['response_to_direct_bound_ratio'])))
        y = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, y, color=color, label=label)
    ax.axvline(0, color=COLORS['coral'], linestyle='--', linewidth=1.0)
    ax.set_xlabel(r'$\log_{10}(U_{\rm r}/U_{\rm d})$')
    ax.set_ylabel('Empirical cumulative fraction')
    style_axis(ax)

    ax = axes[1, 0]
    x = np.arange(4)
    lower_error = []
    lower_bound = []
    labels = []
    for dataset, lane, _, _, label in GROUPS:
        selected = [r for r in rows if r['dataset'] == dataset and r['lane'] == lane]
        lower_error.append(sum(Decimal(r['error_response']) < Decimal(r['error_direct'])
                               for r in selected) / len(selected))
        lower_bound.append(sum(Decimal(r['U_response']) < Decimal(r['U_direct'])
                               for r in selected) / len(selected))
        labels.append(label)
    width = 0.34
    ax.bar(x - width / 2, lower_error, width, color=COLORS['blue'],
           edgecolor=COLORS['deep'], label='Lower error')
    ax.bar(x + width / 2, lower_bound, width, color=COLORS['mint'],
           edgecolor=COLORS['teal'], label='Lower enclosure')
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x, labels, rotation=18, ha='right')
    ax.set_ylabel('Fraction of 300 cases')
    style_axis(ax, grid='y')
    ax.legend(loc='lower left')

    ax = axes[1, 1]
    error_median = []
    bound_median = []
    for dataset, lane, _, _, _ in GROUPS:
        selected = [r for r in rows if r['dataset'] == dataset and r['lane'] == lane]
        error_median.append(np.median([
            log10_decimal(r['response_to_direct_error_ratio']) for r in selected
        ]))
        bound_median.append(np.median([
            log10_decimal(r['response_to_direct_bound_ratio']) for r in selected
        ]))
    ax.bar(x - width / 2, error_median, width, color=COLORS['blue'],
           edgecolor=COLORS['deep'], label='Error ratio')
    ax.bar(x + width / 2, bound_median, width, color=COLORS['amber'],
           edgecolor=COLORS['amber'], label='Enclosure ratio')
    ax.axhline(0, color=COLORS['coral'], linestyle='--', linewidth=1.0)
    ax.set_xticks(x, labels, rotation=18, ha='right')
    ax.set_ylabel('Median log10(response/direct)')
    style_axis(ax, grid='y')
    ax.legend(loc='lower right')

    fig.suptitle(
        'Both operation graphs retain coverage while their errors and enclosures differ',
        fontsize=10.3, fontweight='bold',
    )
    save_figure(fig, 'F7_route_error_mechanism')


if __name__ == '__main__':
    render()
