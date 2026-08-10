from matplotlib.patches import FancyBboxPatch

from render_publication import COLORS, arrow, box, mm_figure, save_figure


def render() -> None:
    fig = mm_figure(190, 118)
    ax = fig.add_axes([0.025, 0.035, 0.95, 0.93])
    ax.set_axis_off()
    ax.text(
        0.0, 0.98, 'Reference contracts and route-specific error propagation',
        transform=ax.transAxes, fontsize=10.4, fontweight='bold',
        color=COLORS['black'], va='top',
    )

    box(
        ax, (0.05, 0.80), 0.39, 0.115,
        'DECIMAL-SOURCE REFERENCE\nregistered decimal operands',
        edge=COLORS['deep'], face='#E9F5FA', fontsize=8.7, weight='bold',
    )
    box(
        ax, (0.56, 0.80), 0.39, 0.115,
        'BINARY64-OPERAND REFERENCE\nexact-real captured operands',
        edge=COLORS['teal'], face='#E8F6F2', fontsize=8.7, weight='bold',
    )
    ax.text(
        0.50, 0.855, 'NO\nCROSS-CONTRACT\nSUBSTITUTION',
        transform=ax.transAxes, ha='center', va='center',
        fontsize=7.7, color=COLORS['coral'], fontweight='bold',
    )

    ax.add_patch(FancyBboxPatch(
        (0.035, 0.42), 0.445, 0.29, transform=ax.transAxes,
        boxstyle='round,pad=0.006,rounding_size=0.012',
        facecolor='#FFF9E3', edgecolor=COLORS['amber'], linewidth=1.15,
    ))
    ax.text(
        0.257, 0.675, 'DIRECT-DIFFERENCE GRAPH',
        transform=ax.transAxes, ha='center', fontsize=8.9,
        fontweight='bold', color=COLORS['amber'],
    )
    direct = [
        (0.055, 'parent $z$', r'$U_z$', COLORS['deep'], '#E9F5FA'),
        (0.170, 'guarded parent', r'$U_g$', COLORS['teal'], '#E8F6F2'),
        (0.285, 'subtraction', r'$U_s$', COLORS['amber'], COLORS['cream']),
    ]
    for x, title, formula, edge, face in direct:
        box(ax, (x, 0.50), 0.10, 0.115, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=9.0, weight='bold')
    ax.text(0.160, 0.557, '+', transform=ax.transAxes, ha='center',
            va='center', fontsize=11, fontweight='bold')
    ax.text(0.275, 0.557, '+', transform=ax.transAxes, ha='center',
            va='center', fontsize=11, fontweight='bold')
    arrow(ax, (0.385, 0.557), (0.405, 0.557), color=COLORS['gray'])
    box(
        ax, (0.405, 0.485), 0.055, 0.145,
        r'$U_{\rm d}$', edge=COLORS['coral'], face=COLORS['coral_light'],
        fontsize=8.7, weight='bold',
    )

    ax.add_patch(FancyBboxPatch(
        (0.52, 0.42), 0.445, 0.29, transform=ax.transAxes,
        boxstyle='round,pad=0.006,rounding_size=0.012',
        facecolor='#E8F6F2', edgecolor=COLORS['teal'], linewidth=1.15,
    ))
    ax.text(
        0.742, 0.675, 'RESPONSE-EQUATION GRAPH',
        transform=ax.transAxes, ha='center', fontsize=8.9,
        fontweight='bold', color=COLORS['teal'],
    )
    response = [
        (0.540, 'parent', r'$U_p$', COLORS['deep'], '#E9F5FA'),
        (0.655, 'forcing', r'$U_f$', COLORS['amber'], COLORS['cream']),
        (0.770, 'solve', r'$U_s$', COLORS['teal'], '#E8F6F2'),
    ]
    for x, title, formula, edge, face in response:
        box(ax, (x, 0.50), 0.10, 0.115, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=9.0, weight='bold')
    ax.text(0.645, 0.557, '+', transform=ax.transAxes, ha='center',
            va='center', fontsize=11, fontweight='bold')
    ax.text(0.760, 0.557, '+', transform=ax.transAxes, ha='center',
            va='center', fontsize=11, fontweight='bold')
    arrow(ax, (0.870, 0.557), (0.890, 0.557), color=COLORS['gray'])
    box(
        ax, (0.890, 0.485), 0.055, 0.145,
        r'$U_{\rm r}$', edge=COLORS['coral'], face=COLORS['coral_light'],
        fontsize=8.7, weight='bold',
    )

    arrow(ax, (0.245, 0.80), (0.245, 0.715), color=COLORS['deep'])
    arrow(ax, (0.755, 0.80), (0.755, 0.715), color=COLORS['teal'])
    box(
        ax, (0.17, 0.20), 0.66, 0.12,
        r'Matching interval: $[\max(0,d_a-U_a),\ d_a+U_a]$',
        edge=COLORS['deep'], face=COLORS['gray_light'],
        fontsize=8.7, weight='bold',
    )
    arrow(ax, (0.26, 0.42), (0.39, 0.32), color=COLORS['amber'])
    arrow(ax, (0.74, 0.42), (0.61, 0.32), color=COLORS['teal'])
    ax.text(
        0.50, 0.075,
        'Coverage and threshold decisions use the matching reference contract and operation graph.',
        transform=ax.transAxes, ha='center', va='center',
        fontsize=8.3, fontweight='bold', color=COLORS['gray'],
    )
    save_figure(fig, 'F5_two_reference_contracts')


if __name__ == '__main__':
    render()
