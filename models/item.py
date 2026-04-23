class Item:
    def __init__(self, i_id: str, name: str, description: str):
        self.id = i_id
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }
