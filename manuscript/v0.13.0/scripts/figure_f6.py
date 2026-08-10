import math

import matplotlib.pyplot as plt
import numpy as np

from render_publication import COLORS, panel_label, read_csv, save_figure, style_axis


STYLES = [
    ('development', 'decimal-source', COLORS['deep'], 'o', '-', 'Development source'),
    ('development', 'binary64-operand', COLORS['teal'], 's', '--', 'Development binary'),
    ('holdout', 'decimal-source', COLORS['blue'], '^', '-.', 'Holdout source'),
    ('holdout', 'binary64-operand', COLORS['amber'], 'D', ':', 'Holdout binary'),
]


def finite_rows(rows):
    return [
        row for row in rows
        if row['I_eff_status'] == 'FINITE' and float(row['I_eff']) > 0.0
    ]


def grouped_curve(rows, factor, transform):
    values = sorted({row[factor] for row in rows}, key=transform)
    x, median, low, high = [], [], [], []
    for value in values:
        sample = np.asarray([
            math.log10(float(row['I_eff'])) for row in rows if row[factor] == value
        ])
        x.append(transform(value))
        median.append(float(np.quantile(sample, 0.50)))
        low.append(float(np.quantile(sample, 0.25)))
        high.append(float(np.quantile(sample, 0.75)))
    return np.asarray(x), np.asarray(median), np.asarray(low), np.asarray(high)


def render() -> None:
    rows = finite_rows(read_csv('Paper2_effectivity_per_case.csv'))
    fig, axes = plt.subplots(2, 2, figsize=(190 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.89, bottom=0.12,
                        hspace=0.48, wspace=0.30)
    for label, ax in zip('abcd', axes.flat):
        panel_label(ax, label, x=-0.13, y=1.04)

    specifications = [
        ('condition_exponent', 'Condition exponent', lambda value: float(value)),
        ('epsilon', 'Perturbation exponent log10(ε)',
         lambda value: math.log10(float(value))),
        ('dimension', 'System dimension', lambda value: float(value)),
    ]
    for ax, (factor, xlabel, transform) in zip(axes.flat[:3], specifications):
        for dataset, lane, color, marker, linestyle, label in STYLES:
            selected = [
                row for row in rows
                if row['dataset'] == dataset and row['lane'] == lane
            ]
            x, median, low, high = grouped_curve(selected, factor, transform)
            ax.plot(x, median, color=color, marker=marker, linestyle=linestyle,
                    markersize=4.2, label=label)
            ax.fill_between(x, low, high, color=color, alpha=0.12, linewidth=0)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r'$\log_{10}(I_{\mathrm{eff}})$')
        style_axis(ax)
    axes[0, 0].legend(loc='upper left', ncol=2, columnspacing=0.9,
                      handlelength=2.0, handletextpad=0.45)

    ax = axes[1, 1]
    families = ['SPD', 'NONSYMMETRIC', 'SADDLE_POINT_LIKE']
    family_labels = ['SPD', 'Nonsymmetric', 'Saddle-point\nlike']
    positions = np.arange(len(families), dtype=float)
    offsets = [-0.27, -0.09, 0.09, 0.27]
    for offset, (dataset, lane, color, _, _, label) in zip(offsets, STYLES):
        data = [
            [math.log10(float(row['I_eff'])) for row in rows
             if row['dataset'] == dataset and row['lane'] == lane
             and row['family'] == family]
            for family in families
        ]
        artists = ax.boxplot(
            data, positions=positions + offset, widths=0.15,
            patch_artist=True, showfliers=False,
            medianprops={'color': COLORS['black'], 'linewidth': 0.9},
        )
        for patch in artists['boxes']:
            patch.set_facecolor(color)
            patch.set_alpha(0.38)
            patch.set_edgecolor(color)
        for item in artists['whiskers'] + artists['caps']:
            item.set_color(color)
        ax.plot([], [], color=color, linewidth=6, alpha=0.38, label=label)
    ax.set_xticks(positions, family_labels)
    ax.set_xlabel('Matrix family')
    ax.set_ylabel(r'$\log_{10}(I_{\mathrm{eff}})$')
    style_axis(ax, grid='y')
    ax.legend(loc='upper left', ncol=2, columnspacing=0.8,
              handlelength=1.3, handletextpad=0.4)

    fig.suptitle(
        'Archived uncertainty-bound effectivity depends most strongly on conditioning',
        fontsize=10.3, fontweight='bold',
    )
    save_figure(fig, 'F6_effectivity_dependence')


if __name__ == '__main__':
    render()
