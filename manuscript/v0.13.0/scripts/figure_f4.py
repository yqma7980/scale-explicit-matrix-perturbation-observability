import matplotlib.pyplot as plt

from render_publication import COLORS, arrow, box, panel_label, read_csv, save_figure, style_axis


def render() -> None:
    rows = read_csv('P3_scaling_audit.csv')
    transformed = sorted(
        (row for row in rows if row['lane_id'] == 'PHYSICAL_GUARD_TRANSFORMED'),
        key=lambda row: float(row['s']),
    )
    redeclared = sorted(
        (row for row in rows if row['lane_id'] == 'IDENTITY_REDECLARED_IN_SCALED_COORDINATES'),
        key=lambda row: float(row['s']),
    )
    scales = [float(row['s']) for row in transformed]
    eta_transform = [float(row['eta_physical_coordinates']) for row in transformed]
    eta_redeclare = [float(row['eta_physical_coordinates']) for row in redeclared]

    fig, axes = plt.subplots(
        1, 2, figsize=(190 / 25.4, 94 / 25.4),
        gridspec_kw={'width_ratios': [1.16, 0.84]},
    )
    fig.subplots_adjust(left=0.055, right=0.985, top=0.84, bottom=0.18, wspace=0.27)
    ax, bx = axes
    for label, axis in zip('ab', axes):
        panel_label(axis, label, x=-0.10, y=1.06)

    ax.set_axis_off()
    ax.set_title('Coordinate transformation and operator redeclaration', loc='left', fontweight='bold')
    ax.text(0.24, 0.89, 'SAME OPERATOR', transform=ax.transAxes, ha='center',
            fontsize=9.0, fontweight='bold', color=COLORS['teal'])
    box(
        ax, (0.03, 0.64), 0.42, 0.15, 'Physical: ΔJ = εI',
        edge=COLORS['teal'], face='#E8F6F2', fontsize=8.9, weight='bold',
    )
    arrow(ax, (0.24, 0.64), (0.24, 0.47), color=COLORS['teal'])
    ax.text(0.24, 0.535, r'consistent map $D_r^{-1}(\cdot)D_x$',
            transform=ax.transAxes, ha='center', fontsize=8.6, color=COLORS['gray'])
    box(
        ax, (0.03, 0.27), 0.42, 0.15,
        r'Scaled: $\widehat{\Delta J}=\epsilon D_r^{-1}D_x$',
        edge=COLORS['teal'], face='#E8F6F2', fontsize=8.6, weight='bold',
    )
    ax.text(0.24, 0.12, 'EQUIVALENT', transform=ax.transAxes, ha='center',
            fontsize=9.0, fontweight='bold', color=COLORS['teal'])

    ax.text(0.76, 0.89, 'REDECLARED OPERATOR', transform=ax.transAxes, ha='center',
            fontsize=9.0, fontweight='bold', color=COLORS['coral'])
    box(
        ax, (0.55, 0.64), 0.42, 0.15,
        r'Scaled: $\widehat{\Delta J}=\epsilon I$',
        edge=COLORS['amber'], face=COLORS['cream'], fontsize=8.9, weight='bold',
    )
    arrow(ax, (0.76, 0.64), (0.76, 0.47), color=COLORS['coral'])
    ax.text(0.76, 0.535, r'map back $D_r(\cdot)D_x^{-1}$',
            transform=ax.transAxes, ha='center', fontsize=8.6, color=COLORS['gray'])
    box(
        ax, (0.55, 0.27), 0.42, 0.15,
        r'Physical: $\Delta J=\epsilon D_rD_x^{-1}$',
        edge=COLORS['coral'], face=COLORS['coral_light'], fontsize=8.6, weight='bold',
    )
    ax.text(0.76, 0.12, 'NOT EQUIVALENT', transform=ax.transAxes, ha='center',
            fontsize=9.0, fontweight='bold', color=COLORS['coral'])

    bx.loglog(scales, eta_transform, marker='o', markersize=5.0,
              color=COLORS['teal'], label='consistent transform')
    bx.loglog(scales, eta_redeclare, marker='s', markersize=4.8,
              linestyle='--', color=COLORS['coral'], label='same-number redeclaration')
    bx.set_title('Response of the represented operator', fontweight='bold')
    bx.set_xlabel(r'Unknown-coordinate scale $s$')
    bx.set_ylabel(r'Physical response $\eta_z$')
    style_axis(bx)
    bx.legend(loc='lower left')
    save_figure(fig, 'F4_coordinate_transformation')


if __name__ == '__main__':
    render()
