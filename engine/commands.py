from abc import ABC, abstractmethod

class Command(ABC):
    def __init__(self, engine_sys):
        self.engine_sys = engine_sys

    @abstractmethod
    def execute(self, args: list):
        pass

class GoCommand(Command):
    def execute(self, args: list):
        if not args:
            print("Go where?")
            return
        direction = args[0]
        state = self.engine_sys.state
        player = state.player
        current_room = state.rooms.get(player.current_room_id)
        
        if current_room and direction in current_room.exits:
            player.previous_room_id = current_room.id # Store for escape
            next_room_id = current_room.exits[direction]
            player.current_room_id = next_room_id
            self.engine_sys.event_bus.notify("room_enter", {"room_id": next_room_id})
            print(f"You go {direction}.")
            self.engine_sys._look()
            self.engine_sys._check_hostiles() # Check encounters
        else:
            print("You can't go that way.")

class LookCommand(Command):
    def execute(self, args: list):
        self.engine_sys._look()

class TakeCommand(Command):
    def execute(self, args: list):
        if not args:
            print("Take what?")
            return
        item_name = " ".join(args).lower()
        room = self.engine_sys.state.rooms.get(self.engine_sys.state.player.current_room_id)
        
        for item in list(room.items):
            if item.name.lower() == item_name:
                room.items.remove(item)
                self.engine_sys.state.player.inventory.append(item)
                print(f"You picked up the {item.name}.")
                self.engine_sys.event_bus.notify("item_taken", {"item_id": item.id})
                return
        print("I don't see that here.")

class InventoryCommand(Command):
    def execute(self, args: list):
        player = self.engine_sys.state.player
        print(f"HP: {player.hp}")
        if not player.inventory:
            print("Your inventory is empty.")
        else:
            print("You are carrying:")
            for item in player.inventory:
                print(f"- {item.name}")

class EscapeCommand(Command):
    def execute(self, args: list):
        player = self.engine_sys.state.player
        if player.previous_room_id and player.previous_room_id in self.engine_sys.state.rooms:
            temp = player.current_room_id
            player.current_room_id = player.previous_room_id
            player.previous_room_id = temp
            print("You hastily escape back to where you came from!")
            self.engine_sys.event_bus.notify("room_enter", {"room_id": player.current_room_id})
            self.engine_sys._look()
            self.engine_sys._check_hostiles()
        else:
            print("You have nowhere to escape to!")

class InspectCommand(Command):
    def execute(self, args: list):
        if not args:
            print("Inspect what?")
            return
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)
        
        # Check inventory first, then room
        items_to_check = player.inventory + room.items
        for item in items_to_check:
            if item.name.lower() == target:
                print(f"--- {item.name} ---")
                print(item.description)
                if item.stats:
                    if "damage" in item.stats:
                        print(f"Damage: {item.stats['damage']}")
                    if "heal" in item.stats:
                        print(f"Heals: {item.stats['heal']} HP")
                return
        print("You don't see that to inspect.")

class AttackCommand(Command):
    def execute(self, args: list):
        if not args:
            print("Attack who?")
            return
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)
        
        npc_target = None
        for n in room.npcs:
            if n.name.lower() == target:
                npc_target = n
                break
                
        if not npc_target:
            print("They aren't here.")
            return

        # Calculate player damage (find highest weapon)
        dmg = 5 # base punch damage
        for item in player.inventory:
            if item.item_type == "weapon" and item.stats.get("damage", 0) > dmg:
                dmg = item.stats["damage"]

        npc_target.hp -= dmg
        print(f"You attack {npc_target.name} for {dmg} damage! (Enemy HP: {max(0, npc_target.hp)})")
        
        if npc_target.hp <= 0:
            print(f"You defeated {npc_target.name}!")
            room.npcs.remove(npc_target)
            self.engine_sys.event_bus.notify("npc_defeated", {"npc_id": npc_target.id})
        else:
            if npc_target.npc_type == "hostile":
                ret_dmg = getattr(npc_target, 'damage', 10)
                player.hp -= ret_dmg
                print(f"{npc_target.name} retaliates for {ret_dmg} damage! (Your HP: {max(0, player.hp)})")
                if player.hp <= 0:
                    print("You have been defeated... GAME OVER.")
                    self.engine_sys.can_play = False

class UseCommand(Command):
    def execute(self, args: list):
        if not args:
            print("Use what?")
            return
        
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        
        for item in list(player.inventory):
            if item.name.lower() == target:
                if getattr(item, 'item_type', 'misc') == "consumable":
                    heal_amount = getattr(item, 'stats', {}).get("heal", 0)
                    if heal_amount > 0:
                        player.hp = min(100, player.hp + heal_amount)
                        player.inventory.remove(item)
                        print(f"You consumed the {item.name}. It healed you for {heal_amount} HP! (Current HP: {player.hp})")
                    else:
                        print(f"You used the {item.name}, but nothing happened.")
                    return
                else:
                    print(f"You can't consume or use the {item.name} that way.")
                    return
                    
        print("You don't have that item in your inventory. Did you 'take' it first?")
