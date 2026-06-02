# Software Requirements Specification (SRS) & Use Cases

## 1. Introduction
The Adventure Game Engine is a text-based, object-oriented runtime environment developed in Python. It provides an interactive command-line RPG experience with dynamic world generation via Ollama, a tactical combat system, and an integrated World Builder (Game Editor).

## 2. Functional Requirements
- **F-1 (Movement):** The player shall be able to navigate between connected rooms using directional commands (`go north`, `go east`).
- **F-2 (Inventory Management):** The player shall be able to pick up items (`take sword`), view their inventory (`inv`), and inspect item stats (`inspect potion`).
- **F-3 (Combat & Health):** The player shall be able to attack hostile entities (`attack goblin`) utilizing weapon damage, while tracking their own Health Points (HP).
- **F-4 (Trading):** The player shall be able to interact with merchants to view stock (`shop`), purchase items (`buy flask`), and sell items (`sell sword`).
- **F-5 (AI Dialogue & Quests):** The player shall be able to talk to NPCs (`talk villager`) to receive AI-generated dialogues and track active quests (`quests`).
- **F-6 (Persistence):** The system shall allow the player to save their state and load it subsequently.
- **F-7 (World Editor):** The designer shall be able to create, edit, and link rooms, items, and NPCs via a CLI interface.

## 3. Non-Functional Requirements
- **NF-1 (Performance):** Basic commands should execute in under 100ms. AI-generated world generation may take up to 45 seconds depending on hardware but must provide clear loading indicators.
- **NF-2 (Usability):** The game must utilize `rich` terminal graphics to present data clearly (e.g., tables for inventory, colors for damage).
- **NF-3 (Maintainability):** The system must strictly adhere to Object-Oriented paradigms (Encapsulation, Polymorphism) to ensure ease of future expansion.

## 4. Use Cases

### 4.1 Player Use Cases
- **Move to Room:** The player inputs a direction. The parser validates the exit. If valid, the engine updates the player's current location and triggers the room's entry observer (e.g., triggering an ambush).
- **Engage in Combat:** The player types `attack <target>`. The system calculates total damage based on inventory, reduces target HP, and processes a counter-attack if the target survives.
- **Save Current Progress:** The player types `quit`. The engine serializes the current player state, inventory, and room configurations into `save_data.json`.

### 4.2 Designer Use Cases
- **Create New Item:** The designer launches `main.py editor`, selects the 'Create Item' menu, and inputs the item's name, type, and base stats.
- **Map Room Connection:** The designer selects a room and links it to another room by specifying the cardinal direction.
- **Export World:** The designer finalizes the map, and the engine serializes it into a JSON template (e.g., `test_world2.json`) that can be loaded by the main game loop or AI generator.
