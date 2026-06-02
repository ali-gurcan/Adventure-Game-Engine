# Text-Based Adventure Game Engine

A robust, object-oriented, command-line RPG engine developed in Python. It features a scalable runtime system for interactive storytelling built with the Command, Factory, and Observer design patterns.

## 🚀 Key Features
- **Object-Oriented Design**: Clean entity inheritance (Entity -> Player/NPC), aggregation between rooms and items.
- **Dynamic AI World Generation**: Seamless integration with **Ollama** to procedurally generate dark fantasy, gothic, or high fantasy themed worlds, including NPC lore, dialogues, and quest narratives.
- **Rich Terminal UI**: Beautiful, vibrant terminal interfaces powered by the `rich` library. Features dynamic **ASCII Arts**, emoji icons, stylized inventory tables, and a mini-map layout.
- **Advanced Combat & Economy**:
  - Tactical combat with weapon damage and armor defense calculations.
  - Interactive economy system allowing you to trade gold with merchants.
- **Dynamic Quest System**: Procedurally generated Kill, Collect, and Deliver quests uniquely tailored to each game session.
- **Interactive NPC Chat**: Talk to intelligent NPCs whose behavior changes based on their role (hostile, merchant, or neutral) using LLM-driven responses.
- **Game Editor**: Built-in CLI authoring tool to generate and link game rooms, spawn items and NPCs manually.
- **JSON Serialization**: Full save & load functionality to securely preserve your state.

## ⚙️ Installation & Requirements

Ensure you have Python 3 installed. The game utilizes the `rich` library for rendering the UI and requires `Ollama` if you wish to use the AI World Generator.

```bash
# 1. Clone the repository
git clone https://github.com/ali-gurcan/Adventure-Game-Engine.git
cd Adventure-Game-Engine

# 2. Install Python dependencies
pip install rich

# 3. (Optional) Install Ollama for AI generation
# Follow instructions at https://ollama.com/
```

## 🧠 AI World Generation (Ollama Manual)

To unlock the procedural generation capabilities (`make generate`), you must run a local Large Language Model via **Ollama**.

1. **Download & Install:** Visit [Ollama.com](https://ollama.com/) and install it for your OS.
2. **Setup the Required Model:** The engine is specifically fine-tuned for Llama 3.1 8B. It expects the following specific model (or an equivalent) to be available in your local Ollama library:
   - **Model Name:** `Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M`
   - **ID:** `d4d7942fcda0`

   *(If you are pulling a fresh, standard model instead, you can run `ollama run llama3.1` in your terminal).*
3. **Changing the Model:** If you don't have the exact custom GGUF model mentioned above, you can change the AI model the game points to. Open `engine/world_generator.py` and modify line 24:
   ```python
   DEFAULT_MODEL = "llama3.1" # Change this to the model name you pulled
   ```
4. **Running the Game:** Ensure the Ollama app is open in the background (running on `http://localhost:11434`), then run `make generate`. The engine will connect locally to Ollama and dynamically generate your map!


## 🎮 How to Play

You can use the provided `Makefile` to quickly start the game, or run the Python scripts manually.

```bash
# Generate a completely new dynamic world using AI
make generate

# Or manually:
python3 main.py generate
```

```bash
# Play an existing save file or base template
make play

# Or manually:
python3 main.py play test_world2.json
```

## 📜 In-Game Commands

**Exploration & Environment:**
- `look` — Observe your current surroundings, seeing exits, items, characters, and beautiful ASCII art.
- `map` — View the local 2D ASCII map of discovered rooms.
- `go <direction>` / `move <direction>` — Move between rooms (e.g., `go north`, `go east`).
- `escape` — Hastily retreat to the previous room you came from if things go bad in an ambush.

**Items & Inventory:**
- `take <item>` / `get <item>` — Pick an item up from the ground to put in your inventory.
- `inventory` / `inv` / `i` — Open your stylized backpack to view your items, stats, and total gold.
- `inspect <item>` / `examine <item>` — Look closely at an item to see its detailed stats (Damage, Heal, Defense, Value).
- `use <item>` / `eat <item>` / `drink <item>` — Consume a consumable item to restore HP.

**NPCs & Interaction:**
- `talk <npc_name>` — Initiate a dynamic LLM-driven chat with an NPC.
- `quests` — View your Quest Journal, displaying active and completed objectives.
- `attack <npc_name>` — Engage in tactical combat. Automatically calculates your total damage and defense.

**Trading & Economy:**
- `shop` — View the list of items a merchant has for sale in the current room.
- `buy <item_name>` — Purchase an item from a merchant using your gold.
- `sell <item_name>` — Sell an item from your inventory to a merchant for half its value.

**System Commands:**
- `quit` / `exit` — Saves the current game state to `save_data.json` and gracefully exits the game.

## 🛠️ World Builder (Game Editor)

You can craft your own unique map files and adventures entirely through the terminal. Launch the editor using:

```bash
make editor
# or python3 main.py editor
```

The Editor provides a simple menu to guide you through:
1. Creating Rooms, Items, and NPCs.
2. Linking Rooms via directions (North, South, etc.).
3. Setting enemy Logic (neutral vs hostile, setting their HP and Damage points).
4. Exporting everything into a `<world_name>.json` file.

## 🧪 Testing

The engine includes a full automated test scenario that spins up the AI Generator, navigates the map, completes quests, buys items, and tests all commands automatically.

```bash
make test
# or python3 auto_test.py
```

---
*Developed as a Term Project for CSE 444 Software Engineering II*
