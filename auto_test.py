"""
Auto-Test Scenario for the Adventure Game Engine.
Tests ALL commands including full quest completion (kill, collect, deliver).
"""
import sys
import builtins

from engine.world_generator import WorldGenerator
from engine.core import GameEngine
from engine.game_state import GameState
from engine.parser import Parser
from engine.events import Subject, GameEventLogger

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

# ─────────────────────────────────────────
# BFS path finder
# ─────────────────────────────────────────
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
curr_room = start_room
command_queue = []

def navigate_to(target_room_id):
    global curr_room
    path = find_path(curr_room, target_room_id)
    for step in path:
        command_queue.append(f"go {step}")
    curr_room = target_room_id

# ─────────────────────────────────────────
# Scan world for targets
# ─────────────────────────────────────────
quest_givers   = []   # list of {room, npc, quest}
merchants      = []   # list of {room, npc}
kill_enemies   = []   # list of {room, npc, quest} – hostile with kill quest
items_in_rooms = []   # list of {room, item}
quest_deliver_targets = []  # list of {room, npc, quest} – NPCs who receive delivery

for room in engine.state.rooms.values():
    for itm in room.items:
        items_in_rooms.append({"room": room.id, "item": itm})

    for npc in room.npcs:
        if npc.npc_type == "merchant":
            merchants.append({"room": room.id, "npc": npc})
        elif npc.npc_type == "hostile":
            # Find any kill quest targeting this NPC
            for q in engine.state.quests.values():
                if q.quest_type == "kill" and q.target_id == npc.id:
                    kill_enemies.append({"room": room.id, "npc": npc, "quest": q})
                    break
            else:
                kill_enemies.append({"room": room.id, "npc": npc, "quest": None})
        else:
            # Check if this NPC gives a quest
            for q in engine.state.quests.values():
                if q.giver_npc_id == npc.id:
                    quest_givers.append({"room": room.id, "npc": npc, "quest": q})

            # Check if this NPC receives a delivery
            for q in engine.state.quests.values():
                if q.quest_type == "deliver" and q.deliver_to == npc.id:
                    quest_deliver_targets.append({"room": room.id, "npc": npc, "quest": q})

# ─────────────────────────────────────────
# Build command sequence
# ─────────────────────────────────────────

# Intro commands
command_queue.extend(["look", "inv", "map"])

# 1. Accept all available quests from quest givers + have a real conversation
for qg in quest_givers:
    navigate_to(qg["room"])
    command_queue.append(f"talk {qg['npc'].name}")
    command_queue.append("yes")   # accept quest

    # Build contextual multi-turn conversation based on NPC type
    q = qg.get("quest")
    npc_type = qg["npc"].npc_type

    if npc_type == "neutral":
        command_queue.append("What dangers lurk nearby?")
        command_queue.append("Tell me more about this place.")
        command_queue.append("Is there anything I should know before I go?")
    elif npc_type == "merchant":
        command_queue.append("What rare items do you carry?")
        command_queue.append("Any rumors from the road?")
    else:
        command_queue.append("Who are you?")
        command_queue.append("Why are you here?")

    command_queue.append("bye")

command_queue.append("quests")

# 2. Pick up items in rooms (for collect & deliver quests)
collect_quest_item_ids = set()
deliver_quest_item_ids = set()
for q in engine.state.quests.values():
    if q.quest_type == "collect":
        collect_quest_item_ids.add(q.target_id)
    elif q.quest_type == "deliver":
        deliver_quest_item_ids.add(q.target_id)

all_pickup_ids = collect_quest_item_ids | deliver_quest_item_ids

for ir in items_in_rooms:
    navigate_to(ir["room"])
    command_queue.append(f"take {ir['item'].name}")
    command_queue.append(f"inspect {ir['item'].name}")

command_queue.append("inv")

# 3. Visit merchant
if merchants:
    m = merchants[0]
    navigate_to(m["room"])
    command_queue.append("shop")
    command_queue.append("buy shield")  # Will fail gracefully if not available
    # Sell a non-quest item if we have one picked up
    for ir in items_in_rooms:
        if ir["item"].id not in all_pickup_ids:
            command_queue.append(f"sell {ir['item'].name}")
            break

command_queue.append("inv")

# 4. Kill hostile enemies (complete kill quests)
for ke in kill_enemies:
    navigate_to(ke["room"])
    
    # Pre-emptively heal if we have a potion
    for ir in items_in_rooms:
        if ir["item"].item_type == "consumable":
            command_queue.append(f"use {ir['item'].name}")
            
    # Attack loop
    # We cap at 6 hits so we don't spam 'They aren't here' when we do massive damage
    npc_hp = getattr(ke["npc"], 'hp', 60)
    hits_needed = min(6, (npc_hp // 15) + 1)
    for _ in range(hits_needed):
        command_queue.append(f"attack {ke['npc'].name}")

command_queue.append("quests")

# 5. Complete deliver quests – go to the delivery NPC and talk
for dt in quest_deliver_targets:
    navigate_to(dt["room"])
    command_queue.append(f"talk {dt['npc'].name}")
    command_queue.append("bye")


command_queue.append("quests")
command_queue.append("inv")
command_queue.append("quit")

# ─────────────────────────────────────────
# Print plan and execute
# ─────────────────────────────────────────
print("\n>>> Generated command sequence:")
for i, cmd in enumerate(command_queue):
    print(f"  {i+1:>3}. {cmd}")

def mock_input(prompt=""):
    print(prompt, end="")
    if command_queue:
        cmd = command_queue.pop(0)
        print(cmd)
        return cmd
    return "quit"

builtins.input = mock_input

print("\n>>> Executing Automated Command Loop...")
engine._look()
engine.run()

print("\n=======================================")
print("✅ FULL AUTO-TEST SCENARIO COMPLETED!")
print("=======================================")
