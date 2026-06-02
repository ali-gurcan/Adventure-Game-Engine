"""
World Generator Module
Generates dynamic adventure game worlds using Ollama LLM.
Uses a lightning-fast template-based approach with 3-5 rooms.
"""

import json
import urllib.request
import urllib.error
import os
import random
import copy

# Base template world file path (relative to project root)
BASE_TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_world2.json")

class WorldGenerator:
    """
    Generates a unique game world by loading a static template and 
    using Ollama to generate ONLY the text content (names, descriptions).
    Randomly selects 3-5 rooms from the 5-room template.
    """

    DEFAULT_MODEL = "Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M"
    DEFAULT_BASE_URL = "http://localhost:11434"
    MAX_RETRIES = 1

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.theme = "medieval"

    def generate(self) -> dict:
        print("\n⚡ Generating a new medieval adventure world...")
        
        # 1. Load base structure
        try:
            with open(BASE_TEMPLATE_FILE, 'r') as f:
                world_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"❌ Could not load base template: {e}")

        # 2. Randomly select 3-5 rooms from the template
        room_count = random.randint(3, 5)
        world_data = self._trim_world(world_data, room_count)
        print(f"   🏰 Room count: {room_count}")

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # 3. Get names and text from LLM
                request_body = self._build_request(room_count)
                raw_response = self._call_ollama(request_body)
                
                # 4. Inject new names into the template structure
                updated_world = self._apply_replacements(world_data, raw_response, room_count)
                print("\n✅ World generated successfully!")
                return updated_world
            except Exception as e:
                print(f"\n   ❌ Error on attempt {attempt + 1}: {e}")

        raise RuntimeError("World generation failed completely. No fallback world will be used.")

    def _trim_world(self, data: dict, room_count: int) -> dict:
        """Trims the world to room_count rooms and fixes dangling exits."""
        data = copy.deepcopy(data)
        rooms = data.get('rooms', [])
        
        # Keep only the first room_count rooms
        kept_rooms = rooms[:room_count]
        kept_room_ids = {r['id'] for r in kept_rooms}
        
        # Remove exits that point to removed rooms
        for room in kept_rooms:
            room['exits'] = {
                direction: target_id
                for direction, target_id in room.get('exits', {}).items()
                if target_id in kept_room_ids
            }
        
        data['rooms'] = kept_rooms
        
        # Trim items and NPCs to match what rooms reference
        kept_item_ids = set()
        kept_npc_ids = set()
        for room in kept_rooms:
            kept_item_ids.update(room.get('item_ids', []))
            kept_npc_ids.update(room.get('npc_ids', []))
        
        data['items'] = [i for i in data.get('items', []) if i['id'] in kept_item_ids]
        data['npcs'] = [n for n in data.get('npcs', []) if n['id'] in kept_npc_ids]
        
        return data

    def _build_request(self, room_count: int) -> str:
        variety_seed = random.randint(1, 100000)
        
        # Dynamic line count based on room_count
        item_count = len([1 for _ in range(3)])  # always 3 items max
        npc_count = len([1 for _ in range(3)])    # always 3 NPCs max
        total_lines = room_count + item_count + npc_count + 1  # +1 for player
        
        # Build dynamic format section
        room_lines = "\n".join([f"[Room {i+1} Name]|[Very short description]" for i in range(room_count)])
        item_lines = "[Item Name]|[Very short description]\n" * 3
        npc_lines = "[NPC Name]|[Very short desc]|[Very short dialogue]\n" * 3
        
        system_prompt = f"""You are a game generator. Reply with EXACTLY {total_lines} lines of pipe-separated (|) text. NO markdown, NO intro.
Order: {room_count} Rooms, 3 Items, 3 NPCs, 1 Player.
Keep descriptions and dialogues EXTREMELY short (max 3-5 words) to save time!

Format:
{room_lines}
{item_lines.strip()}
{npc_lines.strip()}
[Player Name]|[Very short desc]

Example:
Village Square|A peaceful cobblestone square.
Dark Forest|Shadowy woods, creepy noises.
Castle Tower|A tall abandoned tower.
Iron Sword|A rusty but sharp blade.
Health Potion|Glowing red magical liquid.
Gold Ring|A shiny plain band.
Villager|A scared looking man.|Please help us!
Goblin|A green ugly monster.|Argh! Die!
Old Wizard|A wise old man.|Take this wand.
Sir Boramir|A brave and noble knight."""

        user_prompt = f"Generate {self.theme} fantasy game objects. Seed: {variety_seed}"

        return json.dumps({
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.8,
                "num_predict": 150
            }
        })

    def _call_ollama(self, request_body: str) -> str:
        url = f"{self.base_url}/api/generate"
        print("   🔄 Fetching new names and lore: ", end="", flush=True)

        req = urllib.request.Request(
            url,
            data=request_body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        full_response = []
        with urllib.request.urlopen(req, timeout=45) as resp:
            for line in resp:
                if line.strip():
                    chunk = json.loads(line.decode("utf-8"))
                    if "response" in chunk:
                        full_response.append(chunk["response"])
                        if len(full_response) % 3 == 0:
                            print(".", end="", flush=True)
                    if chunk.get("done"):
                        total_dur = chunk.get("total_duration", 0)
                        print(f" [Done in {total_dur / 1e9:.1f}s]")
                        break
        
        raw_text = "".join(full_response)
        if not raw_text:
            raise ValueError("Empty response")
        return raw_text

    def _apply_replacements(self, base_data: dict, raw_text: str, room_count: int) -> dict:
        """Injects the LLM generated short lore into the base JSON structure"""
        lines = [line.strip() for line in raw_text.strip().split('\n') if '|' in line]
        
        total_expected = room_count + 3 + 3 + 1  # rooms + items + npcs + player
        if len(lines) < total_expected:
            raise ValueError(f"LLM produced incomplete data (expected {total_expected} lines, got {len(lines)}).")

        def safe_split(line, expected_parts):
            parts = line.split('|')
            if len(parts) < expected_parts:
                raise ValueError(f"Incomplete line format: '{line}' (expected {expected_parts} parts, got {len(parts)}).")
            return [p.strip() for p in parts]

        # Rooms
        rooms = base_data.get('rooms', [])
        for i in range(min(room_count, len(rooms))):
            if i < len(lines):
                parts = safe_split(lines[i], 2)
                rooms[i]['name'] = parts[0]
                exits = ", ".join(f"'{k}'" for k in rooms[i].get('exits', {}).keys())
                rooms[i]['description'] = f"{parts[1]} Exits: {exits}."

        # Items (start after rooms)
        items = base_data.get('items', [])
        for i in range(min(3, len(items))):
            idx = room_count + i
            if idx < len(lines):
                parts = safe_split(lines[idx], 2)
                items[i]['name'] = parts[0]
                items[i]['description'] = parts[1]
                if items[i].get('item_type') == 'weapon':
                    items[i]['stats']['damage'] = random.randint(15, 50)
                elif items[i].get('item_type') == 'consumable':
                    items[i]['stats']['heal'] = random.randint(25, 60)

        # NPCs (start after rooms + items)
        npcs = base_data.get('npcs', [])
        for i in range(min(3, len(npcs))):
            idx = room_count + 3 + i
            if idx < len(lines):
                parts = safe_split(lines[idx], 3)
                npcs[i]['name'] = parts[0]
                npcs[i]['description'] = parts[1]
                npcs[i]['dialogue'] = parts[2]
                npcs[i]['hp'] = random.randint(50, 200)
                if npcs[i].get('npc_type') == 'hostile':
                    npcs[i]['damage'] = random.randint(10, 30)

        # Player (last line)
        player = base_data.get('player', {})
        player_idx = room_count + 3 + 3
        if player_idx < len(lines):
            parts = safe_split(lines[player_idx], 2)
            player['name'] = parts[0]
            player['description'] = parts[1]
            player['hp'] = random.randint(100, 200)

        return base_data
