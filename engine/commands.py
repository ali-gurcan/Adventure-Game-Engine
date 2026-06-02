from abc import ABC, abstractmethod
from engine import colors as c

class Command(ABC):
    def __init__(self, engine_sys):
        self.engine_sys = engine_sys

    @abstractmethod
    def execute(self, args: list):
        pass

class GoCommand(Command):
    def execute(self, args: list):
        if not args:
            print(c.warning("Go where?"))
            return
        direction = args[0]
        state = self.engine_sys.state
        player = state.player
        current_room = state.rooms.get(player.current_room_id)
        
        if current_room and direction in current_room.exits:
            player.previous_room_id = current_room.id # Store for escape
            next_room_id = current_room.exits[direction]
            player.current_room_id = next_room_id
            self.engine_sys.event_bus.notify("room_enter", {"room_id": next_room_id})
            print(c.narration(f"You go {direction}."))
            self.engine_sys._look()
            self.engine_sys._check_hostiles() # Check encounters
        else:
            print(c.warning("You can't go that way."))

class LookCommand(Command):
    def execute(self, args: list):
        self.engine_sys._look()

class TakeCommand(Command):
    def execute(self, args: list):
        if not args:
            print(c.warning("Take what?"))
            return
        item_name = " ".join(args).lower()
        room = self.engine_sys.state.rooms.get(self.engine_sys.state.player.current_room_id)
        
        for itm in list(room.items):
            if itm.name.lower() == item_name:
                room.items.remove(itm)
                self.engine_sys.state.player.inventory.append(itm)
                print(f"You picked up the {c.item_bold(itm.name)}.")
                self.engine_sys.event_bus.notify("item_taken", {"item_id": itm.id})
                return
        print(c.dim("I don't see that here."))

class InventoryCommand(Command):
    def execute(self, args: list):
        player = self.engine_sys.state.player
        print(f"HP: {c.hp_color(player.hp)}  |  Gold: {c.gold(player.gold)}")
        if not player.inventory:
            print(c.dim("Your inventory is empty."))
        else:
            print(c.bold("You are carrying:"))
            for itm in player.inventory:
                desc_parts = []
                if itm.stats:
                    if "damage" in itm.stats:
                        desc_parts.append(f"{c.damage('DMG:' + str(itm.stats['damage']))}")
                    if "heal" in itm.stats:
                        desc_parts.append(f"{c.success('HEAL:' + str(itm.stats['heal']))}")
                    if "defense" in itm.stats:
                        desc_parts.append(f"{c.defense_color('DEF:' + str(itm.stats['defense']))}")
                if itm.value > 0:
                    desc_parts.append(f"Value: {c.gold(itm.value)}")
                extra = f" ({', '.join(desc_parts)})" if desc_parts else ""
                print(f"  - {c.item(itm.name)}{extra}")

class EscapeCommand(Command):
    def execute(self, args: list):
        player = self.engine_sys.state.player
        if player.previous_room_id and player.previous_room_id in self.engine_sys.state.rooms:
            temp = player.current_room_id
            player.current_room_id = player.previous_room_id
            player.previous_room_id = temp
            print(c.warning("You hastily escape back to where you came from!"))
            self.engine_sys.event_bus.notify("room_enter", {"room_id": player.current_room_id})
            self.engine_sys._look()
            self.engine_sys._check_hostiles()
        else:
            print(c.error("You have nowhere to escape to!"))

class InspectCommand(Command):
    def execute(self, args: list):
        if not args:
            print(c.warning("Inspect what?"))
            return
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)
        
        # Check inventory first, then room
        items_to_check = player.inventory + room.items
        for itm in items_to_check:
            if itm.name.lower() == target:
                print(f"--- {c.item_bold(itm.name)} ---")
                print(c.narration(itm.description))
                if itm.stats:
                    if "damage" in itm.stats:
                        print(f"Damage: {c.damage(str(itm.stats['damage']))}")
                    if "heal" in itm.stats:
                        print(f"Heals: {c.success(str(itm.stats['heal']) + ' HP')}")
                    if "defense" in itm.stats:
                        print(f"Defense: {c.defense_color(str(itm.stats['defense']))}")
                if itm.value > 0:
                    print(f"Value: {c.gold(itm.value)}")
                return
        print(c.dim("You don't see that to inspect."))

