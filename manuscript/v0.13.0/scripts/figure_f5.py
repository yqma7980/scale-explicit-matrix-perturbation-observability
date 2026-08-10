from matplotlib.patches import FancyBboxPatch

from render_publication import COLORS, arrow, box, mm_figure, save_figure


def contract_lane(ax, x0, title, items, edge, face) -> None:
    ax.add_patch(FancyBboxPatch(
        (x0, 0.57), 0.455, 0.31, transform=ax.transAxes,
        boxstyle='round,pad=0.006,rounding_size=0.012',
        facecolor=face, edgecolor=edge, linewidth=1.15,
    ))
    ax.text(
        x0 + 0.2275, 0.835, title, transform=ax.transAxes,
        ha='center', fontsize=9.0, fontweight='bold', color=edge,
    )
    box_x = [x0 + 0.025, x0 + 0.168, x0 + 0.311]
    for index, ((heading, formula), x) in enumerate(zip(items, box_x)):
        box(
            ax, (x, 0.64), 0.118, 0.125, f'{heading}\n{formula}',
            edge=edge, face=COLORS['white'], fontsize=8.5, weight='bold',
        )
        if index < 2:
            arrow(ax, (x + 0.118, 0.702), (box_x[index + 1], 0.702),
                  color=edge, mutation=8.5)


def render() -> None:
    fig = mm_figure(190, 110)
    ax = fig.add_axes([0.03, 0.045, 0.94, 0.92])
    ax.set_axis_off()
    ax.text(
        0.0, 0.975, 'Reference problems and direct-difference uncertainty anatomy',
        transform=ax.transAxes, fontsize=10.4, fontweight='bold',
        color=COLORS['black'], va='top',
    )

    contract_lane(
        ax, 0.02, 'DECIMAL-SOURCE REFERENCE',
        [('Declared\noperands', r'$A_s,b_s$'),
         ('Parent\nsolutions', r'$z_s,z_{g,s}$'),
         ('Parent\nbounds', r'$U_{z,s},U_{zg,s}$')],
        COLORS['deep'], '#E9F5FA',
    )
    contract_lane(
        ax, 0.525, 'BINARY64-OPERAND REFERENCE',
        [('Captured\noperands', r'$A_b,b_b$'),
         ('Parent\nsolutions', r'$z_b,z_{g,b}$'),
         ('Parent\nbounds', r'$U_{z,b},U_{zg,b}$')],
        COLORS['teal'], '#E8F6F2',
    )

    ax.add_patch(FancyBboxPatch(
        (0.19, 0.49), 0.62, 0.055, transform=ax.transAxes,
        boxstyle='round,pad=0.004,rounding_size=0.009',
        facecolor=COLORS['coral_light'], edgecolor=COLORS['coral'], linewidth=1.0,
    ))
    ax.text(
        0.50, 0.518, 'Reference problems remain separate; cross-reference mixing is not allowed',
        transform=ax.transAxes, ha='center', va='center',
        fontsize=8.2, fontweight='bold', color=COLORS['coral'],
    )

    ax.text(0.02, 0.43, 'Direct-difference computational route',
            transform=ax.transAxes, fontsize=9.0, fontweight='bold')
    components = [
        (0.04, COLORS['deep'], '#E9F5FA', r'parent $z$', r'$U_z$'),
        (0.275, COLORS['teal'], '#E8F6F2', r'parent $z_g$', r'$U_{zg}$'),
        (0.510, COLORS['amber'], COLORS['cream'], 'subtraction', r'$U_{\mathrm{sub}}$'),
    ]
    for x, edge, face, title, formula in components:
        box(
            ax, (x, 0.245), 0.19, 0.13, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=8.5, weight='bold',
        )
    ax.text(0.252, 0.310, '+', transform=ax.transAxes,
            fontsize=12, fontweight='bold', ha='center', va='center')
    ax.text(0.487, 0.310, '+', transform=ax.transAxes,
            fontsize=12, fontweight='bold', ha='center', va='center')
    arrow(ax, (0.700, 0.310), (0.755, 0.310), color=COLORS['gray'])
    box(
        ax, (0.755, 0.220), 0.225, 0.18,
        'Route envelope\n' + r'$U_{\mathrm{direct}}$' + '\n'
        + r'$=U_z+U_{zg}+U_{\mathrm{sub}}$',
        edge=COLORS['coral'], face=COLORS['coral_light'],
        fontsize=8.6, weight='bold',
    )

    ax.add_patch(FancyBboxPatch(
        (0.02, 0.055), 0.96, 0.105, transform=ax.transAxes,
        boxstyle='round,pad=0.006,rounding_size=0.010',
        facecolor=COLORS['gray_light'], edgecolor=COLORS['grid'], linewidth=1.0,
    ))
    ax.text(
        0.50, 0.108,
        'Coverage and threshold decisions are evaluated only against the matching reference and route.',
        transform=ax.transAxes, ha='center', va='center',
        fontsize=8.3, fontweight='bold', color=COLORS['gray'],
    )
    save_figure(fig, 'F5_two_reference_contracts')


if __name__ == '__main__':
    render()
