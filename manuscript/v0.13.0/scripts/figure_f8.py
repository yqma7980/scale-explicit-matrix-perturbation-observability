import matplotlib.pyplot as plt
import numpy as np

from render_publication import (
    COLORS, INPUTS, panel_label, read_json, save_figure, style_axis,
)


def sparsity(ax, matrix, case, color, marker_size) -> None:
    row, column = np.nonzero(matrix)
    ax.scatter(column, row, s=marker_size, color=color, marker='s', linewidths=0)
    dimension = matrix.shape[0]
    ticks = [0, dimension // 2, dimension - 1]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xlim(-1, dimension)
    ax.set_ylim(dimension, -1)
    ax.set_aspect('equal')
    ax.set_xlabel('column')
    ax.set_ylabel('row')
    ax.set_title(
        f'{case}: {dimension} DOFs, {len(row):,} nonzeros',
        fontweight='bold', pad=7,
    )


def interval_axis(ax, decisions, case, scale, xmax) -> None:
    ax.axvline(0.0, color=COLORS['coral'], linewidth=1.0, linestyle='--')
    routes = [
        ('Response equation', decisions['response_equation_route'],
         COLORS['teal'], 'D', 0),
        ('Direct difference', decisions['direct_route'],
         COLORS['amber'], 'o', 1),
    ]
    for label, lane, color, marker, y in routes:
        observed = float(lane['d_obs']) / scale
        lower = float(lane['interval_lower']) / scale
        upper = float(lane['interval_upper']) / scale
        left = observed - lower
        right = upper - observed
        ax.errorbar(
            observed, y, xerr=np.asarray([[left], [right]]),
            fmt=marker, markersize=6.5, color=color, ecolor=color,
            elinewidth=4.0, capsize=5.0, markeredgecolor=COLORS['white'],
            markeredgewidth=0.8, zorder=4,
        )
        d_value = float(lane['d_obs'])
        u_value = float(lane['U'])
        ax.annotate(
            rf'$d_{{\mathsf{{obs}}}}={d_value:.3e}$' + '\n'
            + rf'$U={u_value:.3e}$',
            xy=(observed, y), xycoords='data',
            xytext=(0.975, 0.90 if y == 1 else 0.10),
            textcoords='axes fraction',
            ha='right', va='center', fontsize=8.0, color=color,
            bbox={
                'boxstyle': 'round,pad=0.22',
                'facecolor': COLORS['white'],
                'edgecolor': color,
                'linewidth': 0.8,
                'alpha': 0.96,
            },
        )
    ax.set_yticks([0, 1], ['Response equation', 'Direct difference'])
    ax.set_xlim(-0.035 * xmax, xmax)
    ax.set_ylim(-0.55, 1.55)
    exponent = int(round(np.log10(scale)))
    ax.set_xlabel(rf'Response norm ($\times 10^{{{exponent}}}$)')
    ax.set_title(f'{case}: route-specific intervals', fontweight='bold', pad=7)
    style_axis(ax, grid='x')
    ax.tick_params(axis='y', length=0)
    ax.spines['left'].set_visible(False)
    ax.text(0.015, 0.96, r'$\tau=0$', transform=ax.transAxes,
            color=COLORS['coral'], fontsize=8.0, va='top')


def render() -> None:
    with np.load(INPUTS / 'M8_snapshot.npz') as archive:
        m8 = np.array(archive['jhat_phys'], copy=True)
    with np.load(INPUTS / 'M16_snapshot.npz') as archive:
        m16 = np.array(archive['jhat_phys'], copy=True)
    m8_decisions = read_json('M8_decisions.json')
    m16_decisions = read_json('M16_decisions.json')

    fig, axes = plt.subplots(
        2, 2, figsize=(190 / 25.4, 128 / 25.4),
        gridspec_kw={'width_ratios': [0.78, 1.32]},
    )
    fig.subplots_adjust(left=0.08, right=0.985, top=0.90, bottom=0.12,
                        wspace=0.30, hspace=0.54)
    for label, axis in zip('abcd', axes.flat):
        panel_label(axis, label, x=-0.22 if axis in axes[:, 0] else -0.08, y=1.06)

    sparsity(axes[0, 0], m8, 'M8', COLORS['teal'], 0.50)
    interval_axis(axes[0, 1], m8_decisions, 'M8', 1e-12, 4.30)
    sparsity(axes[1, 0], m16, 'M16', COLORS['deep'], 0.14)
    interval_axis(axes[1, 1], m16_decisions, 'M16', 1e-11, 3.60)
    fig.suptitle(
        'Route-specific response qualification for two archived finite-element tangents',
        fontsize=10.3, fontweight='bold',
    )
    save_figure(fig, 'F8_two_operator_route_qualification')


if __name__ == '__main__':
    render()
