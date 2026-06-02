from abc import ABC, abstractmethod
from typing import Dict, Any

class Entity(ABC):
    def __init__(self, e_id: str, name: str, description: str, hp: int = 100):
        self.id = e_id
        self.name = name
        self.description = description
        self.hp = hp
        
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class Player(Entity):
    def __init__(self, e_id: str, name: str, description: str, current_room_id: str = None, hp: int = 100, previous_room_id: str = None, gold: int = 50):
        super().__init__(e_id, name, description, hp)
        self.inventory = []
        self.current_room_id = current_room_id
        self.previous_room_id = previous_room_id
        self.gold = gold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "Player",
            "name": self.name,
            "description": self.description,
            "hp": self.hp,
            "gold": self.gold,
            "inventory": [item.id for item in self.inventory],
            "current_room_id": self.current_room_id,
            "previous_room_id": self.previous_room_id
        }

class NPC(Entity):
    def __init__(self, e_id: str, name: str, description: str, dialogue: str = "", npc_type: str = "neutral", damage: int = 0, hp: int = 100):
        super().__init__(e_id, name, description, hp)
        self.dialogue = dialogue
        self.npc_type = npc_type
        self.damage = damage

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "NPC",
            "name": self.name,
            "description": self.description,
            "hp": self.hp,
            "dialogue": self.dialogue,
            "npc_type": self.npc_type,
            "damage": self.damage
        }
