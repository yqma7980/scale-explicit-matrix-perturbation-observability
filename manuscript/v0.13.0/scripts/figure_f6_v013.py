import math

import matplotlib.pyplot as plt
import numpy as np

from render_publication import COLORS, panel_label, read_csv, save_figure, style_axis


def finite(value: str) -> float:
    result = float(value)
    return result if math.isfinite(result) and result > 0 else math.nan


def render() -> None:
    anatomy = [r for r in read_csv('Paper2_effectivity_anatomy.csv') if r['status'] == 'FINITE']
    attribution = read_csv('Paper2_multivariable_attribution.csv')
    direct = [r for r in read_csv('Paper2_effectivity_per_case.csv')
              if r['I_eff_status'] == 'FINITE' and finite(r['I_eff']) > 0]

    fig, axes = plt.subplots(2, 2, figsize=(190 / 25.4, 132 / 25.4))
    fig.subplots_adjust(left=0.085, right=0.98, top=0.89, bottom=0.12,
                        hspace=0.48, wspace=0.34)
    for label, ax in zip('abcd', axes.flat):
        panel_label(ax, label, x=-0.13, y=1.04)

    ax = axes[0, 0]
    styles = [
        ('development', COLORS['deep'], 'o', 'Development'),
        ('holdout', COLORS['amber'], 's', 'Holdout'),
    ]
    for dataset, color, marker, label in styles:
        rows = [r for r in anatomy if r['dataset'] == dataset]
        ax.scatter(
            [math.log10(finite(r['norm_majorant_inflation'])) for r in rows],
            [math.log10(finite(r['directional_alignment_inflation'])) for r in rows],
            s=9, alpha=0.30, color=color, marker=marker, edgecolors='none',
            label=label,
        )
    ax.set_xlabel(r'$\log_{10}$ norm-majorant inflation')
    ax.set_ylabel(r'$\log_{10}$ directional inflation')
    style_axis(ax)
    ax.legend(loc='upper right')

    ax = axes[0, 1]
    groups = ['Development', 'Holdout']
    norm_med = []
    dir_med = []
    for dataset in ['development', 'holdout']:
        rows = [r for r in anatomy if r['dataset'] == dataset]
        norm_med.append(np.median([math.log10(finite(r['norm_majorant_inflation'])) for r in rows]))
        dir_med.append(np.median([math.log10(finite(r['directional_alignment_inflation'])) for r in rows]))
    x = np.arange(2)
    width = 0.34
    ax.bar(x - width / 2, norm_med, width, color=COLORS['blue'],
           edgecolor=COLORS['deep'], label='Norm majorant')
    ax.bar(x + width / 2, dir_med, width, color=COLORS['mint'],
           edgecolor=COLORS['teal'], label='Directional alignment')
    ax.set_xticks(x, groups)
    ax.set_ylabel('Median log10 inflation')
    ax.set_ylim(0, max(dir_med) + 0.7)
    style_axis(ax, grid='y')
    ax.legend(loc='upper right')

    ax = axes[1, 0]
    factors = ['condition_exponent', 'family', 'log10_epsilon',
               'log2_dimension', 'lane']
    labels = ['Condition', 'Family', r'$\log_{10}\epsilon$',
              r'$\log_2 n$', 'Ref. lane']
    y = np.arange(len(factors))
    width = 0.34
    for offset, model, color, label in [
        (-width / 2, 'development', COLORS['deep'], 'Development'),
        (width / 2, 'holdout', COLORS['amber'], 'Holdout'),
    ]:
        values = []
        for factor in factors:
            match = [r for r in attribution
                     if r['model'] == model and r['group'] == factor
                     and r['drop_one_partial_R2']]
            values.append(float(match[0]['drop_one_partial_R2']) if match else 0.0)
        ax.barh(y + offset, values, height=width, color=color, alpha=0.82,
                label=label)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel(r'Drop-one partial $R^2$')
    style_axis(ax, grid='x')
    ax.legend(loc='lower right')

    ax = axes[1, 1]
    data = []
    labels = []
    colors = []
    for dataset, lane, color, label in [
        ('development', 'decimal-source', COLORS['deep'], 'Dev source'),
        ('development', 'binary64-operand', COLORS['teal'], 'Dev binary'),
        ('holdout', 'decimal-source', COLORS['blue'], 'Holdout source'),
        ('holdout', 'binary64-operand', COLORS['amber'], 'Holdout binary'),
    ]:
        values = [math.log10(finite(r['I_eff'])) for r in direct
                  if r['dataset'] == dataset and r['lane'] == lane
                  and math.log10(finite(r['I_eff'])) < 20]
        data.append(values)
        labels.append(label)
        colors.append(color)
    artists = ax.boxplot(data, patch_artist=True, showfliers=False,
                         medianprops={'color': COLORS['black'], 'linewidth': 1.1})
    for patch, color in zip(artists['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.50)
        patch.set_edgecolor(color)
    ax.set_xticks(np.arange(1, 5), labels, rotation=18, ha='right')
    ax.set_ylabel(r'$\log_{10}$ effectivity')
    ax.text(
        0.98, 0.95,
        r'Maximum $\log_{10}$ effectivity $=86.90$'
        '\nnear-zero denominator; not drawn',
        transform=ax.transAxes, ha='right', va='top', fontsize=8.6,
        color=COLORS['coral'], fontweight='bold',
    )
    style_axis(ax, grid='y')

    fig.suptitle(
        'Conservativeness is dominated by realized-direction loss, not Frobenius majorization',
        fontsize=10.3, fontweight='bold',
    )
    save_figure(fig, 'F6_effectivity_dependence')


if __name__ == '__main__':
    render()
