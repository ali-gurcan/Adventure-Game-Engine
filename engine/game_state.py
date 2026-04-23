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
        if not os.path.exists(filepath):
            print("Save file not found.")
            return False
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Restore Items and NPCs first
        self.items = {i['id']: Item(i['id'], i['name'], i['description']) for i in data.get('items', [])}
        self.npcs = {n['id']: NPC(n['id'], n['name'], n['description'], n.get('dialogue', '')) for n in data.get('npcs', [])}
        
        # Restore Rooms and assign objects
        self.rooms = {}
        for r_data in data.get('rooms', []):
            room = Room(r_data['id'], r_data['name'], r_data['description'])
            room.exits = r_data.get('exits', {})
            for item_id in r_data.get('item_ids', []):
                if item_id in self.items:
                    room.add_item(self.items[item_id])
            for npc_id in r_data.get('npc_ids', []):
                if npc_id in self.npcs:
                    room.add_npc(self.npcs[npc_id])
            self.rooms[room.id] = room

        # Restore Player
        p_data = data.get('player')
        if p_data:
            self.player = Player(p_data['id'], p_data['name'], p_data['description'], p_data.get('current_room_id'))
            for item_id in p_data.get('inventory', []):
                if item_id in self.items:
                    self.player.inventory.append(self.items[item_id])
        return True
