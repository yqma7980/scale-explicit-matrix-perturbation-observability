import math

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

from render_publication import COLORS, panel_label, read_csv, save_figure, style_axis


FAMILY_STYLES = {
    'SPD': (COLORS['blue'], 'o', 'SPD'),
    'NONSYMMETRIC': (COLORS['teal'], 's', 'Nonsymmetric'),
    'SADDLE_POINT_LIKE': (COLORS['amber'], '^', 'Saddle-point-like'),
}


def render() -> None:
    rows = read_csv('Paper2_route_error_per_case.csv')
    fig, axes = plt.subplots(2, 2, figsize=(190 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=0.085, right=0.935, top=0.89, bottom=0.12,
                        hspace=0.50, wspace=0.42)
    for label, ax in zip('abcd', axes.flat):
        panel_label(ax, label, x=-0.13, y=1.04)

    ax = axes[0, 0]
    positive = [row for row in rows if float(row['error_response']) > 0.0]
    for family, (color, marker, label) in FAMILY_STYLES.items():
        selected = [row for row in positive if row['family'] == family]
        ax.scatter(
            [float(row['error_direct']) for row in selected],
            [float(row['error_response']) for row in selected],
            s=20, alpha=0.72, color=color, marker=marker,
            edgecolors='none', label=label,
        )
    limits = [1e-32, 1e-10]
    ax.plot(limits, limits, color=COLORS['coral'], linestyle='--',
            linewidth=1.1, label='Equal error')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(limits)
    ax.set_ylim(limits)
    ax.set_xlabel('Direct-difference error')
    ax.set_ylabel('Response-equation error')
    style_axis(ax)
    ax.legend(loc='upper left', ncol=2, columnspacing=0.8,
              handletextpad=0.4)

    ax = axes[0, 1]
    conditions = sorted({int(row['condition_exponent']) for row in rows})
    epsilons = sorted({float(row['epsilon']) for row in rows})
    grid = np.full((len(conditions), len(epsilons)), np.nan)
    for i, condition in enumerate(conditions):
        for j, epsilon in enumerate(epsilons):
            values = [
                float(row['log10_ratio']) for row in rows
                if int(row['condition_exponent']) == condition
                and float(row['epsilon']) == epsilon
                and row['ratio_status'] == 'FINITE_POSITIVE'
            ]
            if values:
                grid[i, j] = float(np.median(values))
    cmap = LinearSegmentedColormap.from_list(
        'route_difference', [COLORS['mint'], COLORS['white'], COLORS['coral_light']],
    )
    norm = TwoSlopeNorm(vmin=-15.0, vcenter=0.0, vmax=1.0)
    image = ax.imshow(grid, origin='lower', aspect='auto', cmap=cmap, norm=norm)
    ax.set_xticks(np.arange(len(epsilons)),
                  [f'{math.log10(value):.0f}' for value in epsilons])
    ax.set_yticks(np.arange(len(conditions)), [str(value) for value in conditions])
    ax.set_xlabel('Perturbation exponent log10(ε)')
    ax.set_ylabel('Condition exponent')
    for i in range(len(conditions)):
        for j in range(len(epsilons)):
            if np.isfinite(grid[i, j]):
                ax.text(j, i, f'{grid[i, j]:.1f}', ha='center', va='center',
                        fontsize=7.5, color=COLORS['black'])
    colorbar = fig.colorbar(image, ax=ax, fraction=0.040, pad=0.025)
    colorbar.set_label('Median log10(error ratio)')
    colorbar.ax.tick_params(labelsize=7.6)

    ax = axes[1, 0]
    dimensions = sorted({int(row['dimension']) for row in rows})
    for family, (color, marker, label) in FAMILY_STYLES.items():
        median, low, high = [], [], []
        for dimension in dimensions:
            values = np.asarray([
                float(row['log10_ratio']) for row in rows
                if row['family'] == family and int(row['dimension']) == dimension
                and row['ratio_status'] == 'FINITE_POSITIVE'
            ])
            median.append(float(np.quantile(values, 0.50)))
            low.append(float(np.quantile(values, 0.25)))
            high.append(float(np.quantile(values, 0.75)))
        ax.plot(dimensions, median, color=color, marker=marker,
                markersize=4.5, label=label)
        ax.fill_between(dimensions, low, high, color=color, alpha=0.13)
    ax.axhline(0.0, color=COLORS['coral'], linestyle='--', linewidth=1.0)
    ax.set_xscale('log', base=2)
    ax.set_xticks(dimensions, [str(value) for value in dimensions])
    ax.set_xlabel('System dimension')
    ax.set_ylabel(r'$\log_{10}(e_{\mathrm{response}}/e_{\mathrm{direct}})$')
    style_axis(ax)
    ax.legend(loc='upper left')

    ax = axes[1, 1]
    x = np.arange(len(conditions), dtype=float)
    fractions, direct_counts = [], []
    for condition in conditions:
        selected = [row for row in rows if int(row['condition_exponent']) == condition]
        fractions.append(
            sum(row['winner'] == 'RESPONSE_EQUATION' for row in selected) / len(selected)
        )
        direct_counts.append(sum(row['winner'] == 'DIRECT_DIFFERENCE' for row in selected))
    bars = ax.bar(x, fractions, width=0.62, color=COLORS['mint'],
                  edgecolor=COLORS['teal'], linewidth=1.0)
    ax.set_ylim(0.88, 1.012)
    ax.set_xticks(x, [str(value) for value in conditions])
    ax.set_xlabel('Condition exponent')
    ax.set_ylabel('Response-equation lower-error fraction')
    style_axis(ax, grid='y')
    for bar, fraction, count in zip(bars, fractions, direct_counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, fraction - 0.010,
            f'{fraction:.2f}\nD={count}', ha='center', va='top',
            fontsize=7.7, color=COLORS['deep'], fontweight='bold',
        )

    fig.suptitle(
        'Arithmetic-route differences across the archived 300-case grid',
        fontsize=10.3, fontweight='bold',
    )
    save_figure(fig, 'F7_route_error_mechanism')


if __name__ == '__main__':
    render()
