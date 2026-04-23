import sys
import os

# Add the project root to sys.path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from editor.cli_editor import CLIEditor
from engine.core import GameEngine

def print_help():
    print("==========================================")
    print("   TEXT-BASED ADVENTURE GAME ENGINE       ")
    print("==========================================")
    print("Usage:")
    print("  python main.py editor                  --> Launch the Game World Builder")
    print("  python main.py play <savefile.json>    --> Play a created adventure")
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
    else:
        print_help()
