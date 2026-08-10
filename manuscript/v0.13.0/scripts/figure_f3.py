import matplotlib.pyplot as plt
import numpy as np

from render_publication import COLORS, arrow, panel_label, read_csv, save_figure, style_axis


def render() -> None:
    rows = read_csv('P2_counterexample.csv')
    aligned = sorted(
        (row for row in rows if row['lane_id'] == 'A_ALIGNED'),
        key=lambda row: float(row['epsilon']),
    )
    orthogonal = sorted(
        (row for row in rows if row['lane_id'] == 'B_ORTHOGONAL'),
        key=lambda row: float(row['epsilon']),
    )
    epsilon = np.asarray([float(row['epsilon']) for row in aligned])
    if any(float(row['eta_z']) != 0.0 for row in orthogonal):
        raise ValueError('registered orthogonal responses must remain exactly zero')

    fig = plt.figure(figsize=(190 / 25.4, 104 / 25.4))
    outer = fig.add_gridspec(1, 3, width_ratios=[0.95, 1.03, 1.10])
    ax = fig.add_subplot(outer[0, 0])
    bx = fig.add_subplot(outer[0, 1])
    right = outer[0, 2].subgridspec(2, 1, height_ratios=[4.0, 0.95], hspace=0.13)
    cx = fig.add_subplot(right[0, 0])
    zx = fig.add_subplot(right[1, 0], sharex=cx)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.83, bottom=0.18, wspace=0.43)

    for label, axis in zip('abc', [ax, bx, cx]):
        panel_label(axis, label, x=-0.13, y=1.07)

    ax.set_axis_off()
    ax.set_title('Probe direction and\nperturbation range', loc='left',
                 fontsize=8.8, fontweight='bold', linespacing=1.0, pad=7)
    ax.text(0.02, 0.78, 'Aligned', transform=ax.transAxes, fontsize=8.8, fontweight='bold')
    ax.plot([0.12, 0.80], [0.64, 0.64], transform=ax.transAxes,
            color=COLORS['deep'], linewidth=2.4)
    arrow(ax, (0.48, 0.64), (0.86, 0.64), color=COLORS['teal'], lw=2.1, mutation=12)
    ax.text(0.16, 0.69, r'probe $z$', transform=ax.transAxes,
            color=COLORS['deep'], fontsize=8.4)
    ax.text(0.56, 0.69, 'range(ΔJ)', transform=ax.transAxes,
            color=COLORS['teal'], fontsize=8.4)

    ax.text(0.02, 0.41, 'Orthogonal', transform=ax.transAxes, fontsize=8.8, fontweight='bold')
    ax.plot([0.12, 0.80], [0.25, 0.25], transform=ax.transAxes,
            color=COLORS['deep'], linewidth=2.4)
    arrow(ax, (0.49, 0.25), (0.49, 0.52), color=COLORS['amber'], lw=2.1, mutation=12)
    ax.text(0.16, 0.30, r'probe $z$', transform=ax.transAxes,
            color=COLORS['deep'], fontsize=8.4)
    ax.text(0.54, 0.43, 'range(ΔJ)', transform=ax.transAxes,
            color=COLORS['amber'], fontsize=8.4)
    ax.text(
        0.48, 0.055, 'Matched matrix metrics;\ndifferent probe action',
        transform=ax.transAxes, ha='center', fontsize=8.1,
        fontweight='bold', color=COLORS['coral'],
    )

    metric_styles = [
        ('mu_J', 'o', COLORS['deep'], r'$\mu_J$'),
        ('rho_1', 's', COLORS['teal'], r'$ρ_1$'),
        ('rho_g', '^', COLORS['amber'], r'$ρ_g$'),
    ]
    for field, marker, color, label in metric_styles:
        bx.loglog(
            epsilon, [float(row[field]) for row in aligned],
            marker=marker, markersize=4.8, color=color, label=label,
        )
    bx.set_title('Matched matrix and\ninverse metrics',
                 fontsize=8.8, fontweight='bold', linespacing=1.0, pad=7)
    bx.set_xlabel('Perturbation amplitude ε')
    bx.set_ylabel('Metric value')
    style_axis(bx)
    bx.legend(loc='upper left')

    cx.plot(
        epsilon, [float(row['eta_z']) for row in aligned],
        marker='o', markersize=5.0, color=COLORS['teal'], label='aligned response',
    )
    cx.set_xscale('log')
    cx.set_yscale('log')
    cx.set_title('Directional response\nfor the selected probe',
                 fontsize=8.8, fontweight='bold', linespacing=1.0, pad=7)
    cx.set_ylabel(r'$\eta_z$')
    style_axis(cx)
    cx.legend(loc='upper left')
    cx.tick_params(axis='x', labelbottom=False)

    zx.scatter(epsilon, np.zeros_like(epsilon), marker='x', s=30,
               linewidths=1.5, color=COLORS['coral'])
    zx.axhline(0.0, color=COLORS['coral'], linewidth=0.9, linestyle='--')
    zx.set_xscale('log')
    zx.set_ylim(-0.7, 0.7)
    zx.set_yticks([0.0], [r'$\eta_z=0$'])
    zx.set_xlabel('Perturbation amplitude ε')
    zx.tick_params(axis='y', length=0)
    zx.spines['left'].set_visible(False)
    zx.text(
        0.98, 0.74, 'exact orthogonal response', transform=zx.transAxes,
        ha='right', va='center', fontsize=8.0,
        color=COLORS['coral'], fontweight='bold',
    )
    save_figure(fig, 'F3_directional_response')


if __name__ == '__main__':
    render()
