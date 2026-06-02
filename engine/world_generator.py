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
    Randomly selects 3-5 connected rooms from the 7-room template.
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

        # 2. Randomly select 3-5 CONNECTED rooms from the template
        room_count = random.randint(3, 5)
        world_data = self._trim_world(world_data, room_count)
        actual_room_count = len(world_data.get('rooms', []))
        print(f"   🏰 Room count: {actual_room_count}")

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # 3. Get names and text from LLM
                request_body = self._build_request(world_data)
                raw_response = self._call_ollama(request_body)
                
                # 4. Inject new names into the template structure
                updated_world = self._apply_replacements(world_data, raw_response)
                print("\n✅ World generated successfully!")
                return updated_world
            except Exception as e:
                print(f"\n   ❌ Error on attempt {attempt + 1}: {e}")

        raise RuntimeError("World generation failed completely. No fallback world will be used.")

    def _trim_world(self, data: dict, room_count: int) -> dict:
        """Trims the world to room_count rooms using random connected subgraph selection."""
        data = copy.deepcopy(data)
        rooms = data.get('rooms', [])
        
        if len(rooms) <= room_count:
            return data
        
        # Build adjacency map
        room_map = {r['id']: r for r in rooms}
        
        # Start from player's starting room (always room_village)
        start_room_id = data.get('player', {}).get('current_room_id', rooms[0]['id'])
        
        # BFS-based random connected subgraph selection
        selected_ids = set()
        selected_ids.add(start_room_id)
        frontier = [start_room_id]
        
        while len(selected_ids) < room_count and frontier:
            # Pick a random room from the frontier
            current_id = random.choice(frontier)
            current_room = room_map.get(current_id)
            if not current_room:
                frontier.remove(current_id)
                continue
            
            # Get unvisited neighbors
            neighbors = [
                target_id for target_id in current_room.get('exits', {}).values()
                if target_id not in selected_ids and target_id in room_map
            ]
            
            if neighbors:
                # Add a random neighbor
                next_id = random.choice(neighbors)
                selected_ids.add(next_id)
                frontier.append(next_id)
            else:
                # No more unvisited neighbors from this room
                frontier.remove(current_id)
        
        # Keep only selected rooms
        kept_rooms = [r for r in rooms if r['id'] in selected_ids]
        
        # Remove exits that point to removed rooms
        for room in kept_rooms:
            room['exits'] = {
                direction: target_id
                for direction, target_id in room.get('exits', {}).items()
                if target_id in selected_ids
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
        
        # Trim quests — keep only those whose giver AND target are still in the game
        kept_quests = []
        for q in data.get('quests', []):
            giver_ok = q.get('giver_npc_id') in kept_npc_ids
            target_id = q.get('target_id', '')
            # Target can be an NPC (kill) or item (collect/deliver)
            target_ok = target_id in kept_npc_ids or target_id in kept_item_ids
            # For deliver quests, deliver_to NPC must also exist
            deliver_ok = True
            if q.get('quest_type') == 'deliver' and q.get('deliver_to'):
                deliver_ok = q['deliver_to'] in kept_npc_ids
            if giver_ok and target_ok and deliver_ok:
                kept_quests.append(q)
        data['quests'] = kept_quests
        
        return data

    def _build_request(self, world_data: dict) -> str:
        variety_seed = random.randint(1, 100000)
        
        room_count = len(world_data.get('rooms', []))
        item_count = len(world_data.get('items', []))
        npc_count = len(world_data.get('npcs', []))
        
        # Build dynamic format section
        room_lines = "\n".join([f"[Room {i+1} Name]|[Very short description]" for i in range(room_count)])
        item_lines = "\n".join([f"[Item Name]|[Very short description]" for _ in range(item_count)])
        
        # Determine NPC format based on types
        npc_format_lines = []
        for npc in world_data.get('npcs', []):
            npc_type = npc.get('npc_type', 'neutral')
            if npc_type == 'merchant':
                npc_format_lines.append("[Merchant Name]|[Very short desc]|[Short merchant greeting]")
            else:
                npc_format_lines.append("[NPC Name]|[Very short desc]|[Very short dialogue]")
        npc_lines = "\n".join(npc_format_lines)
        
        # Quest format
        quest_count = len(world_data.get('quests', []))
        quest_lines = "\n".join([f"[Quest Name]|[Very short quest description]" for _ in range(quest_count)])
        total_lines = room_count + item_count + npc_count + 1 + quest_count  # +1 for player
        
        system_prompt = f"""You are a game generator. Reply with EXACTLY {total_lines} lines of pipe-separated (|) text. NO markdown, NO intro.
Order: {room_count} Rooms, {item_count} Items, {npc_count} NPCs, 1 Player, {quest_count} Quests.
Keep descriptions and dialogues EXTREMELY short (max 3-5 words) to save time!

Format:
{room_lines}
{item_lines}
{npc_lines}
[Player Name]|[Very short desc]
{quest_lines}

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
Sir Boramir|A brave and noble knight.
Goblin Hunt|Slay the forest beast.
The Lost Crown|Return the king's crown."""

        user_prompt = f"Generate {self.theme} fantasy game objects. Seed: {variety_seed}"

        return json.dumps({
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.8,
                "num_predict": 250
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

    def _apply_replacements(self, base_data: dict, raw_text: str) -> dict:
        """Injects the LLM generated short lore into the base JSON structure"""
        lines = [line.strip() for line in raw_text.strip().split('\n') if '|' in line]
        
        room_count = len(base_data.get('rooms', []))
        item_count = len(base_data.get('items', []))
        npc_count = len(base_data.get('npcs', []))
        total_expected = room_count + item_count + npc_count + 1

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
        for i in range(min(item_count, len(items))):
            idx = room_count + i
            if idx < len(lines):
                parts = safe_split(lines[idx], 2)
                items[i]['name'] = parts[0]
                items[i]['description'] = parts[1]
                if items[i].get('item_type') == 'weapon':
                    items[i]['stats']['damage'] = random.randint(15, 50)
                elif items[i].get('item_type') == 'consumable':
                    items[i]['stats']['heal'] = random.randint(25, 60)
                elif items[i].get('item_type') == 'armor':
                    items[i]['stats']['defense'] = random.randint(5, 20)
                # Randomize value a bit
                base_val = items[i].get('value', 10)
                items[i]['value'] = max(5, base_val + random.randint(-10, 15))

        # NPCs (start after rooms + items)
        npcs = base_data.get('npcs', [])
        for i in range(min(npc_count, len(npcs))):
            idx = room_count + item_count + i
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
        player_idx = room_count + item_count + npc_count
        if player_idx < len(lines):
            parts = safe_split(lines[player_idx], 2)
            player['name'] = parts[0]
            player['description'] = parts[1]
            player['hp'] = random.randint(100, 200)
            player['gold'] = random.randint(30, 80)

        # Quests (after player)
        quests = base_data.get('quests', [])
        quest_count = len(quests)
        for i in range(quest_count):
            idx = room_count + item_count + npc_count + 1 + i
            if idx < len(lines):
                parts = safe_split(lines[idx], 2)
                quests[i]['name'] = parts[0]
                quests[i]['description'] = parts[1]

        return base_data

    @staticmethod
    def chat_with_npc(npc_name: str, npc_description: str, npc_type: str, user_message: str,
                      model: str = None, base_url: str = None) -> str:
        """Send a single chat message to an NPC via Ollama and return the streamed response."""
        model = model or WorldGenerator.DEFAULT_MODEL
        base_url = base_url or WorldGenerator.DEFAULT_BASE_URL

        personality = ""
        if npc_type == "hostile":
            personality = "You are aggressive, threatening, and menacing. You speak in short, angry sentences. You might insult the player or threaten violence."
        elif npc_type == "merchant":
            personality = "You are a shrewd but friendly trader. You love talking about your wares and making deals. You speak with merchant charm."
        else:
            personality = "You are a friendly, helpful character. You may share rumors, advice, or lore about the world."

        system_prompt = f"""You are '{npc_name}', a {npc_type} NPC in a medieval fantasy adventure game.
Description: {npc_description}
{personality}
Rules:
- Stay in character at ALL times.
- Keep responses SHORT (1-2 sentences max).
- NEVER break character or mention you are an AI.
- React naturally to what the player says."""

        request_body = json.dumps({
            "model": model,
            "prompt": user_message,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 60
            }
        })

        url = f"{base_url}/api/generate"
        req = urllib.request.Request(
            url,
            data=request_body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        full_response = []
        with urllib.request.urlopen(req, timeout=30) as resp:
            for line in resp:
                if line.strip():
                    chunk = json.loads(line.decode("utf-8"))
                    if "response" in chunk:
                        token = chunk["response"]
                        full_response.append(token)
                        print(token, end="", flush=True)
                    if chunk.get("done"):
                        break

        return "".join(full_response).strip()
