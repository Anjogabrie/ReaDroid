"""Compact, bold ReaDroid terminal banner."""

ART = [
    "██████╗ ███████╗ █████╗ ██████╗",
    "██╔══██╗██╔════╝██╔══██╗██╔══██╗",
    "██████╔╝█████╗  ███████║██║  ██║",
    "██╔══██╗██╔══╝  ██╔══██║██║  ██║",
    "██║  ██║███████╗██║  ██║██████╔╝",
    "╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝",
]

def render(columns: int, colors: tuple[str, str, str]) -> list[str]:
    green, cyan, reset = colors
    gold = "\033[38;5;220m"
    width = max(24, min(int(columns), 78))

    # Wordmark compacto para caber em Termux com 44 colunas.
    lines = [""]
    for i, art_line in enumerate(ART):
        color = gold
        lines.append(f"{color}{art_line.center(width)}{reset}")

    lines.extend([
        f"{cyan}{'ANDROID APK ANALYSIS'.center(width)}{reset}",
        f"{gold}{'REVERSE ENGINEERING AGENT'.center(width)}{reset}",
        "",
    ])
    return lines
