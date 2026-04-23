from engine.commands import GoCommand, LookCommand, TakeCommand, InventoryCommand

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
            "i": InventoryCommand(engine_sys)
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
            print("I don't understand that command. Try 'look', 'go <direction>', 'take <item>', or 'inventory'.")