class AttackCommand(Command):
    def _get_player_defense(self):
        """Calculate total defense from equipped armor in inventory."""
        player = self.engine_sys.state.player
        total_defense = 0
        for itm in player.inventory:
            if itm.item_type == "armor" and "defense" in itm.stats:
                total_defense += itm.stats["defense"]
        return total_defense

    def execute(self, args: list):
        if not args:
            print(c.warning("Attack who?"))
            return
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)
        
        npc_target = None
        for n in room.npcs:
            if n.name.lower() == target:
                npc_target = n
                break
                
        if not npc_target:
            print(c.dim("They aren't here."))
            return

        # Calculate player damage (find highest weapon)
        dmg = 5 # base punch damage
        for itm in player.inventory:
            if itm.item_type == "weapon" and itm.stats.get("damage", 0) > dmg:
                dmg = itm.stats["damage"]

        npc_target.hp -= dmg
        print(f"You attack {c.enemy(npc_target.name)} for {c.damage(str(dmg))} damage! (Enemy HP: {c.damage(str(max(0, npc_target.hp)))})")
        
        if npc_target.hp <= 0:
            print(c.success(f"You defeated {npc_target.name}!"))
            # Drop gold reward
            gold_reward = getattr(npc_target, 'damage', 10) * 2
            player.gold += gold_reward
            print(f"  💰 You found {c.gold(gold_reward)} on the body!")
            room.npcs.remove(npc_target)
            self.engine_sys.event_bus.notify("npc_defeated", {"npc_id": npc_target.id})
        else:
            if npc_target.npc_type == "hostile":
                ret_dmg = getattr(npc_target, 'damage', 10)
                # Apply armor defense
                defense = self._get_player_defense()
                actual_dmg = max(1, ret_dmg - defense)
                player.hp -= actual_dmg
                if defense > 0:
                    print(f"{c.enemy(npc_target.name)} retaliates for {c.damage(str(ret_dmg))} damage! "
                          f"(Armor absorbs {c.defense_color(str(ret_dmg - actual_dmg))}. "
                          f"You take {c.damage(str(actual_dmg))}. Your HP: {c.hp_color(max(0, player.hp))})")
                else:
                    print(f"{c.enemy(npc_target.name)} retaliates for {c.damage(str(actual_dmg))} damage! (Your HP: {c.hp_color(max(0, player.hp))})")
                if player.hp <= 0:
                    print(c.error("You have been defeated... GAME OVER."))
                    self.engine_sys.can_play = False

class UseCommand(Command):
    def execute(self, args: list):
        if not args:
            print(c.warning("Use what?"))
            return
        
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        
        for itm in list(player.inventory):
            if itm.name.lower() == target:
                if getattr(itm, 'item_type', 'misc') == "consumable":
                    heal_amount = getattr(itm, 'stats', {}).get("heal", 0)
                    if heal_amount > 0:
                        player.hp = min(200, player.hp + heal_amount)
                        player.inventory.remove(itm)
                        print(f"You consumed the {c.item_bold(itm.name)}. It healed you for {c.success(str(heal_amount))} HP! (Current HP: {c.hp_color(player.hp)})")
                    else:
                        print(f"You used the {c.item(itm.name)}, but nothing happened.")
                    return
                else:
                    print(f"You can't consume or use the {c.item(itm.name)} that way.")
                    return
                    
        print(c.dim("You don't have that item in your inventory. Did you 'take' it first?"))


class TalkCommand(Command):
    """Interactive LLM-powered conversation with any NPC. Type 'bye' to exit."""

    def execute(self, args: list):
        if not args:
            print(c.warning("Talk to whom?"))
            return

        target_name = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        npc_target = None
        for n in room.npcs:
            if n.name.lower() == target_name:
                npc_target = n
                break

        if not npc_target:
            print(c.dim("They aren't here."))
            return

        # Show initial static dialogue as greeting
        npc_color = c.enemy if npc_target.npc_type == "hostile" else (c.merchant if npc_target.npc_type == "merchant" else c.info)
        print(f"\n{npc_color(npc_target.name)}: \"{c.narration(npc_target.dialogue)}\"")
        print(c.dim(f"(You are now talking to {npc_target.name}. Type 'bye' to end the conversation.)"))

        # Interactive LLM dialogue loop
        from engine.world_generator import WorldGenerator

        while True:
            try:
                user_input = input(f"\n{c.BOLD_CYAN}You> {c.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{c.dim('(Conversation ended.)')}")
                break

            if not user_input:
                continue

            if user_input.lower() in ("bye", "goodbye", "farewell", "leave"):
                print(f"\n{npc_color(npc_target.name)}: \"{c.narration('Farewell, traveler.')}\"")
                print(c.dim("(Conversation ended.)"))
                break

            # Stream the NPC's reply from Ollama
            print(f"\n{npc_color(npc_target.name)}: \"", end="", flush=True)
            try:
                WorldGenerator.chat_with_npc(
                    npc_name=npc_target.name,
                    npc_description=npc_target.description,
                    npc_type=npc_target.npc_type,
                    user_message=user_input
                )
                print("\"")  # Close the quote
            except Exception as e:
                print(f"\"\n{c.dim(f'({npc_target.name} seems lost in thought... [{e}])')}")


