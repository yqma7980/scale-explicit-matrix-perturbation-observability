from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'inputs'
FIGURES = ROOT / 'figures'
FIGURES.mkdir(parents=True, exist_ok=True)

COLORS = {
    'deep': '#1F5A63',
    'blue': '#4F8EAD',
    'sky': '#78CDEA',
    'teal': '#2E8C85',
    'mint': '#ACEDDB',
    'amber': '#C77724',
    'peach': '#F8CBAC',
    'coral': '#C95454',
    'coral_light': '#FDDAD6',
    'rose': '#A96785',
    'rose_light': '#F4C6DD',
    'lavender': '#E2D4EB',
    'cream': '#FFF9E3',
    'gray': '#6E7B80',
    'gray_light': '#EEF1F1',
    'grid': '#D0CECE',
    'white': '#FFFFFF',
    'black': '#233238',
}

mpl.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.sans-serif': ['Times New Roman'],
    'mathtext.fontset': 'stix',
    'font.size': 8.5,
    'axes.titlesize': 9.5,
    'axes.labelsize': 8.5,
    'xtick.labelsize': 8.6,
    'ytick.labelsize': 8.6,
    'legend.fontsize': 8.6,
    'axes.linewidth': 0.85,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'legend.frameon': False,
    'lines.linewidth': 1.45,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'svg.fonttype': 'none',
    'savefig.facecolor': 'white',
})


def read_csv(name: str) -> list[dict[str, str]]:
    with (INPUTS / name).open('r', encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def read_json(name: str):
    return json.loads((INPUTS / name).read_text(encoding='utf-8-sig'))


def mm_figure(width_mm: float, height_mm: float):
    return plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4))


def panel_label(ax, label: str, x: float = -0.11, y: float = 1.035) -> None:
    ax.text(
        x, y, label, transform=ax.transAxes, fontsize=10.5,
        fontweight='bold', va='bottom', ha='left',
        color=COLORS['black'], clip_on=False,
    )


def arrow(
    ax, start, end, *, color: str | None = None, lw: float = 1.2,
    mutation: float = 10.0, connectionstyle: str = 'arc3',
    zorder: int = 2,
) -> None:
    ax.add_patch(FancyArrowPatch(
        start, end, transform=ax.transAxes, arrowstyle='-|>',
        mutation_scale=mutation, linewidth=lw,
        color=color or COLORS['deep'], connectionstyle=connectionstyle,
        shrinkA=1.5, shrinkB=1.5, zorder=zorder,
    ))


def box(
    ax, xy, width, height, text, *, edge: str, face: str,
    fontsize: float = 8.3, weight: str = 'normal',
    radius: float = 0.012, linewidth: float = 1.15,
) -> None:
    ax.add_patch(FancyBboxPatch(
        xy, width, height, transform=ax.transAxes,
        boxstyle=f'round,pad=0.006,rounding_size={radius}',
        facecolor=face, edgecolor=edge, linewidth=linewidth, zorder=1,
    ))
    ax.text(
        xy[0] + width / 2, xy[1] + height / 2, text,
        transform=ax.transAxes, ha='center', va='center',
        fontsize=fontsize, fontweight=weight, color=COLORS['black'],
        linespacing=1.18, zorder=3,
    )


def style_axis(ax, *, grid: str = 'both') -> None:
    if grid in {'both', 'x'}:
        ax.grid(axis='x', color=COLORS['grid'], linewidth=0.55, alpha=0.85)
    if grid in {'both', 'y'}:
        ax.grid(axis='y', color=COLORS['grid'], linewidth=0.55, alpha=0.85)
    ax.set_axisbelow(True)


def save_figure(fig, stem: str) -> None:
    for suffix in ('pdf', 'svg', 'eps'):
        fig.savefig(FIGURES / f'{stem}.{suffix}', bbox_inches=None)
    fig.savefig(FIGURES / f'{stem}.png', dpi=600, bbox_inches=None)
    plt.close(fig)


def finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f'non-finite frozen input: {value}')
    return result
