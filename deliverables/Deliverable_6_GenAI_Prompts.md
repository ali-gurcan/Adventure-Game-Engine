# Generative AI Prompts Log

This document records the major Generative AI prompts used during the development lifecycle to brainstorm architecture, debug code, and generate procedural content.

## 1. Procedural World Generation (In-Game LLM Prompt)
Used dynamically inside `world_generator.py` to command Ollama to reskin the JSON template.

**System Prompt:**
```text
You are a world-builder for a [gothic horror] text adventure game.
Reply with EXACTLY 20 pipe-separated (|) lines. NO markdown, NO numbered lists, NO extra text.
Order: 7 Rooms, 5 Items, 4 NPCs, 1 Player name line, 3 Quests.

Naming rules:
- Room names: 2-3 evocative words (e.g. "Ashen Hollow", "Thornwall Keep", "Pale Reaches").
- Item names: specific and interesting (e.g. "Voidstone Dagger", "Flask of Moonfire", "Gravewarden Shield").
- NPC names: fit their role. Merchants sound mercantile. Enemies sound menacing. Neutral NPCs feel real.
- Descriptions: exactly 1 sentence, atmospheric, max 15 words.
- Dialogues: exactly 1 sentence, in-character, 8-14 words, hint at lore or quest.
- Player line: a single heroic first name only (e.g. "Aldric", "Sera", "Vorn").

Quest Rules:
The quests MUST deeply tie into the lore and use the newly generated names based on these relations:
- Quest 1: Given by NPC 1, objective is to assassinate/defeat NPC 3.
- Quest 2: Given by NPC 4, objective is to find/steal Item 5.
- Quest names: 3-5 creative words.
- Quest descriptions: 1 sentence that connects the lore to the specific objective.
```

## 2. NPC Dialogue Generation (In-Game LLM Prompt)
Used in `chat_with_npc()` to generate contextual multi-turn conversation.

**System Prompt:**
```text
You are an NPC in a dark medieval fantasy text adventure.
Your name is: Grask the Bone-Render.
Your description: A skeleton animated by dark sorcery.
Your type is: hostile (You are threatening, aggressive, and evil).

Current context: You are speaking to the hero.
Respond in exactly one or two short sentences (max 20 words). Stay in character. Do not use quotation marks.
```

## 3. Development / Debugging Prompts (Used via ChatGPT / Claude)
- *"I am getting a bug where my `BuyCommand` is unable to find the item in the room. The merchant's shop is rendering fine, but buying fails. Here is my `BuyCommand` and `ShopCommand`. How do I synchronize their item lookup?"* -> Resulted in the `copy.deepcopy` fix from global `state.items`.
- *"How can I ensure my Python game parses commands robustly? Should I use a big if-else chain or a pattern?"* -> Resulted in the adoption of the **Command Pattern** mapping strings to Class executables.
- *"My text adventure game feels dead. How can I use the Observer Pattern to make things happen automatically?"* -> Resulted in the `Event/Trigger` system where moving into a room triggers an Ambush sequence based on the room's current state.
