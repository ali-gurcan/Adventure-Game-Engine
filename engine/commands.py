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
            next_room_id = current_room.exits[direction]
            player.current_room_id = next_room_id
            self.engine_sys.event_bus.notify("room_enter", {"room_id": next_room_id})
            print(f"You go {direction}.")
            self.engine_sys._look()
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
        if not player.inventory:
            print("Your inventory is empty.")
        else:
            print("You are carrying:")
            for item in player.inventory:
                print(f"- {item.name}: {item.description}")
