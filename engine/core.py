from engine.game_state import GameState
from engine.parser import Parser
from engine.events import Subject, GameEventLogger
from engine import colors as c
from engine.ui import console, print_hp_bar
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns

# Room-name to emoji mapping for richer room titles
ROOM_EMOJIS = {
    'forest': '🌲', 'wood': '🌲', 'glade': '🌿', 'grove': '🌿', 'jungle': '🌴',
    'swamp': '🐸', 'marsh': '🐸', 'bog': '☠️', 'cursed': '☠️',
    'castle': '🏰', 'keep': '🏰', 'fort': '🏰', 'citadel': '🏰',
    'tower': '🔮', 'wizard': '🔮', 'spire': '🔮', 'arcane': '🔮',
    'dungeon': '⛓️', 'prison': '⛓️', 'cell': '⛓️', 'tomb': '💀',
    'cave': '🕳️', 'mine': '⛏️', 'pit': '🕳️', 'lair': '🐉',
    'throne': '👑', 'palace': '👑', 'hall': '🏛️', 'royal': '👑',
    'village': '🏠', 'town': '🏘️', 'hamlet': '🏠', 'square': '⛲',
    'market': '🪙', 'bazaar': '🪙', 'shop': '🛒', 'district': '🏙️',
    'temple': '🛕', 'shrine': '🛕', 'church': '⛪', 'cathedral': '⛪',
    'ruins': '🗿', 'ruin': '🗿', 'ancient': '🗿',
}

def _get_room_emoji(room_name: str) -> str:
    n = room_name.lower()
    for keyword, emoji in ROOM_EMOJIS.items():
        if keyword in n:
            return emoji
    return '🗺️'


class GameEngine:
    def __init__(self, save_path: str):
        self.state = GameState()
        self.event_bus = Subject()
        self.event_bus.attach(GameEventLogger())
        self.parser = Parser(self)
        
        if not self.state.load(save_path):
            console.print(c.error("Failed to load game. Make sure the JSON file is correct."))
            self.can_play = False
        else:
            self.can_play = True

    def _get_player_defense(self):
        """Calculate total defense from armor in inventory."""
        total_defense = 0
        for itm in self.state.player.inventory:
            if itm.item_type == "armor" and "defense" in itm.stats:
                total_defense += itm.stats["defense"]
        return total_defense

    def _look(self):
        room = self.state.rooms.get(self.state.player.current_room_id)
        if not room:
            console.print(c.narration("You are suspended in a digital void."))
            return

        emoji = _get_room_emoji(room.name)
        room_title = f"{emoji} {room.name} {emoji}"

        content = Text()
        content.append(f"{room.description}\n\n", style="italic bright_white")

        if room.items:
            from engine.ascii_art import get_item_icon
            item_strs = []
            for i in room.items:
                icon = get_item_icon(i.name)
                item_strs.append(Text.from_markup(f"{icon}{c.item_bold(i.name)}"))
            content.append(Text.from_markup("📦 Items: "))
            content.append(Text(", ").join(item_strs))
            content.append(Text("\n"))

        if room.npcs:
            npc_strs = []
            for n in room.npcs:
                npc_type = getattr(n, 'npc_type', 'neutral')
                if npc_type == 'hostile':
                    npc_strs.append(f"💀 {c.enemy(n.name)} [HP:{c.damage(str(n.hp))}]")
                elif npc_type == 'merchant':
                    npc_strs.append(f"🪙 {c.merchant(n.name)}")
                else:
                    npc_strs.append(f"💬 {c.info(n.name)}")
            content.append(Text.from_markup(f"👥 Here: {', '.join(npc_strs)}\n"))

        if room.exits:
            exit_strs = "  ".join([f"[bold cyan]↪ {e}[/]" for e in room.exits.keys()])
            content.append(Text.from_markup(f"🚪 Exits: {exit_strs}"))
        else:
            content.append(Text.from_markup(c.dim("🚫 There are no obvious exits.")))

        panel = Panel(
            content,
            title=f"[bold green]{room_title}[/]",
            border_style="green",
            expand=False,
            padding=(0, 1),
        )

        from engine.ascii_art import get_room_art
        art = get_room_art(room.name)
        if art:
            art_panel = Panel(Text(art.strip('\n'), style="dim green"), border_style="dim green", padding=(0, 0))
            console.print(Columns([art_panel, panel]))
        else:
            console.print(panel)

        # Render the ASCII map
        from engine.commands import MapCommand
        MapCommand(self).execute([])

    def _check_hostiles(self):
        room = self.state.rooms.get(self.state.player.current_room_id)
        if not room: return
        for npc in room.npcs:
            if getattr(npc, 'npc_type', 'neutral') == 'hostile':
                raw_dmg = getattr(npc, 'damage', 15)
                defense = self._get_player_defense()
                actual_dmg = max(1, raw_dmg - defense)
                self.state.player.hp -= actual_dmg

                from engine.ascii_art import get_npc_art
                art = get_npc_art(npc.name)

                ambush_content = Text()
                ambush_content.append("⚠  AMBUSH! ⚠\n", style="bold red blink")
                ambush_content.append(f"{npc.name} leaps from the shadows!\n", style="italic red")
                ambush_content.append(f"HP: {npc.hp}", style="dim red")
                ambush_panel = Panel(ambush_content, border_style="bold red", expand=False)

                if art:
                    art_panel = Panel(Text(art.strip('\n'), style="bold red"), border_style="red", padding=(0, 0))
                    console.print(Columns([art_panel, ambush_panel]))
                else:
                    console.print(ambush_panel)

                if defense > 0:
                    console.print(
                        f"  💥 {c.enemy(npc.name)} deals {c.damage(str(raw_dmg))} damage! "
                        f"[Armor absorbs {c.defense_color(str(raw_dmg - actual_dmg))}] "
                        f"→ You take {c.damage(str(actual_dmg))}  |  HP: {c.hp_color(max(0, self.state.player.hp))}"
                    )
                else:
                    console.print(
                        f"  💥 {c.enemy(npc.name)} strikes for {c.damage(str(actual_dmg))} damage!  "
                        f"|  HP: {c.hp_color(max(0, self.state.player.hp))}"
                    )

                if self.state.player.hp <= 0:
                    console.print(Rule("[bold red]💀  YOU HAVE BEEN DEFEATED  💀[/]", style="red"))
                    self.can_play = False

    def run(self):
        if not self.can_play:
            return

        console.print(Rule("[bold cyan]⚔   ADVENTURE BEGINS   ⚔[/]", style="cyan"))
        console.print(f"  Welcome, {c.room_name(self.state.player.name)}!")
        console.print(f"  💰 Starting gold: {c.gold(self.state.player.gold)}")
        console.print()
        self._look()
        self._check_hostiles()

        while self.can_play:
            cmd = input(f"\n> ")
            res = self.parser.parse_and_execute(cmd)
            if res == "QUIT":
                console.print(Rule("[dim]Game Over[/]", style="dim"))
                console.print(c.info("Saving game..."))
                self.state.save("save_data.json")
                console.print(c.success("Game saved successfully to save_data.json."))
                console.print(c.success("Thanks for playing!"))
                break