class BuyCommand(Command):
    """Buy items from a merchant NPC in the current room."""

    def execute(self, args: list):
        if not args:
            print(c.warning("Buy what? Check the merchant's wares first with 'shop'."))
            return

        item_name = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        # Find a merchant in the room
        merchant_npc = None
        for n in room.npcs:
            if getattr(n, 'npc_type', 'neutral') == 'merchant':
                merchant_npc = n
                break

        if not merchant_npc:
            print(c.dim("There is no merchant here to buy from."))
            return

        # Find the item in the room
        target_item = None
        for itm in room.items:
            if itm.name.lower() == item_name:
                target_item = itm
                break

        if not target_item:
            print(c.dim(f"The merchant doesn't have '{item_name}' for sale."))
            return

        price = target_item.value
        if price <= 0:
            price = 10  # Minimum price

        if player.gold < price:
            print(f"{c.merchant(merchant_npc.name)}: \"You don't have enough gold! This costs {c.gold(price)}.\"")
            print(f"  Your gold: {c.gold(player.gold)}")
            return

        # Complete purchase
        player.gold -= price
        room.items.remove(target_item)
        player.inventory.append(target_item)
        print(f"  💰 You bought {c.item_bold(target_item.name)} for {c.gold(price)}!")
        print(f"  Remaining gold: {c.gold(player.gold)}")


