import os
from engine.game_state import GameState
from editor.factory import GameFactory

class CLIEditor:
    def __init__(self):
        self.state = GameState()

    def load_if_exists(self, filepath):
        if os.path.exists(filepath):
            print(f"Loading existing state from {filepath}...")
            self.state.load(filepath)

    def run(self):
        print("\n--- Game Editor ---")
        
        load_choice = input("Do you want to load an existing world to edit? (y/N): ")
        if load_choice.lower() == 'y':
            file_path = input("Enter path (e.g. save_data.json): ")
            self.load_if_exists(file_path)
            
        while True:
            print("\nOptions: [1] Create Room, [2] Create Item, [3] Assign Item to Room, [4] Set Room Exit, [5] Create NPC, [6] Setup Player, [7] Save Game, [8] List Elements, [9] Exit Editor")
            choice = input("Select an option: ")
            
            if choice == "1":
                name = input("Room name: ")
                desc = input("Room description: ")
                room = GameFactory.create_room(name, desc)
                self.state.rooms[room.id] = room
                print(f"Room created! ID: {room.id}")
            elif choice == "2":
                name = input("Item name: ")
                desc = input("Item description: ")
                item = GameFactory.create_item(name, desc)
                self.state.items[item.id] = item
                print(f"Item created! ID: {item.id}")
            elif choice == "3":
                r_id = input("Room ID: ")
                i_id = input("Item ID: ")
                if r_id in self.state.rooms and i_id in self.state.items:
                    self.state.rooms[r_id].add_item(self.state.items[i_id])
                    print("Item assigned to room.")
                else:
                    print("Invalid IDs.")
            elif choice == "4":
                r_id1 = input("From Room ID: ")
                direction = input("Direction (e.g. north, south): ")
                r_id2 = input("To Room ID: ")
                if r_id1 in self.state.rooms and r_id2 in self.state.rooms:
                    self.state.rooms[r_id1].add_exit(direction, r_id2)
                    print(f"Exit {direction} created.")
                else:
                    print("One or both room IDs are invalid.")
            elif choice == "5":
                name = input("NPC Name: ")
                desc = input("NPC Description: ")
                dialogue = input("NPC Dialogue: ")
                r_id = input("Room ID to spawn in: ")
                if r_id in self.state.rooms:
                    npc = GameFactory.create_npc(name, desc, dialogue)
                    self.state.npcs[npc.id] = npc
                    self.state.rooms[r_id].add_npc(npc)
                    print(f"NPC created and spawned in room! ID: {npc.id}")
                else:
                    print("Invalid Room ID.")
            elif choice == "6":
                name = input("Player name: ")
                r_id = input("Starting Room ID: ")
                if r_id in self.state.rooms:
                    self.state.player = GameFactory.create_player(name, "The Hero", r_id)
                    print("Player setup complete.")
                else:
                    print("Invalid Room ID.")
            elif choice == "7":
                filepath = input("Save path (e.g. world.json): ")
                self.state.save(filepath)
            elif choice == "8":
                print("\n--- Current World Data ---")
                print("Rooms:")
                for r in self.state.rooms.values():
                    print(f"  {r.id}: {r.name}")
                print("Items:")
                for i in self.state.items.values():
                    print(f"  {i.id}: {i.name}")
                print("NPCs:")
                for n in self.state.npcs.values():
                    print(f"  {n.id}: {n.name}")
                if self.state.player:
                    print(f"Player: {self.state.player.name} in Room {self.state.player.current_room_id}")
            elif choice == "9":
                break
            else:
                print("Invalid choice.")
