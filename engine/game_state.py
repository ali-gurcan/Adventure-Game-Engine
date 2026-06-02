import json
import os
from models.environment import Room
from models.item import Item
from models.entity import Player, NPC

class GameState:
    def __init__(self):
        self.rooms = {}
        self.items = {}
        self.npcs = {}
        self.player = None
    
    def to_dict(self):
        return {
            "rooms": [r.to_dict() for r in self.rooms.values()],
            "items": [i.to_dict() for i in self.items.values()],
            "npcs": [n.to_dict() for n in self.npcs.values()],
            "player": self.player.to_dict() if self.player else None
        }

    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
        print(f"Game saved successfully to {filepath}.")

    def load(self, filepath: str) -> bool:
        """Load game state from a JSON file."""
        if not os.path.exists(filepath):
            print("Save file not found.")
            return False
            
        with open(filepath, 'r') as f:
            data = json.load(f)

        return self.load_from_dict(data)

    def load_from_dict(self, data: dict) -> bool:
        """Load game state from a dictionary (used by both file loading and LLM generation)."""
        try:
            self.items = {i['id']: Item(i['id'], i['name'], i['description'], i.get('item_type', 'misc'), i.get('stats', {})) for i in data.get('items', [])}
            self.npcs = {n['id']: NPC(n['id'], n['name'], n['description'], n.get('dialogue', ''), n.get('npc_type', 'neutral'), n.get('damage', 0), n.get('hp', 100)) for n in data.get('npcs', [])}
            
            self.rooms = {}
            for r_data in data.get('rooms', []):
                room = Room(r_data['id'], r_data['name'], r_data['description'], r_data.get('x', 0), r_data.get('y', 0))
                room.exits = r_data.get('exits', {})
                for item_id in r_data.get('item_ids', []):
                    if item_id in self.items:
                        room.add_item(self.items[item_id])
                for npc_id in r_data.get('npc_ids', []):
                    if npc_id in self.npcs:
                        room.add_npc(self.npcs[npc_id])
                self.rooms[room.id] = room

            p_data = data.get('player')
            if p_data:
                self.player = Player(p_data['id'], p_data['name'], p_data['description'], p_data.get('current_room_id'), p_data.get('hp', 100), p_data.get('previous_room_id'))
                for item_id in p_data.get('inventory', []):
                    if item_id in self.items:
                        self.player.inventory.append(self.items[item_id])
            return True
        except (KeyError, TypeError) as e:
            print(f"Error loading game data: {e}")
            return False
