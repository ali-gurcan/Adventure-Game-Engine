import sys
import builtins

from engine.world_generator import WorldGenerator
from engine.core import GameEngine
from engine.game_state import GameState
from engine.parser import Parser
from engine.events import Subject, GameEventLogger
from engine.commands import GoCommand

print("=======================================")
print("🤖 FULL AUTO-TEST SCENARIO (ALL COMMANDS)")
print("=======================================")

print("\n>>> Generating dynamic world using Ollama...")
gen = WorldGenerator()
world_data = gen.generate()

engine = GameEngine.__new__(GameEngine)
engine.state = GameState()
engine.event_bus = Subject()
engine.event_bus.attach(GameEventLogger())
engine.parser = Parser(engine)

if not engine.state.load_from_dict(world_data):
    print("Failed to load world.")
    sys.exit(1)

engine.can_play = True
print("\n>>> Analyzing World Map for Auto-Navigation...")

# Helper to find path between rooms using BFS
def find_path(start_id, target_id):
    queue = [(start_id, [])]
    visited = set()
    while queue:
        curr, path = queue.pop(0)
        if curr == target_id:
            return path
        if curr in visited:
            continue
        visited.add(curr)
        room = engine.state.rooms.get(curr)
        if room:
            for direction, next_id in room.exits.items():
                queue.append((next_id, path + [direction]))
    return []

start_room = engine.state.player.current_room_id

# Find targets
quest_giver = None
merchant = None
enemy = None
take_item = None

# Identify rooms
for room in engine.state.rooms.values():
    # Items
    if room.items and not take_item:
        take_item = {"room": room.id, "item": room.items[0]}
    
    # NPCs
    for npc in room.npcs:
        # Is merchant?
        if npc.npc_type == "merchant" and not merchant:
            merchant = {"room": room.id, "npc": npc}
        # Is hostile?
        elif npc.npc_type == "hostile" and not enemy:
            enemy = {"room": room.id, "npc": npc}
        # Has quest?
        elif not quest_giver:
            for q in engine.state.quests.values():
                if q.giver_npc_id == npc.id:
                    quest_giver = {"room": room.id, "npc": npc, "quest": q}
                    break

# Build command queue dynamically
command_queue = []
curr_room = start_room

command_queue.extend(["look", "inv", "map"])

def navigate_to(target_room_id):
    global curr_room
    path = find_path(curr_room, target_room_id)
    for step in path:
        command_queue.append(f"go {step}")
    curr_room = target_room_id

# 1. Test Quest / Talk
if quest_giver:
    navigate_to(quest_giver["room"])
    command_queue.append(f"talk {quest_giver['npc'].name}")
    command_queue.append("yes") # Accept quest
    command_queue.append("What is your name?") # Talk to LLM
    command_queue.append("bye")
    command_queue.append("quests")

# 2. Test Take
if take_item:
    navigate_to(take_item["room"])
    command_queue.append(f"take {take_item['item'].name}")
    command_queue.append("inv")

# 3. Test Merchant (Shop, Buy, Sell)
if merchant:
    navigate_to(merchant["room"])
    command_queue.append("shop")
    # Merchant items aren't generated directly on merchant in this engine, 
    # but the command works. Just to test parser:
    command_queue.append("buy shield")
    if take_item:
        command_queue.append(f"sell {take_item['item'].name}")
    command_queue.append("inv")

# 4. Test Combat
if enemy:
    navigate_to(enemy["room"])
    # Attack until dead (queue a few attacks)
    for _ in range(3):
        command_queue.append(f"attack {enemy['npc'].name}")

command_queue.append("quit")

def mock_input(prompt=""):
    print(prompt, end="")
    if command_queue:
        cmd = command_queue.pop(0)
        print(cmd)
        return cmd
    return "quit"

builtins.input = mock_input

print("\n>>> Generated command sequence:")
for i, cmd in enumerate(command_queue):
    print(f"{i+1}. {cmd}")

print("\n>>> Executing Automated Command Loop...")
engine._look()
engine.run()

print("\n=======================================")
print("✅ FULL AUTO-TEST SCENARIO COMPLETED!")
print("=======================================")
