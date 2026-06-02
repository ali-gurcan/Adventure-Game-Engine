from engine.game_state import GameState
from engine.parser import Parser
from engine.events import Subject, GameEventLogger
from engine import colors as c

class GameEngine:
    def __init__(self, save_path: str):
        self.state = GameState()
        self.event_bus = Subject()
        self.event_bus.attach(GameEventLogger())
        self.parser = Parser(self)
        
        if not self.state.load(save_path):
            print(c.error("Failed to load game. Make sure the JSON file is correct."))
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
            print(c.narration("You are suspended in a digital void."))
            return
        print(f"\n--- {c.room_name(room.name)} ---")
        print(c.narration(room.description))
        if room.items:
            item_names = ", ".join([c.item(i.name) for i in room.items])
            print(f"You see: {item_names}")
        if room.npcs:
            npc_strs = []
            for n in room.npcs:
                npc_type = getattr(n, 'npc_type', 'neutral')
                if npc_type == 'hostile':
                    npc_strs.append(f"{c.enemy(n.name)} (HP:{c.damage(str(n.hp))})")
                elif npc_type == 'merchant':
                    npc_strs.append(f"{c.merchant(n.name)} 🪙")
                else:
                    npc_strs.append(f"{c.info(n.name)} (HP:{n.hp})")
            print(f"Characters here: {', '.join(npc_strs)}")
        if room.exits:
            exit_strs = ", ".join([c.bold(e) for e in room.exits.keys()])
            print(f"Exits: {exit_strs}")
        else:
            print(c.dim("There are no obvious exits."))
        
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
                print(f"\n{c.error('!!! AMBUSH !!!')}")
                if defense > 0:
                    print(f"The {c.enemy(npc.name)} attacks you dealing {c.damage(str(raw_dmg))} damage! "
                          f"(Armor absorbs {c.defense_color(str(raw_dmg - actual_dmg))}. "
                          f"You take {c.damage(str(actual_dmg))}. Your HP: {c.hp_color(max(0, self.state.player.hp))})")
                else:
                    print(f"The {c.enemy(npc.name)} attacks you dealing {c.damage(str(actual_dmg))} damage! (Your HP: {c.hp_color(max(0, self.state.player.hp))})")
                if self.state.player.hp <= 0:
                    print(c.error("You have been defeated... GAME OVER."))
                    self.can_play = False

    def run(self):
        if not self.can_play:
            return
            
        print(f"\n{c.bold('Welcome to the Adventure')}, {c.room_name(self.state.player.name)}!")
        print(f"  💰 Starting gold: {c.gold(self.state.player.gold)}")
        self._look()
        self._check_hostiles()
        
        while self.can_play:
            cmd = input(f"\n{c.BOLD_CYAN}> {c.RESET}")
            res = self.parser.parse_and_execute(cmd)
            if res == "QUIT":
                print(c.info("Saving game..."))
                self.state.save("save_data.json")
                print(c.success("Thanks for playing!"))
                break
