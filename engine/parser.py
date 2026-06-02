from engine.commands import (GoCommand, LookCommand, TakeCommand, InventoryCommand,
                              EscapeCommand, InspectCommand, AttackCommand, UseCommand,
                              MapCommand, TalkCommand, BuyCommand, SellCommand, ShopCommand,
                              QuestsCommand)

class Parser:
    def __init__(self, engine_sys):
        self.engine_sys = engine_sys
        self.commands = {
            "go": GoCommand(engine_sys),
            "move": GoCommand(engine_sys),
            "look": LookCommand(engine_sys),
            "take": TakeCommand(engine_sys),
            "get": TakeCommand(engine_sys),
            "inventory": InventoryCommand(engine_sys),
            "inv": InventoryCommand(engine_sys),
            "i": InventoryCommand(engine_sys),
            "escape": EscapeCommand(engine_sys),
            "inspect": InspectCommand(engine_sys),
            "examine": InspectCommand(engine_sys),
            "attack": AttackCommand(engine_sys),
            "hit": AttackCommand(engine_sys),
            "use": UseCommand(engine_sys),
            "eat": UseCommand(engine_sys),
            "drink": UseCommand(engine_sys),
            "map": MapCommand(engine_sys),
            "talk": TalkCommand(engine_sys),
            "chat": TalkCommand(engine_sys),
            "buy": BuyCommand(engine_sys),
            "sell": SellCommand(engine_sys),
            "shop": ShopCommand(engine_sys),
            "wares": ShopCommand(engine_sys),
            "quests": QuestsCommand(engine_sys),
            "quest": QuestsCommand(engine_sys),
            "journal": QuestsCommand(engine_sys),
        }

    def parse_and_execute(self, input_str: str):
        parts = input_str.strip().split()
        if not parts:
            return
        cmd_keyword = parts[0].lower()
        args = parts[1:]
        
        if cmd_keyword in ["quit", "exit"]:
            return "QUIT"
            
        cmd = self.commands.get(cmd_keyword)
        if cmd:
            cmd.execute(args)
        else:
            print("I don't understand that command. Try 'look', 'go', 'take', 'use', 'escape', 'inspect', 'attack', 'talk', 'buy', 'sell', 'shop', or 'quests'.")
