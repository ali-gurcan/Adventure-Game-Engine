# Text-Based Adventure Game Engine

A robust, object-oriented, command-line RPG engine developed in Python. It features a scalable runtime system for interactive storytelling built with the Command, Factory, and Observer design patterns.

## Features
- **Object-Oriented Design**: Clean entity inheritance (Entity -> Player/NPC), aggregation between rooms and items.
- **Dynamic Combat & Stats**: Player HP management, hostile NPC ambushes, item statistics (damage, healing).
- **Design Patterns Applied**:
  - `Command Pattern`: Processes natural language input parsing (`go`, `take`, `use`, `attack`).
  - `Factory Pattern`: Generates world instances seamlessly through the game editor.
  - `Observer Pattern`: Triggers background events and scene updates.
- **Game Editor**: Built-in CLI authoring tool to generate and link game rooms, spawn items and NPCs without writing code.
- **JSON Serialization**: Full save & load functionality to securely preserve your state.

## Installation
Ensure you have Python 3 installed. No external package management or `requirements.txt` are needed since the project is built using powerful Python Standard Libraries.

```bash
# Clone the repository (If you haven't already locally)
git clone https://github.com/ali-gurcan/Adventure-Game-Engine.git
cd Adventure-Game-Engine
```

## How to Play

Start the runtime engine by loading a JSON world file instance:
```bash
# Example with the included fantasy map:
python3 main.py play test_world2.json
```

**In-Game Commands:**
- `look` — Observe your current surroundings, seeing exits, items, and characters.
- `go <direction>` or `move <direction>` — Move between rooms (e.g., `go north`, `go east`).
- `take <item>` or `get <item>` — Pick an item up from the ground to put in your inventory.
- `inventory` or `inv` or `i` — Check the items currently in your bag and view your HP limit.
- `inspect <item>` or `examine <item>` — Look closely at an item in the room or in your inventory to see its stats (Damage numbers or HP healing yield).
- `attack <npc_name>` — Engage in combat. It automatically uses your strongest weapon from your inventory.
- `use <item>` / `eat <item>` / `drink <item>` — Consume a consumable item to restore HP (e.g., `eat apple`).
- `escape` — Hastily retreat to the previous room you came from if things go bad.
- `quit` or `exit` — Saves the current game state to a JSON file and gracefully safely exits the game.

## World Builder (Game Editor)

You can craft your own unique map files and adventures entirely through the terminal. Launch the editor using:

```bash
python3 main.py editor
```

The Editor provides a simple menu to guide you through:
1. Creating Rooms, Items, and NPCs.
2. Linking Rooms via directions (North, South, etc.).
3. Setting enemy Logic (neutral vs hostile, setting their HP and Damage points).
4. Exporting everything into a `<world_name>.json` file, which can then be played using the `play` command.

---
*Developed as a Term Project for CSE 444 Software Engineering II*
