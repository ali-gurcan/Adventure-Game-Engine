"""
ANSI Color utility for terminal output.
No external dependencies — uses raw ANSI escape codes.
"""

# Reset
RESET = "\033[0m"

# Regular colors
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN = "\033[0;36m"
WHITE = "\033[0;37m"

# Bold
BOLD = "\033[1m"
BOLD_RED = "\033[1;31m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"
BOLD_CYAN = "\033[1;36m"
BOLD_WHITE = "\033[1;37m"

# Italic
ITALIC = "\033[3m"
ITALIC_WHITE = "\033[3;37m"

# Dim
DIM = "\033[2m"


# Helper functions
def room_name(text: str) -> str:
    """Bold Green — for room names."""
    return f"{BOLD_GREEN}{text}{RESET}"

def enemy(text: str) -> str:
    """Bold Red — for enemies and damage numbers."""
    return f"{BOLD_RED}{text}{RESET}"

def damage(text: str) -> str:
    """Red — for damage values."""
    return f"{RED}{text}{RESET}"

def item(text: str) -> str:
    """Yellow — for items and inventory."""
    return f"{YELLOW}{text}{RESET}"

def item_bold(text: str) -> str:
    """Bold Yellow — for item highlights."""
    return f"{BOLD_YELLOW}{text}{RESET}"

def narration(text: str) -> str:
    """Italic White — for story narration."""
    return f"{ITALIC_WHITE}{text}{RESET}"

def hp_color(current_hp: int, max_hp: int = 200) -> str:
    """Color-coded HP display: green if healthy, yellow if mid, red if low."""
    if current_hp > max_hp * 0.5:
        return f"{GREEN}{current_hp}{RESET}"
    elif current_hp > max_hp * 0.25:
        return f"{YELLOW}{current_hp}{RESET}"
    else:
        return f"{BOLD_RED}{current_hp}{RESET}"

def success(text: str) -> str:
    """Bold Green — for success messages."""
    return f"{BOLD_GREEN}{text}{RESET}"

def warning(text: str) -> str:
    """Bold Yellow — for warnings."""
    return f"{BOLD_YELLOW}{text}{RESET}"

def error(text: str) -> str:
    """Bold Red — for errors."""
    return f"{BOLD_RED}{text}{RESET}"

def info(text: str) -> str:
    """Cyan — for info/system messages."""
    return f"{CYAN}{text}{RESET}"

def bold(text: str) -> str:
    """Bold white."""
    return f"{BOLD_WHITE}{text}{RESET}"

def dim(text: str) -> str:
    """Dim text."""
    return f"{DIM}{text}{RESET}"
