class Room:
    def __init__(self, r_id: str, name: str, description: str):
        self.id = r_id
        self.name = name
        self.description = description
        self.exits = {} # Format: {"north": "room_id"}
        self.items = []
        self.npcs = []

    def add_exit(self, direction: str, room_id: str):
        self.exits[direction] = room_id

    def add_item(self, item):
        self.items.append(item)

    def add_npc(self, npc):
        self.npcs.append(npc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "exits": self.exits,
            "item_ids": [item.id for item in self.items],
            "npc_ids": [npc.id for npc in self.npcs]
        }
