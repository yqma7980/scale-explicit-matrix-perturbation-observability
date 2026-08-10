from render_publication import COLORS, arrow, box, mm_figure, save_figure


def render() -> None:
    fig = mm_figure(190, 112)
    ax = fig.add_axes([0.025, 0.035, 0.95, 0.93])
    ax.set_axis_off()
    ax.text(
        0.0, 0.98,
        'Coordinate-explicit, route-specific response-enclosure method',
        transform=ax.transAxes, fontsize=10.4, fontweight='bold',
        color=COLORS['black'], va='top',
    )

    box(
        ax, (0.04, 0.81), 0.69, 0.12,
        r'Frozen problem: $(J,A,\Delta J,b,D_x,D_r,\Vert\cdot\Vert,\tau)$'
        '\nsolved space, reference contract and arithmetic specification',
        edge=COLORS['deep'], face='#E7F2F4', fontsize=8.7, weight='bold',
    )
    box(
        ax, (0.77, 0.81), 0.19, 0.12,
        'No post-result\nselection',
        edge=COLORS['amber'], face=COLORS['cream'],
        fontsize=8.4, weight='bold',
    )

    box(
        ax, (0.04, 0.58), 0.18, 0.14,
        'Matrix space\n' + r'$\mu_J$',
        edge=COLORS['blue'], face='#E9F5FA', fontsize=8.6, weight='bold',
    )
    box(
        ax, (0.27, 0.58), 0.18, 0.14,
        'Worst direction\n' + r'$\rho_1,\rho_g$',
        edge=COLORS['deep'], face='#E7F2F4', fontsize=8.6, weight='bold',
    )
    box(
        ax, (0.50, 0.58), 0.20, 0.14,
        'Selected response\n' + r'$A\delta z=-Ez$',
        edge=COLORS['teal'], face='#E8F6F2', fontsize=8.6, weight='bold',
    )
    arrow(ax, (0.22, 0.65), (0.27, 0.65), color=COLORS['gray'])
    arrow(ax, (0.45, 0.65), (0.50, 0.65), color=COLORS['gray'])
    arrow(ax, (0.385, 0.81), (0.385, 0.74), color=COLORS['deep'])

    box(
        ax, (0.75, 0.67), 0.21, 0.12,
        'Direct difference\n' + r'$U_{\rm d}$',
        edge=COLORS['amber'], face=COLORS['cream'], fontsize=8.5, weight='bold',
    )
    box(
        ax, (0.75, 0.49), 0.21, 0.12,
        'Response equation\n' + r'$U_{\rm r}$',
        edge=COLORS['coral'], face=COLORS['coral_light'],
        fontsize=8.5, weight='bold',
    )
    arrow(ax, (0.70, 0.67), (0.75, 0.73), color=COLORS['amber'])
    arrow(ax, (0.70, 0.63), (0.75, 0.55), color=COLORS['coral'])

    box(
        ax, (0.17, 0.31), 0.66, 0.12,
        r'Route interval: $[L_a,H_a]=[\max(0,d_a-U_a),\ d_a+U_a]$',
        edge=COLORS['deep'], face=COLORS['gray_light'],
        fontsize=8.7, weight='bold',
    )
    arrow(ax, (0.855, 0.49), (0.76, 0.43), color=COLORS['coral'])
    arrow(ax, (0.855, 0.67), (0.76, 0.43), color=COLORS['amber'])

    outcomes = [
        (0.08, 'BELOW', r'$H_a<\tau$', COLORS['blue'], '#E9F5FA'),
        (0.385, 'UNRESOLVED', r'$L_a\leq\tau\leq H_a$', COLORS['amber'], COLORS['cream']),
        (0.69, 'ABOVE', r'$L_a>\tau$', COLORS['teal'], '#E8F6F2'),
    ]
    for x, title, formula, edge, face in outcomes:
        box(
            ax, (x, 0.16), 0.23, 0.095, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=8.7, weight='bold',
        )
        arrow(ax, (0.50, 0.31), (x + 0.115, 0.255), color=edge)

    ax.text(
        0.50, 0.055,
        'Output: a selected finite-precision response relation, not a matrix-only or nonlinear-convergence claim',
        transform=ax.transAxes, ha='center', va='center',
        fontsize=8.2, fontweight='bold', color=COLORS['gray'],
    )
    save_figure(fig, 'F1_assessment_sequence')


if __name__ == '__main__':
    render()
