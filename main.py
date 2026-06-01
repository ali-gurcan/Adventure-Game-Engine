import sys
import os
import json

# Add the project root to sys.path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from editor.cli_editor import CLIEditor
from engine.core import GameEngine
from engine.world_generator import WorldGenerator

def print_help():
    print("==========================================")
    print("   TEXT-BASED ADVENTURE GAME ENGINE       ")
    print("==========================================")
    print("Usage:")
    print("  python main.py editor                  --> Launch the Game World Builder")
    print("  python main.py play <savefile.json>    --> Play a created adventure")
    print("  python main.py generate                --> Generate a new world with AI and play")
    print("==========================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
        
    mode = sys.argv[1].lower()
    
    if mode == "editor":
        editor = CLIEditor()
        editor.run()
    elif mode == "play":
        if len(sys.argv) < 3:
            print("Please specify a world/save file to load.")
            print("Example: python main.py play world.json")
            sys.exit(1)
        engine = GameEngine(sys.argv[2])
        engine.run()
    elif mode == "generate":
        # Generate a new world using Ollama LLM
        generator = WorldGenerator()
        world_data = generator.generate()

        # Save the generated world to a file for reference
        generated_path = os.path.join(os.path.dirname(__file__), "generated_world.json")
        with open(generated_path, 'w') as f:
            json.dump(world_data, f, indent=4)
        print(f"\n📄 Generated world saved to: {generated_path}")

        # Load and play the generated world
        engine = GameEngine.__new__(GameEngine)
        from engine.game_state import GameState
        from engine.parser import Parser
        from engine.events import Subject, GameEventLogger

        engine.state = GameState()
        engine.event_bus = Subject()
        engine.event_bus.attach(GameEventLogger())
        engine.parser = Parser(engine)

        if engine.state.load_from_dict(world_data):
            engine.can_play = True
            engine.run()
        else:
            print("Failed to load generated world. Try again or use 'play' with a static file.")
    else:
        print_help()
