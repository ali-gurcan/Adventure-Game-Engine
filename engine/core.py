from engine.game_state import GameState
from engine.parser import Parser
from engine.events import Subject, GameEventLogger

class GameEngine:
    def __init__(self, save_path: str):
        self.state = GameState()
        self.event_bus = Subject()
        self.event_bus.attach(GameEventLogger())
        self.parser = Parser(self)
        
        if not self.state.load(save_path):
            print("Failed to load game. Make sure the JSON file is correct.")
            self.can_play = False
        else:
            self.can_play = True

    def _look(self):
        room = self.state.rooms.get(self.state.player.current_room_id)
        if not room:
            print("You are suspended in a digital void.")
            return
        print(f"\n--- {room.name} ---")
        print(room.description)
        if room.items:
            print("You see:", ", ".join([i.name for i in room.items]))
        if room.npcs:
            print("Characters here:", ", ".join([f"{n.name} (HP:{n.hp})" for n in room.npcs]))
        if room.exits:
            print("Exits:", ", ".join(room.exits.keys()))
        else:
            print("There are no obvious exits.")

    def _check_hostiles(self):
        room = self.state.rooms.get(self.state.player.current_room_id)
        if not room: return
        for npc in room.npcs:
            if getattr(npc, 'npc_type', 'neutral') == 'hostile':
                dmg = getattr(npc, 'damage', 15)
                self.state.player.hp -= dmg
                print(f"\n!!! AMBUSH !!!")
                print(f"The {npc.name} attacks you dealing {dmg} damage! (Your HP: {max(0, self.state.player.hp)})")
                if self.state.player.hp <= 0:
                    print("You have been defeated... GAME OVER.")
                    self.can_play = False

    def run(self):
        if not self.can_play:
            return
            
        print(f"\nWelcome to the Adventure, {self.state.player.name}!")
        self._look()
        self._check_hostiles()
        
        while self.can_play:
            cmd = input("\n> ")
            res = self.parser.parse_and_execute(cmd)
            if res == "QUIT":
                print("Saving game...")
                self.state.save("save_data.json")
                print("Thanks for playing!")
                break
