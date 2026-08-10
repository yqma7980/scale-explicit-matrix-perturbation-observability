from matplotlib.patches import FancyBboxPatch

from render_publication import COLORS, arrow, box, mm_figure, save_figure


def render() -> None:
    fig = mm_figure(190, 112)
    ax = fig.add_axes([0.025, 0.035, 0.95, 0.93])
    ax.set_axis_off()
    ax.text(
        0.0, 0.975, 'Coordinate- and route-aware response qualification',
        transform=ax.transAxes, fontsize=10.4, fontweight='bold',
        color=COLORS['black'], va='top',
    )

    box(
        ax, (0.03, 0.79), 0.64, 0.125,
        r'Problem specification: $(J,\Delta J,b,D_x,D_r,\Vert\cdot\Vert)$'
        '\ncoordinates, norm, probe and reference problem',
        edge=COLORS['deep'], face='#E8F6F2', fontsize=8.5, weight='bold',
    )
    box(
        ax, (0.72, 0.79), 0.25, 0.125,
        'Freeze before evaluation\nNo post-result selection',
        edge=COLORS['amber'], face=COLORS['cream'],
        fontsize=8.4, weight='bold',
    )
    arrow(ax, (0.35, 0.79), (0.35, 0.715), color=COLORS['deep'])

    stages = [
        (0.025, 0.165, 'Matrix amplitude', r'$\mu_J$', COLORS['deep'], '#E7F2F4'),
        (0.215, 0.165, 'Inverse response', r'$ρ_1,\ ρ_g$', COLORS['blue'], '#E9F5FA'),
        (0.405, 0.165, 'Directional response', r'$\eta_z$', COLORS['teal'], '#E8F6F2'),
        (0.595, 0.175, 'Route uncertainty', r'$d_{\mathrm{obs}}\ \pm\ U$', COLORS['amber'], COLORS['cream']),
        (0.795, 0.180, 'Qualified decision', r'$d_{\mathrm{obs}}-U>\tau$?', COLORS['coral'], COLORS['coral_light']),
    ]
    for index, (x, width, title, formula, edge, face) in enumerate(stages):
        box(
            ax, (x, 0.53), width, 0.155, f'{title}\n{formula}',
            edge=edge, face=face, fontsize=8.6, weight='bold',
        )
        if index < len(stages) - 1:
            next_x = stages[index + 1][0]
            arrow(ax, (x + width, 0.607), (next_x, 0.607), color=COLORS['gray'])

    box(
        ax, (0.14, 0.285), 0.32, 0.125,
        'ABOVE THRESHOLD\nresponse distinguished under the route',
        edge=COLORS['teal'], face='#E8F6F2', fontsize=8.4, weight='bold',
    )
    box(
        ax, (0.55, 0.285), 0.32, 0.125,
        'UNRESOLVED\nthreshold crossing cannot be excluded',
        edge=COLORS['amber'], face=COLORS['cream'], fontsize=8.4, weight='bold',
    )
    arrow(
        ax, (0.85, 0.53), (0.30, 0.41), color=COLORS['teal'],
        connectionstyle='arc3,rad=0.05',
    )
    arrow(
        ax, (0.91, 0.53), (0.71, 0.41), color=COLORS['amber'],
        connectionstyle='arc3,rad=-0.05',
    )

    ax.add_patch(FancyBboxPatch(
        (0.03, 0.055), 0.94, 0.135, transform=ax.transAxes,
        boxstyle='round,pad=0.006,rounding_size=0.010',
        facecolor=COLORS['gray_light'], edgecolor=COLORS['grid'], linewidth=1.0,
    ))
    ax.text(
        0.055, 0.123, 'Inference boundary', transform=ax.transAxes,
        fontsize=8.8, fontweight='bold', color=COLORS['coral'], va='center',
    )
    ax.text(
        0.225, 0.123,
        'The decision qualifies a numerical response under the specified route.\n'
        'Physical significance and nonlinear consequences require separate evidence.',
        transform=ax.transAxes, fontsize=8.1, color=COLORS['black'], va='center',
    )
    save_figure(fig, 'F1_assessment_sequence')


if __name__ == '__main__':
    render()
