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
    MAX_RETRIES = 4

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

        # 2. Randomly select 4-7 CONNECTED rooms from the template
        room_count = random.randint(4, 6)
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
        themes = [
            "dark medieval fantasy", "high fantasy with ancient ruins", "gothic horror",
            "sword and sorcery", "cursed kingdom", "lost civilization explorer"
        ]
        theme = random.choice(themes)
        self.theme = theme

        room_count = len(world_data.get('rooms', []))
        item_count = len(world_data.get('items', []))
        npc_count  = len(world_data.get('npcs', []))

        # Build dynamic format hints
        room_lines = "\n".join(
            [f"[Evocative Room {i+1} Name]|[1 atmospheric sentence about this place]" for i in range(room_count)]
        )
        item_lines = "\n".join(
            [f"[Unique Item Name]|[1 sentence description with lore flavour]" for _ in range(item_count)]
        )

        npc_format_lines = []
        for npc in world_data.get('npcs', []):
            npc_type = npc.get('npc_type', 'neutral')
            if npc_type == 'merchant':
                npc_format_lines.append(
                    "[Colourful Merchant Name]|[1 sentence trader description]|[Enticing greeting that mentions their wares]"
                )
            elif npc_type == 'hostile':
                npc_format_lines.append(
                    "[Menacing Enemy Name]|[1 sentence monster description]|[Threatening battle cry or growl]"
                )
            else:
                npc_format_lines.append(
                    "[Interesting NPC Name]|[1 sentence character description]|[Dialogue hinting at a quest, secret, or lore]"
                )
        npc_lines = "\n".join(npc_format_lines)

        quest_count = len(world_data.get('quests', []))
        quest_lines = "\n".join(
            [f"[Creative Quest Name]|[1 sentence story-driven objective mentioning the specific generated names]" for _ in range(quest_count)]
        )

        # Build quest relation hints so the LLM connects the right NPCs and Items
        quest_hints = []
        for i, q in enumerate(world_data.get('quests', [])):
            q_type = q.get('quest_type', 'kill')
            giver_id = q.get('giver_npc_id')
            target_id = q.get('target_id')
            
            giver_idx = next((j+1 for j, n in enumerate(world_data.get('npcs', [])) if n['id'] == giver_id), "?")
            
            if q_type == 'kill':
                target_idx = next((j+1 for j, n in enumerate(world_data.get('npcs', [])) if n['id'] == target_id), "?")
                quest_hints.append(f"- Quest {i+1}: Given by NPC {giver_idx}, objective is to assassinate/defeat NPC {target_idx}.")
            elif q_type == 'collect':
                target_idx = next((j+1 for j, itm in enumerate(world_data.get('items', [])) if itm['id'] == target_id), "?")
                quest_hints.append(f"- Quest {i+1}: Given by NPC {giver_idx}, objective is to find/steal Item {target_idx}.")
            elif q_type == 'deliver':
                target_idx = next((j+1 for j, itm in enumerate(world_data.get('items', [])) if itm['id'] == target_id), "?")
                deliv_id = q.get('deliver_to')
                deliv_idx = next((j+1 for j, n in enumerate(world_data.get('npcs', [])) if n['id'] == deliv_id), "?")
                quest_hints.append(f"- Quest {i+1}: Given by NPC {giver_idx}, objective is to deliver Item {target_idx} to NPC {deliv_idx}.")

        quest_hints_str = "\n".join(quest_hints)

        total_lines = room_count + item_count + npc_count + 1 + quest_count  # +1 for player


        system_prompt = f"""You are a world-builder for a {theme} text adventure game.
Reply with EXACTLY {total_lines} pipe-separated (|) lines. NO markdown, NO numbered lists, NO extra text.
Order: {room_count} Rooms, {item_count} Items, {npc_count} NPCs, 1 Player name line, {quest_count} Quests.

Naming rules:
- Room names: 2-3 evocative words (e.g. "Ashen Hollow", "Thornwall Keep", "Pale Reaches").
- Item names: specific and interesting (e.g. "Voidstone Dagger", "Flask of Moonfire", "Gravewarden Shield").
- NPC names: fit their role. Merchants sound mercantile. Enemies sound menacing. Neutral NPCs feel real.
- Descriptions: exactly 1 sentence, atmospheric, max 15 words.
- Dialogues: exactly 1 sentence, in-character, 8-14 words, hint at lore or quest.
- Player line: a single heroic first name only (e.g. "Aldric|Hero", "Sera|Hero").

Quest Rules:
The quests MUST deeply tie into the lore and use the newly generated names based on these relations:
{quest_hints_str}
- Quest names: 3-5 creative words.
- Quest descriptions: 1 sentence that connects the lore to the specific objective.

Format:
{room_lines}
{item_lines}
{npc_lines}
[Hero's first name only]|Hero
{quest_lines}

Example output:
Ashen Hollow|A ruined village where ash falls like snow from a perpetually grey sky.
Thornwall Keep|Crumbling battlements covered in black ivy overlook a fog-filled valley.
Blood Mire|Thick red mud gurgles and shifts as if something beneath still breathes.
Voidstone Dagger|A blade that drinks light and whispers of forgotten names.
Flask of Moonfire|Liquid starlight swirls within; one sip mends shattered flesh.
Gravewarden Shield|A shield etched with the names of every warrior who ever carried it.
Mira the Undying|A pale merchant who sells only by candlelight and never blinks.|Step closer, traveler; I carry wares the living rarely dare to buy.
Grask the Bone-Render|A skeleton animated by dark sorcery, its joints wrapped in rusted chain.|Your bones will join my collection before this night is through.
Elara of the Mire|A swamp-witch whose eyes hold centuries of cold, patient malice.|The thing you seek lies where the roots drink from the forgotten dead.
Kael|Hero
Bone-Render's End|Defeat Grask the Bone-Render haunting Ashen Hollow to lift the curse.
The Sunken Compass|Retrieve the navigator's lost compass from the depths of Blood Mire."""

        user_prompt = f"Generate a {theme} text adventure world. Seed: {variety_seed}"

        return json.dumps({
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.85,
                "num_predict": 1500,
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
        """Injects the LLM generated lore into the base JSON structure.
        
        Strategy: player name line may or may not have a | character.
        We detect it separately from the raw text, then parse pipe-lines
        for rooms/items/npcs/quests without counting the player line.
        """
        # --- 1. Find the player name from raw text ---
        # The player line is a short (1-2 words) line with no | OR a line like "Name|Hero"
        player_name_candidate = None
        raw_lines_all = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]
        for raw_line in raw_lines_all:
            parts = raw_line.split('|')
            first = parts[0].strip()
            # A valid player name: 1-2 words, no numbers, short (looks like a real name)
            words = first.split()
            if (len(parts) <= 2 and len(words) <= 2 and len(first) <= 24
                    and first.isalpha() or (len(words) == 2 and all(w.isalpha() for w in words))):
                # Extra guard: second part (if any) should be exactly "Hero" or short
                second = parts[1].strip() if len(parts) > 1 else ""
                if second in ("", "Hero", "Protagonist", "Player") or len(second) <= 12:
                    player_name_candidate = first
                    # Don't break yet — keep searching in case it's ambiguous;
                    # take the first qualifying single-word candidate
                    if len(words) == 1:
                        break

        # --- 2. Extract pipe-delimited data lines (rooms/items/npcs/quests only) ---
        # We exclude the player line — recognised by: single or double token, |Hero etc.
        pipe_lines = []
        for raw_line in raw_lines_all:
            if '|' not in raw_line:
                continue
            parts = raw_line.split('|')
            first = parts[0].strip()
            second = parts[1].strip() if len(parts) > 1 else ""
            # Skip the player line that slipped in with |Hero
            if len(first.split()) <= 2 and second in ("Hero", "Protagonist", "Player", ""):
                continue
            pipe_lines.append(raw_line.strip())

        room_count  = len(base_data.get('rooms',  []))
        item_count  = len(base_data.get('items',  []))
        npc_count   = len(base_data.get('npcs',   []))
        quest_count = len(base_data.get('quests', []))
        total_expected = room_count + item_count + npc_count + quest_count
        minimum_required = room_count  # at minimum the rooms must be renamed

        if len(pipe_lines) < minimum_required:
            raise ValueError(
                f"LLM produced too few lines "
                f"(need at least {minimum_required} for rooms, got {len(pipe_lines)})."
            )
        if len(pipe_lines) < total_expected:
            print(f"\n   ⚠️  Partial output ({len(pipe_lines)}/{total_expected} lines) — filling rest from template.")

        def safe_split(line, expected_parts):
            parts = line.split('|')
            if len(parts) < expected_parts:
                parts.extend(["[Mystery]"] * (expected_parts - len(parts)))
            return [p.strip() for p in parts[:expected_parts]]

        # --- 3. Rooms ---
        rooms = base_data.get('rooms', [])
        for i in range(min(room_count, len(rooms))):
            if i < len(pipe_lines):
                parts = safe_split(pipe_lines[i], 2)
                rooms[i]['name'] = parts[0]
                exits = ", ".join(f"'{k}'" for k in rooms[i].get('exits', {}).keys())
                rooms[i]['description'] = f"{parts[1]} Exits: {exits}."

        # --- 4. Items ---
        items = base_data.get('items', [])
        for i in range(min(item_count, len(items))):
            idx = room_count + i
            if idx < len(pipe_lines):
                parts = safe_split(pipe_lines[idx], 2)
                items[i]['name'] = parts[0]
                items[i]['description'] = parts[1]
                if items[i].get('item_type') == 'weapon':
                    items[i]['stats']['damage'] = random.randint(15, 50)
                elif items[i].get('item_type') == 'consumable':
                    items[i]['stats']['heal'] = random.randint(25, 60)
                elif items[i].get('item_type') == 'armor':
                    items[i]['stats']['defense'] = random.randint(5, 20)
                base_val = items[i].get('value', 10)
                items[i]['value'] = max(5, base_val + random.randint(-10, 15))

        # --- 5. NPCs ---
        npcs = base_data.get('npcs', [])
        for i in range(min(npc_count, len(npcs))):
            idx = room_count + item_count + i
            if idx < len(pipe_lines):
                parts = safe_split(pipe_lines[idx], 3)
                npcs[i]['name'] = parts[0]
                npcs[i]['description'] = parts[1]
                npcs[i]['dialogue'] = parts[2]
                npcs[i]['hp'] = random.randint(50, 200)
                if npcs[i].get('npc_type') == 'hostile':
                    npcs[i]['damage'] = random.randint(10, 30)

        # --- 6. Player ---
        player = base_data.get('player', {})
        if player_name_candidate:
            player['name'] = player_name_candidate
        player['hp']   = random.randint(130, 200)
        player['gold'] = random.randint(40, 100)

        # --- 7. Quests ---
        quests = base_data.get('quests', [])
        for i in range(quest_count):
            idx = room_count + item_count + npc_count + i
            if idx < len(pipe_lines):
                parts = safe_split(pipe_lines[idx], 2)
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
            personality = (
                "You are a dangerous and aggressive monster or villain. "
                "You speak in short, threatening sentences full of menace. "
                "You might taunt, insult or threaten violence. "
                "Occasionally you can reveal a twisted backstory or motivation if pressed."
            )
        elif npc_type == "merchant":
            personality = (
                "You are a shrewd but charming trader. You love talking about your rare wares. "
                "Drop hints about interesting items or services. Be persuasive and slightly mysterious."
            )
        else:
            personality = (
                "You are a knowledgeable and interesting character in a fantasy world. "
                "Share rumors, lore, advice, or warnings related to your surroundings. "
                "You may have secrets you reveal gradually if the player asks the right questions."
            )

        system_prompt = f"""You are '{npc_name}', a {npc_type} NPC in a fantasy adventure game.
Description: {npc_description}
{personality}
Strict rules:
- Stay in character at ALL times. NEVER break character or say you are an AI.
- Respond in 1-2 sentences max (20 words max per reply).
- React naturally and emotionally to what the player says.
- If the player mentions something in your environment, acknowledge it."""

        request_body = json.dumps({
            "model": model,
            "prompt": user_message,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.75,
                "num_predict": 80,
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
