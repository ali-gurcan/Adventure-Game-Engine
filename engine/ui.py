from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text

# Global console instance
console = Console()

def print_hp_bar(current_hp: int, max_hp: int = 200, label: str = "HP"):
    """
    Returns a rendered Rich Text object representing an HP bar.
    """
    ratio = current_hp / max_hp if max_hp > 0 else 0
    ratio = max(0, min(1, ratio)) # Clamp between 0 and 1
    
    bar_width = 20
    filled = int(ratio * bar_width)
    empty = bar_width - filled
    
    if ratio > 0.5:
        color = "green"
    elif ratio > 0.25:
        color = "yellow"
    else:
        color = "red"
        
    bar_text = f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
    return Text.from_markup(f"[bold]{label}:[/] {bar_text} {current_hp}/{max_hp}")