class SellCommand(Command):
    """Sell items to a merchant NPC in the current room."""

    def execute(self, args: list):
        if not args:
            print(c.warning("Sell what? Check your inventory with 'inv'."))
            return

        item_name = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        # Find a merchant in the room
        merchant_npc = None
        for n in room.npcs:
            if getattr(n, 'npc_type', 'neutral') == 'merchant':
                merchant_npc = n
                break

        if not merchant_npc:
            print(c.dim("There is no merchant here to sell to."))
            return

        # Find the item in inventory
        target_item = None
        for itm in player.inventory:
            if itm.name.lower() == item_name:
                target_item = itm
                break

        if not target_item:
            print(c.dim(f"You don't have '{item_name}' in your inventory."))
            return

        sell_price = max(1, target_item.value // 2)  # Sell for half value

        player.gold += sell_price
        player.inventory.remove(target_item)
        room.items.append(target_item)
        print(f"  💰 You sold {c.item_bold(target_item.name)} for {c.gold(sell_price)}!")
        print(f"  Current gold: {c.gold(player.gold)}")


class ShopCommand(Command):
    """Show the merchant's available wares in the current room."""

    def execute(self, args: list):
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        # Find a merchant in the room
        merchant_npc = None
        for n in room.npcs:
            if getattr(n, 'npc_type', 'neutral') == 'merchant':
                merchant_npc = n
                break

        if not merchant_npc:
            print(c.dim("There is no merchant here."))
            return

        shop_title = "═══ " + merchant_npc.name + "'s Shop ═══"
        print(f"\n{c.merchant(shop_title)}")
        print(f"Your gold: {c.gold(player.gold)}\n")

        if not room.items:
            print(c.dim("  The merchant has nothing left to sell."))
        else:
            for itm in room.items:
                price = itm.value if itm.value > 0 else 10
                stats_str = ""
                if itm.stats:
                    parts = []
                    if "damage" in itm.stats:
                        parts.append(f"DMG:{itm.stats['damage']}")
                    if "heal" in itm.stats:
                        parts.append(f"HEAL:{itm.stats['heal']}")
                    if "defense" in itm.stats:
                        parts.append(f"DEF:{itm.stats['defense']}")
                    stats_str = f" ({', '.join(parts)})" if parts else ""
                print(f"  {c.item(itm.name)}{stats_str} — {c.gold(price)}")

        print(f"\n{c.dim('Use \"buy <item>\" to purchase or \"sell <item>\" to sell.')}")


class MapCommand(Command):
    """Renders an ASCII map of the world graph, highlighting the player's current room."""

    DIR_OFFSETS = {
        "north": (-1, 0),
        "south": (1, 0),
        "east": (0, 1),
        "west": (0, -1),
    }

    def execute(self, args: list):
        state = self.engine_sys.state
        if not state.rooms:
            print("No map data available.")
            return

        # 1. Place rooms on a grid using BFS from the player's current room
        grid = {}
        placed = {}
        queue = [state.player.current_room_id]
        placed[state.player.current_room_id] = (0, 0)
        grid[(0, 0)] = state.rooms[state.player.current_room_id]

        while queue:
            current_id = queue.pop(0)
            current_pos = placed[current_id]
            room = state.rooms.get(current_id)
            if not room:
                continue

            for direction, target_id in room.exits.items():
                if target_id in placed:
                    continue
                offset = self.DIR_OFFSETS.get(direction)
                if not offset:
                    continue
                new_pos = (current_pos[0] + offset[0], current_pos[1] + offset[1])

                attempts = 0
                while new_pos in grid and attempts < 5:
                    new_pos = (new_pos[0] + offset[0], new_pos[1] + offset[1])
                    attempts += 1

                if new_pos not in grid and target_id in state.rooms:
                    grid[new_pos] = state.rooms[target_id]
                    placed[target_id] = new_pos
                    queue.append(target_id)

        max_col = max(col for _, col in grid.keys()) if grid else 0
        for room_id, room in state.rooms.items():
            if room_id not in placed:
                max_col += 2
                pos = (0, max_col)
                grid[pos] = room
                placed[room_id] = pos

        min_r = min(r for r, _ in grid.keys())
        max_r = max(r for r, _ in grid.keys())
        min_c = min(col for _, col in grid.keys())
        max_c = max(col for _, col in grid.keys())

        CELL_W = 22
        CELL_H = 3
        CONN_H = 1
        CONN_W = 4

        total_cols = max_c - min_c + 1
        total_rows = max_r - min_r + 1
        canvas_w = total_cols * CELL_W + (total_cols - 1) * CONN_W
        canvas_h = total_rows * CELL_H + (total_rows - 1) * CONN_H

        canvas = [[" "] * canvas_w for _ in range(canvas_h)]

        def draw_text(row, col, text):
            for i, ch in enumerate(text):
                if 0 <= row < canvas_h and 0 <= col + i < canvas_w:
                    canvas[row][col + i] = ch

        player_room_id = state.player.current_room_id

        for (gr, gc), room in grid.items():
            canvas_col = (gc - min_c) * (CELL_W + CONN_W)
            canvas_row = (gr - min_r) * (CELL_H + CONN_H)

            is_current = (room.id == player_room_id)
            name = room.name[:CELL_W - 4]
            if is_current:
                label = f"[*{name}*]"
            else:
                label = f"[ {name} ]"

            padded = label.center(CELL_W)

            draw_text(canvas_row, canvas_col, "+" + "-" * (CELL_W - 2) + "+")
            draw_text(canvas_row + 1, canvas_col, "|" + padded[1:-1] + "|")
            draw_text(canvas_row + 2, canvas_col, "+" + "-" * (CELL_W - 2) + "+")

            for direction, target_id in room.exits.items():
                if target_id not in placed:
                    continue

                if direction == "south":
                    cx = canvas_col + CELL_W // 2
                    cy = canvas_row + CELL_H
                    if 0 <= cy < canvas_h:
                        draw_text(cy, cx, "|")
                elif direction == "north":
                    cx = canvas_col + CELL_W // 2
                    cy = canvas_row - 1
                    if 0 <= cy < canvas_h:
                        draw_text(cy, cx, "|")
                elif direction == "east":
                    cx = canvas_col + CELL_W
                    cy = canvas_row + 1
                    for i in range(CONN_W):
                        if 0 <= cx + i < canvas_w:
                            draw_text(cy, cx + i, "-")
                elif direction == "west":
                    cx = canvas_col - CONN_W
                    cy = canvas_row + 1
                    for i in range(CONN_W):
                        if 0 <= cx + i < canvas_w:
                            draw_text(cy, cx + i, "-")

        # Print the colored map
        print(f"\n{c.BOLD_CYAN}🗺️  WORLD MAP{c.RESET}  {c.dim('(You are at [*...*])')}")
        print(c.DIM + "=" * min(canvas_w, 60) + c.RESET)
        for row in canvas:
            line = "".join(row).rstrip()
            if line:
                # Color the current room marker
                line = line.replace("[*", f"{c.BOLD_GREEN}[*").replace("*]", f"*]{c.RESET}")
                print(line)
        print(c.DIM + "=" * min(canvas_w, 60) + c.RESET)
