class Quest:
    """
    Represents a quest/mission in the game.
    Quest types:
      - 'kill': Defeat a specific NPC (target_id = npc_id)
      - 'collect': Pick up a specific item (target_id = item_id)
      - 'deliver': Bring a specific item to a specific NPC (target_id = item_id, deliver_to = npc_id)
    """

    def __init__(self, q_id: str, name: str, description: str, quest_type: str,
                 target_id: str, giver_npc_id: str, reward_gold: int = 20,
                 deliver_to: str = None, status: str = "available"):
        self.id = q_id
        self.name = name
        self.description = description
        self.quest_type = quest_type        # "kill" | "collect" | "deliver"
        self.target_id = target_id          # NPC or Item ID to target
        self.deliver_to = deliver_to        # Only for "deliver": target NPC ID
        self.giver_npc_id = giver_npc_id    # NPC who gives this quest
        self.reward_gold = reward_gold
        self.status = status                # "available" | "active" | "completed"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "quest_type": self.quest_type,
            "target_id": self.target_id,
            "deliver_to": self.deliver_to,
            "giver_npc_id": self.giver_npc_id,
            "reward_gold": self.reward_gold,
            "status": self.status
        }
