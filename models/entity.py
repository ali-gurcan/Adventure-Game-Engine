from abc import ABC, abstractmethod
from typing import Dict, Any

class Entity(ABC):
    def __init__(self, e_id: str, name: str, description: str):
        self.id = e_id
        self.name = name
        self.description = description
        
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class Player(Entity):
    def __init__(self, e_id: str, name: str, description: str, current_room_id: str = None):
        super().__init__(e_id, name, description)
        self.inventory = []
        self.current_room_id = current_room_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "Player",
            "name": self.name,
            "description": self.description,
            "inventory": [item.id for item in self.inventory],
            "current_room_id": self.current_room_id
        }

class NPC(Entity):
    def __init__(self, e_id: str, name: str, description: str, dialogue: str = ""):
        super().__init__(e_id, name, description)
        self.dialogue = dialogue

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": "NPC",
            "name": self.name,
            "description": self.description,
            "dialogue": self.dialogue
        }
