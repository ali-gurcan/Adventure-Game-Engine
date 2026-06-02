"""
Rich Markup utility for terminal output.
Replaces raw ANSI escape codes with rich markup tags.
"""

def room_name(text: str) -> str:
    """Bold Green — for room names."""
    return f"[bold green]{text}[/]"

def enemy(text: str) -> str:
    """Bold Red — for enemies and damage numbers."""
    return f"[bold red]{text}[/]"

def damage(text: str) -> str:
    """Red — for damage values."""
    return f"[red]{text}[/]"

def item(text: str) -> str:
    """Yellow — for items and inventory."""
    return f"[yellow]{text}[/]"

def item_bold(text: str) -> str:
    """Bold Yellow — for item highlights."""
    return f"[bold yellow]{text}[/]"

def narration(text: str) -> str:
    """Italic White — for story narration."""
    return f"[italic white]{text}[/]"

def hp_color(current_hp: int, max_hp: int = 200) -> str:
    """Color-coded HP display: green if healthy, yellow if mid, red if low."""
    if current_hp > max_hp * 0.5:
        return f"[green]{current_hp}[/]"
    elif current_hp > max_hp * 0.25:
        return f"[yellow]{current_hp}[/]"
    else:
        return f"[bold red]{current_hp}[/]"

def success(text: str) -> str:
    """Bold Green — for success messages."""
    return f"[bold green]{text}[/]"

def warning(text: str) -> str:
    """Bold Yellow — for warnings."""
    return f"[bold yellow]{text}[/]"

def error(text: str) -> str:
    """Bold Red — for errors."""
    return f"[bold red]{text}[/]"

def info(text: str) -> str:
    """Cyan — for info/system messages."""
    return f"[cyan]{text}[/]"

def bold(text: str) -> str:
    """Bold white."""
    return f"[bold white]{text}[/]"

def dim(text: str) -> str:
    """Dim text."""
    return f"[dim]{text}[/]"

def gold(amount) -> str:
    """Bold Yellow — for gold amounts."""
    return f"[bold yellow]{amount}g[/]"

def merchant(text: str) -> str:
    """Magenta — for merchant names and trade messages."""
    return f"[magenta]{text}[/]"

def defense_color(text: str) -> str:
    """Cyan — for defense/armor values."""
    return f"[cyan]{text}[/]"

