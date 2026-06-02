class Item:
    def __init__(self, i_id: str, name: str, description: str, item_type: str = "misc", stats: dict = None, value: int = 0):
        self.id = i_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.stats = stats if stats else {}
        self.value = value

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "stats": self.stats,
            "value": self.value
        }
