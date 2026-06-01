"""
World Generator Module
Generates dynamic adventure game worlds using Ollama LLM.
Uses a lightning-fast template-based approach to generate content in 1-2 seconds.
"""

import json
import urllib.request
import urllib.error
import os
import random

# Base template world file path (relative to project root)
BASE_TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_world2.json")

class WorldGenerator:
    """
    Generates a unique game world by loading a static template and 
    using Ollama to generate ONLY the text content (names, descriptions).
    This ensures blazing fast (1-2s) generation.
    """

    DEFAULT_MODEL = "Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M"
    DEFAULT_BASE_URL = "http://localhost:11434"
    MAX_RETRIES = 1

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.theme = "medieval"

    def generate(self) -> dict:
        print("\n⚡ Generating a new medieval adventure world lightning fast...")
        
        # 1. Load base structure (sabit kalacak olan yapi)
        try:
            with open(BASE_TEMPLATE_FILE, 'r') as f:
                world_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"❌ Could not load base template: {e}")

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # 2. Get ONLY names and text from LLM (super fast)
                request_body = self._build_request()
                raw_response = self._call_ollama(request_body)
                
                # 3. Inject new names into the static template structure
                updated_world = self._apply_replacements(world_data, raw_response)
                print("\n✅ World generated successfully!")
                return updated_world
            except Exception as e:
                print(f"\n   ❌ Error on attempt {attempt + 1}: {e}")

        # Eğer retries biterse hiçbir şekilde fallback dönme, işlemi iptal et!
        raise RuntimeError("World generation failed completely. No fallback world will be used.")

    def _build_request(self) -> str:
        variety_seed = random.randint(1, 100000)
        
        system_prompt = """You are a game generator. Reply with EXACTLY 10 lines of pipe-separated (|) text. NO markdown.
Order: 3 Rooms, 3 Items, 3 NPCs, 1 Player.
Keep descriptions and dialogues EXTREMELY short (max 3-5 words) to save time!

Format:
[Room Name]|[Very short description]
[Room Name]|[Very short description]
[Room Name]|[Very short description]
[Item Name]|[Very short description]
[Item Name]|[Very short description]
[Item Name]|[Very short description]
[NPC Name]|[Very short desc]|[Very short dialogue]
[NPC Name]|[Very short desc]|[Very short dialogue]
[NPC Name]|[Very short desc]|[Very short dialogue]
[Player Name]|[Very short desc]

Example:
Village Square|A peaceful cobblestone square.
Dark Forest|Shadowy woods with creepy noises.
Castle Tower|A tall abandoned stone tower.
Iron Sword|A rusty but sharp blade.
Health Potion|Glowing red magical liquid.
Gold Ring|A shiny plain band.
Villager|A scared looking man.|Please help us!
Goblin|A green ugly monster.|Argh! Die!
Old Wizard|A wise old man.|Take this wand.
Sir Ali|A brave and noble knight."""

        user_prompt = f"Generate {self.theme} fantasy game objects. Seed: {variety_seed}"

        return json.dumps({
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": 0.8,
                "num_predict": 130  # Allows for short descriptions while remaining fast
            }
        })

    def _call_ollama(self, request_body: str) -> str:
        url = f"{self.base_url}/api/generate"
        print("   🔄 Fetching new names and short lore: ", end="", flush=True)

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
        
        if len(lines) < 10:
            raise ValueError(f"LLM produced incomplete data (expected 10 lines, got {len(lines)}).")

        def safe_split(line, expected_parts):
            parts = line.split('|')
            if len(parts) < expected_parts:
                raise ValueError(f"Incomplete line format: '{line}' (expected {expected_parts} parts, got {len(parts)}).")
            return [p.strip() for p in parts]

        # 3 Rooms
        rooms = base_data.get('rooms', [])
        for i in range(min(3, len(rooms))):
            if i < len(lines):
                parts = safe_split(lines[i], 2)
                rooms[i]['name'] = parts[0]
                exits = ", ".join(f"'{k}'" for k in rooms[i].get('exits', {}).keys())
                rooms[i]['description'] = f"{parts[1]} Exits: {exits}."

        # 3 Items
        items = base_data.get('items', [])
        for i in range(min(3, len(items))):
            idx = i + 3
            if idx < len(lines):
                parts = safe_split(lines[idx], 2)
                items[i]['name'] = parts[0]
                items[i]['description'] = parts[1]
                if items[i].get('item_type') == 'weapon':
                    items[i]['stats']['damage'] = random.randint(15, 50)
                elif items[i].get('item_type') == 'consumable':
                    items[i]['stats']['heal'] = random.randint(25, 60)

        # 3 NPCs
        npcs = base_data.get('npcs', [])
        for i in range(min(3, len(npcs))):
            idx = i + 6
            if idx < len(lines):
                parts = safe_split(lines[idx], 3)
                npcs[i]['name'] = parts[0]
                npcs[i]['description'] = parts[1]
                npcs[i]['dialogue'] = parts[2]
                npcs[i]['hp'] = random.randint(50, 200)
                if npcs[i].get('npc_type') == 'hostile':
                    npcs[i]['damage'] = random.randint(10, 30)

        # 1 Player
        player = base_data.get('player', {})
        if 9 < len(lines):
            parts = safe_split(lines[9], 2)
            player['name'] = parts[0]
            player['description'] = parts[1]
            player['hp'] = random.randint(100, 200)

        return base_data
