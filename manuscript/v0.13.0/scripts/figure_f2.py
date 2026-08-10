import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from render_publication import COLORS, arrow, box, panel_label, save_figure


def render() -> None:
    fig, axes = plt.subplots(
        1, 2, figsize=(190 / 25.4, 100 / 25.4),
        gridspec_kw={'width_ratios': [1.08, 0.92]},
    )
    fig.subplots_adjust(left=0.055, right=0.985, top=0.86, bottom=0.12, wspace=0.25)
    ax, bx = axes
    for label, axis in zip('ab', axes):
        panel_label(axis, label, x=-0.10, y=1.05)
        axis.set_axis_off()

    ax.set_title('Mixed-field tangent blocks and variable units', loc='left', fontweight='bold')
    bx.set_title('One scalar identity is not one field scale', loc='left', fontweight='bold')

    x0, y0, width, height = 0.26, 0.17, 0.185, 0.175
    rows = ['displacement\nresidual', 'pressure\nresidual', 'saturation\nresidual']
    cols = [r'$u$  [m]', r'$p$  [Pa]', r'$S$  [-]']
    symbols = [
        [r'$J_{uu}$', r'$J_{up}$', r'$J_{uS}$'],
        [r'$J_{pu}$', r'$J_{pp}$', r'$J_{pS}$'],
        [r'$J_{Su}$', r'$J_{Sp}$', r'$J_{SS}$'],
    ]
    faces = ['#E9F5FA', COLORS['cream'], '#E8F6F2']
    edges = [COLORS['blue'], COLORS['amber'], COLORS['teal']]
    for col, name in enumerate(cols):
        ax.text(
            x0 + (col + 0.5) * width, y0 + 3 * height + 0.055, name,
            transform=ax.transAxes, ha='center', va='bottom',
            fontsize=8.6, fontweight='bold',
        )
    for row, name in enumerate(rows):
        y = y0 + (2 - row) * height
        ax.text(
            x0 - 0.03, y + height / 2, name, transform=ax.transAxes,
            ha='right', va='center', fontsize=8.1, linespacing=1.05,
        )
        for col in range(3):
            x = x0 + col * width
            diagonal = row == col
            ax.add_patch(Rectangle(
                (x, y), width, height, transform=ax.transAxes,
                facecolor=faces[col] if diagonal else COLORS['gray_light'],
                edgecolor=edges[col] if diagonal else COLORS['grid'],
                linewidth=1.1 if diagonal else 0.8,
            ))
            ax.text(
                x + width / 2, y + height / 2, symbols[row][col],
                transform=ax.transAxes, ha='center', va='center',
                fontsize=10.0, fontweight='bold' if diagonal else 'normal',
            )
    ax.text(
        0.54, 0.075, 'Physical-coordinate modification:  ΔJ = εI',
        transform=ax.transAxes, ha='center', fontsize=8.6,
        fontweight='bold', color=COLORS['coral'],
    )

    box(
        bx, (0.09, 0.70), 0.82, 0.14,
        'Physical coordinates:  ΔJ = εI',
        edge=COLORS['coral'], face=COLORS['coral_light'],
        fontsize=8.9, weight='bold',
    )
    arrow(bx, (0.50, 0.70), (0.50, 0.615), color=COLORS['deep'])
    box(
        bx, (0.22, 0.49), 0.56, 0.125,
        r'$\widehat{\Delta J}=D_r^{-1}\Delta J D_x$',
        edge=COLORS['deep'], face=COLORS['white'], fontsize=9.4,
    )
    centers = [0.18, 0.50, 0.82]
    for center in centers:
        arrow(bx, (0.50, 0.49), (center, 0.395), color=COLORS['gray'])
    field_boxes = [
        (0.04, COLORS['blue'], '#E9F5FA', r'$u$ block', r'$\epsilon r_u^{-1}x_u$'),
        (0.36, COLORS['amber'], COLORS['cream'], r'$p$ block', r'$\epsilon r_p^{-1}x_p$'),
        (0.68, COLORS['teal'], '#E8F6F2', r'$S$ block', r'$\epsilon r_S^{-1}x_S$'),
    ]
    for x, edge, face, title, formula in field_boxes:
        box(
            bx, (x, 0.20), 0.28, 0.18, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=8.6, weight='bold',
        )
    bx.text(
        0.50, 0.060,
        'Equal diagonal entries need not represent\n'
        'equal scaled perturbations.',
        transform=bx.transAxes, ha='center', va='center', fontsize=8.1,
        fontweight='bold', color=COLORS['coral'],
    )
    save_figure(fig, 'F2_mixed_field_tangent_anatomy')


if __name__ == '__main__':
    render()
