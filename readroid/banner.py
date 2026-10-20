"""Banner grande do ReaDroid, desenhado com blocos sólidos.

Cada letra é uma matriz de pixels ('#' = bloco cheio). Usa só a biblioteca padrão
e se adapta à largura do terminal: abaixo de WIDE_MIN colunas cai para um banner compacto.
"""
from __future__ import annotations

GLYPHS: dict[str, list[str]] = {
    "R": ["###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"],
    "e": ["....", "....", ".##.", "#..#", "####", "#...", ".###"],
    "a": ["....", "....", ".##.", "...#", ".###", "#..#", ".###"],
    "D": ["###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."],
    "r": ["....", "....", "#.##", "##..", "#...", "#...", "#..."],
    "o": ["....", "....", ".##.", "#..#", "#..#", "#..#", ".##."],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "d": ["...#", "...#", ".###", "#..#", "#..#", "#..#", ".###"],
}
NAME = "ReaDroid"
BLOCK = "█"
WIDE_MIN = 36  # colunas necessárias para o banner grande


def big_rows(name: str = NAME, gap: int = 1) -> list[list[str]]:
    """Devolve as 7 linhas do banner, cada uma como lista de pedaços (um por letra)."""
    height = len(GLYPHS["R"])
    rows: list[list[str]] = [[] for _ in range(height)]
    for ch in name:
        glyph = GLYPHS[ch]
        for y in range(height):
            rows[y].append("".join(BLOCK if px == "#" else " " for px in glyph[y]))
    return rows


def plain_lines(name: str = NAME, gap: int = 1) -> list[str]:
    sep = " " * gap
    return [sep.join(parts).rstrip() for parts in big_rows(name)]


def big_width(name: str = NAME, gap: int = 1) -> int:
    return max(len(line) for line in plain_lines(name, gap))


def render(columns: int, colors: tuple[str, str, str]) -> list[str]:
    """Linhas prontas para imprimir. colors = (cor_Rea, cor_Droid, reset)."""
    c1, c2, reset = colors
    if columns < max(WIDE_MIN, big_width()):
        return [c1 + "█▀▀ ReaDroid ▀▀█" + reset]
    parts = big_rows()
    lines = []
    for y in range(len(parts)):
        cells = []
        for i, piece in enumerate(parts[y]):
            cells.append((c1 if i < 3 else c2) + piece + reset)
        lines.append(" ".join(cells))
    return lines
