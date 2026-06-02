import json
import os
from models.environment import Room
from models.item import Item
from models.entity import Player, NPC
from models.quest import Quest

class GameState:
    def __init__(self):
        self.rooms = {}
        self.items = {}
        self.npcs = {}
        self.quests = {}
        self.player = None
    
    def to_dict(self):
        return {
            "rooms": [r.to_dict() for r in self.rooms.values()],
            "items": [i.to_dict() for i in self.items.values()],
            "npcs": [n.to_dict() for n in self.npcs.values()],
            "quests": [q.to_dict() for q in self.quests.values()],
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
            self.items = {i['id']: Item(i['id'], i['name'], i['description'], i.get('item_type', 'misc'), i.get('stats', {}), i.get('value', 0)) for i in data.get('items', [])}
            self.npcs = {n['id']: NPC(n['id'], n['name'], n['description'], n.get('dialogue', ''), n.get('npc_type', 'neutral'), n.get('damage', 0), n.get('hp', 100)) for n in data.get('npcs', [])}
            
            # Load quests
            self.quests = {}
            for q_data in data.get('quests', []):
                quest = Quest(
                    q_id=q_data['id'],
                    name=q_data['name'],
                    description=q_data['description'],
                    quest_type=q_data['quest_type'],
                    target_id=q_data['target_id'],
                    giver_npc_id=q_data['giver_npc_id'],
                    reward_gold=q_data.get('reward_gold', 20),
                    deliver_to=q_data.get('deliver_to'),
                    status=q_data.get('status', 'available')
                )
                self.quests[quest.id] = quest

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
                self.player = Player(p_data['id'], p_data['name'], p_data['description'], p_data.get('current_room_id'), p_data.get('hp', 100), p_data.get('previous_room_id'), p_data.get('gold', 50))
                self.player.active_quests = p_data.get('active_quests', [])
                self.player.completed_quests = p_data.get('completed_quests', [])
                for item_id in p_data.get('inventory', []):
                    if item_id in self.items:
                        self.player.inventory.append(self.items[item_id])
            return True
        except (KeyError, TypeError) as e:
            print(f"Error loading game data: {e}")
            return False
