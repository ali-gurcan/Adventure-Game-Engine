# Test Procedures

## 1. Overview
The testing framework ensures that the text-parser processes natural language robustly, the combat/economy mathematics function correctly, and the JSON serialization handles data persistently.

## 2. Happy-Path Scenarios
- **TP-01 (Movement):** 
  - **Action:** Player types `go north`.
  - **Expected:** Player moves to the northern room, the UI updates, and the new room description is printed.
- **TP-02 (Economy):**
  - **Action:** Player uses `shop` to view wares, then `buy <item>` while having sufficient gold.
  - **Expected:** Gold is deducted, item is added to inventory, and the item's stats now apply to the player.
- **TP-03 (Quests):**
  - **Action:** Player completes a "kill" quest objective and types `quests`.
  - **Expected:** Quest updates status to "completed" and grants the gold reward.

## 3. Negative & Alternative Scenarios
- **TP-04 (Invalid Movement):**
  - **Action:** Player types `go up` (where no exit exists).
  - **Expected:** The engine gracefully rejects the input with: "You can't go that way."
- **TP-05 (Poor Economy):**
  - **Action:** Player attempts `buy <expensive item>` without enough gold.
  - **Expected:** The merchant NPC rejects the sale; gold remains untouched.
- **TP-06 (Spam Attacks):**
  - **Action:** Player spams `attack goblin` after the goblin is already dead.
  - **Expected:** Engine catches the null reference and outputs "They aren't here," preventing exceptions.

## 4. Edge-Cases Highlight
- **LLM Partial Failures:** If the `world_generator.py` receives incomplete JSON text from the Ollama model (e.g., stopping mid-generation).
  - **Mitigation Procedure:** The engine must validate `total_expected` lines. If validation fails, it must explicitly reject the payload and retry (`MAX_RETRIES = 2`), ensuring a non-corrupted game state.
- **Combat Math Overflows:** Player equipping multiple items should correctly aggregate damage without overflowing limits.
