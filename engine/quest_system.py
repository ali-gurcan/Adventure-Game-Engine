from engine import colors as c
from engine.ui import console

class QuestSystem:
    """Manages checking and completing quests."""

    @staticmethod
    def check_quest_completion(engine_sys, event_type: str, target_id: str):
        """Shared helper: checks if any active quest is completed by this event."""
        player = engine_sys.state.player
        quests = engine_sys.state.quests

        for q_id in list(player.active_quests):
            quest = quests.get(q_id)
            if not quest or quest.status != 'active':
                continue

            completed = False
            if quest.quest_type == 'kill' and event_type == 'npc_killed' and quest.target_id == target_id:
                completed = True
            elif quest.quest_type == 'collect' and event_type == 'item_taken' and quest.target_id == target_id:
                completed = True
            # 'deliver' is handled separately in TalkCommand/Dialogue

            if completed:
                QuestSystem.complete_quest(player, quest)

    @staticmethod
    def complete_quest(player, quest):
        """Marks a quest as completed and grants rewards."""
        quest.status = 'completed'
        if quest.id in player.active_quests:
            player.active_quests.remove(quest.id)
        if quest.id not in player.completed_quests:
            player.completed_quests.append(quest.id)
        player.gold += quest.reward_gold
        
        console.print(f"\n[bold green]✨ QUEST COMPLETED![/] [bold white]{quest.name}[/]")
        console.print(f"  [italic white]{quest.description}[/]")
        console.print(f"  💰 Reward: [bold yellow]{quest.reward_gold}g[/]")
