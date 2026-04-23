import uuid
from models.environment import Room
from models.item import Item
from models.entity import NPC, Player

class GameFactory:
    @staticmethod
    def create_room(name: str, description: str) -> Room:
        r_id = f"room_{uuid.uuid4().hex[:8]}"
        return Room(r_id, name, description)

    @staticmethod
    def create_item(name: str, description: str) -> Item:
        i_id = f"item_{uuid.uuid4().hex[:8]}"
        return Item(i_id, name, description)

    @staticmethod
    def create_npc(name: str, description: str, dialogue: str, npc_type: str="neutral", damage: int=0, hp: int=100) -> NPC:
        n_id = f"npc_{uuid.uuid4().hex[:8]}"
        return NPC(n_id, name, description, dialogue, npc_type, damage, hp)
        
    @staticmethod
    def create_player(name: str, description: str, room_id: str) -> Player:
        p_id = f"player_{uuid.uuid4().hex[:8]}"
        return Player(p_id, name, description, room_id, hp=100)
