from abc import ABC, abstractmethod
from engine import colors as c
from engine.ui import console, print_hp_bar
from engine.map_renderer import MapRenderer
from engine.quest_system import QuestSystem
from rich.table import Table
from rich.panel import Panel

# Alias print to console.print for easy migration
print = console.print

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
        
        itm = room.get_item_by_name(item_name)
        if itm:
            room.items.remove(itm)
            self.engine_sys.state.player.inventory.append(itm)
            print(f"You picked up the {c.item_bold(itm.name)}.")
            self.engine_sys.event_bus.notify("item_taken", {"item_id": itm.id})
            # Check collect quests
            QuestSystem.check_quest_completion(self.engine_sys, 'item_taken', itm.id)
        else:
            print(c.dim("I don't see that here."))

class InventoryCommand(Command):
    def execute(self, args: list):
        player = self.engine_sys.state.player
        from rich.rule import Rule
        from rich.text import Text

        # Header bar with HP + Gold
        console.print(Rule("[bold cyan]⚔  CHARACTER STATUS  ⚔[/]", style="cyan"))
        console.print(print_hp_bar(player.hp, max_hp=200, label="HP"))
        console.print(f"  💰 Gold: {c.gold(player.gold)}")
        console.print()

        if not player.inventory:
            console.print(Panel(
                Text("Your pack is empty. Explore the world to find items!", style="dim italic"),
                title="[bold yellow]🎒 Inventory[/]",
                border_style="yellow",
                expand=False
            ))
        else:
            from engine.ascii_art import get_item_icon
            table = Table(
                title="🎒 Inventory",
                show_header=True,
                header_style="bold yellow",
                border_style="yellow",
                show_lines=True,
            )
            table.add_column("", justify="center", width=4)  # icon
            table.add_column("Item", style="bold yellow", no_wrap=True)
            table.add_column("Type", justify="center", style="dim")
            table.add_column("Stats", justify="left")
            table.add_column("Value", justify="right", style="bold gold1")

            for itm in player.inventory:
                icon = get_item_icon(itm.name)
                desc_parts = []
                if itm.stats:
                    if "damage" in itm.stats:
                        desc_parts.append(Text.from_markup(f"⚔  {c.damage('DMG: ' + str(itm.stats['damage']))}"))
                    if "heal" in itm.stats:
                        desc_parts.append(Text.from_markup(f"❤  {c.success('HEAL: ' + str(itm.stats['heal']))}"))
                    if "defense" in itm.stats:
                        desc_parts.append(Text.from_markup(f"🛡  {c.defense_color('DEF: ' + str(itm.stats['defense']))}"))

                stats_text = Text("  ").join(desc_parts) if desc_parts else Text("-", style="dim")
                val_str = f"{itm.value}g" if itm.value > 0 else "-"
                table.add_row(icon, itm.name, itm.item_type.capitalize(), stats_text, val_str)

            console.print(table)

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
        itm = player.get_item_by_name(target) or room.get_item_by_name(target)
        
        if itm:
            from engine.ascii_art import get_item_art
            from rich.columns import Columns
            from rich.text import Text
            
            art = get_item_art(itm.name)
            art_panel = Panel(Text(art.strip('\n'), style="bold yellow"), border_style="yellow")

            content = Text()
            content.append(f"{itm.description}\n\n", style="italic white")
            
            if itm.stats:
                if "damage" in itm.stats:
                    content.append(Text.from_markup(f"Damage: {c.damage(str(itm.stats['damage']))}\n"))
                if "heal" in itm.stats:
                    content.append(Text.from_markup(f"Heals: {c.success(str(itm.stats['heal']) + ' HP')}\n"))
                if "defense" in itm.stats:
                    content.append(Text.from_markup(f"Defense: {c.defense_color(str(itm.stats['defense']))}\n"))
            if itm.value > 0:
                content.append(Text.from_markup(f"Value: {c.gold(itm.value)}"))
            
            stats_panel = Panel(content, title=c.item_bold(itm.name), border_style="yellow", expand=False)
            
            console.print(Columns([art_panel, stats_panel]))
        else:
            print(c.dim("You don't see that to inspect."))

class AttackCommand(Command):
    # Dramatic attack flavour messages
    _ATTACK_VERBS = ["slash", "strike", "hammer", "cleave", "pierce", "pummel"]
    _KILL_MSGS = [
        "falls to their knees and collapses!",
        "lets out a final shriek and crumbles!",
        "shatters into pieces!",
        "is vanquished in a blaze of glory!",
    ]

    def execute(self, args: list):
        import random
        from rich.rule import Rule

        if not args:
            print(c.warning("Attack who?"))
            return
        target = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        npc_target = room.get_npc_by_name(target)

        if not npc_target:
            print(c.dim("They aren't here."))
            return

        dmg = player.get_total_damage()
        npc_target.hp -= dmg
        verb = random.choice(self._ATTACK_VERBS)
        print(
            f"  ⚔️  You {verb} {c.enemy(npc_target.name)} for "
            f"{c.damage(str(dmg))} damage!  [Enemy HP: {c.damage(str(max(0, npc_target.hp)))}]"
        )

        if npc_target.hp <= 0:
            kill_msg = random.choice(self._KILL_MSGS)
            console.print(Rule(f"[bold yellow]☠  {npc_target.name} {kill_msg}[/]", style="yellow"))
            gold_reward = getattr(npc_target, 'damage', 10) * 2
            player.gold += gold_reward
            print(f"  💰 You loot {c.gold(gold_reward)} from the fallen enemy!")
            room.npcs.remove(npc_target)
            self.engine_sys.event_bus.notify("npc_defeated", {"npc_id": npc_target.id})
            QuestSystem.check_quest_completion(self.engine_sys, 'npc_killed', npc_target.id)
        else:
            if npc_target.npc_type == "hostile":
                ret_dmg = getattr(npc_target, 'damage', 10)
                defense = player.get_total_defense()
                actual_dmg = max(1, ret_dmg - defense)
                player.hp -= actual_dmg
                if defense > 0:
                    print(
                        f"  💥 {c.enemy(npc_target.name)} retaliates for {c.damage(str(ret_dmg))}! "
                        f"[Shield absorbs {c.defense_color(str(ret_dmg - actual_dmg))}] "
                        f"→ You take {c.damage(str(actual_dmg))}  |  HP: {c.hp_color(max(0, player.hp))}"
                    )
                else:
                    print(
                        f"  💥 {c.enemy(npc_target.name)} hits you for {c.damage(str(actual_dmg))}!  "
                        f"|  HP: {c.hp_color(max(0, player.hp))}"
                    )
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
        
        itm = player.get_item_by_name(target)
        if itm:
            if getattr(itm, 'item_type', 'misc') == "consumable":
                heal_amount = getattr(itm, 'stats', {}).get("heal", 0)
                if heal_amount > 0:
                    player.hp = min(200, player.hp + heal_amount)
                    player.inventory.remove(itm)
                    print(f"You consumed the {c.item_bold(itm.name)}. It healed you for {c.success(str(heal_amount))} HP! (Current HP: {c.hp_color(player.hp)})")
                else:
                    print(f"You used the {c.item(itm.name)}, but nothing happened.")
            else:
                print(f"You can't consume or use the {c.item(itm.name)} that way.")
        else:
            print(c.dim("You don't have that item in your inventory. Did you 'take' it first?"))


class TalkCommand(Command):
    """Interactive LLM-powered conversation with any NPC. Type 'bye' to exit."""

    def _offer_quests(self, npc_target, npc_color):
        """Check if this NPC has available quests to offer."""
        player = self.engine_sys.state.player
        quests = self.engine_sys.state.quests
        offered = False

        for quest in quests.values():
            if quest.giver_npc_id != npc_target.id:
                continue
            if quest.status != 'available':
                continue
            if quest.id in player.active_quests or quest.id in player.completed_quests:
                continue

            # Offer the quest
            console.print(f"\n[bold cyan]📜 QUEST AVAILABLE:[/] {c.bold(quest.name)}")
            console.print(f"   {c.narration(quest.description)}")
            console.print(f"   Reward: {c.gold(quest.reward_gold)}")
            try:
                answer = console.input(f"   Accept this quest? ([bold green]yes[/]/[red]no[/]): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = 'no'

            if answer in ('yes', 'y', 'evet', 'accept'):
                quest.status = 'active'
                player.active_quests.append(quest.id)
                print(f"   {c.success('✅ Quest accepted!')}")
                offered = True
            else:
                print(f"   {c.dim('Quest declined.')}")

        return offered

    def _check_deliver_quests(self, npc_target, npc_color):
        """Check if the player can complete a deliver quest with this NPC."""
        player = self.engine_sys.state.player
        quests = self.engine_sys.state.quests

        for q_id in list(player.active_quests):
            quest = quests.get(q_id)
            if not quest or quest.quest_type != 'deliver':
                continue
            if quest.deliver_to != npc_target.id:
                continue

            # Check if player has the required item
            itm = player.get_item_by_name(quest.target_id)
            if itm:
                player.inventory.remove(itm)
                print(f"\n  You hand over the {c.item_bold(itm.name)} to {npc_color(npc_target.name)}.")
                QuestSystem.complete_quest(player, quest)

    def execute(self, args: list):
        if not args:
            print(c.warning("Talk to whom?"))
            return

        target_name = " ".join(args).lower()
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        npc_target = room.get_npc_by_name(target_name)

        if not npc_target:
            print(c.dim("They aren't here."))
            return

        # Show initial static dialogue as greeting
        npc_color = c.enemy if npc_target.npc_type == "hostile" else (c.merchant if npc_target.npc_type == "merchant" else c.info)
        print(f"\n{npc_color(npc_target.name)}: \"{c.narration(npc_target.dialogue)}\"")

        # Check for deliver quest completion
        self._check_deliver_quests(npc_target, npc_color)

        # Offer available quests from this NPC
        self._offer_quests(npc_target, npc_color)

        # Enter interactive chat loop
        console.print(f"(You are now talking to {npc_target.name}. Type 'bye' to end the conversation.)")
        from engine.world_generator import WorldGenerator

        while True:
            try:
                user_input = console.input("\n[bold cyan]You>[/] ").strip()
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
            console.print(f"\n{npc_color(npc_target.name)}: \"", end="")
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

        merchant_npc = room.get_merchant()

        if not merchant_npc:
            print(c.dim("There is no merchant here to buy from."))
            return

        target_item = room.get_item_by_name(item_name)

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

        merchant_npc = room.get_merchant()

        if not merchant_npc:
            print(c.dim("There is no merchant here to sell to."))
            return

        target_item = player.get_item_by_name(item_name)

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
    """View items available to buy in the current room."""

    def execute(self, args: list):
        player = self.engine_sys.state.player
        room = self.engine_sys.state.rooms.get(player.current_room_id)

        merchant_npc = room.get_merchant()

        if not merchant_npc:
            print(c.dim("There is no merchant here."))
            return

        print(f"\n{c.merchant('═══ ' + merchant_npc.name + '\'s Shop ═══')}")
        print(f"Your gold: {c.gold(player.gold)}\n")

        wares = self.engine_sys.state.items
        shop_items = [itm for itm in wares.values() if itm.value > 0 and itm.item_type != 'misc']
        shop_items = shop_items[:5]

        if not shop_items:
            print(c.dim("The merchant has nothing to sell right now."))
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Item", style="yellow")
        table.add_column("Stats", justify="left")
        table.add_column("Price", justify="right")

        for itm in shop_items:
            desc_parts = []
            if itm.stats:
                if "damage" in itm.stats:
                    desc_parts.append(f"{c.damage('DMG:' + str(itm.stats['damage']))}")
                if "heal" in itm.stats:
                    desc_parts.append(f"{c.success('HEAL:' + str(itm.stats['heal']))}")
                if "defense" in itm.stats:
                    desc_parts.append(f"{c.defense_color('DEF:' + str(itm.stats['defense']))}")
            stats_str = ", ".join(desc_parts) if desc_parts else "-"
            table.add_row(itm.name, stats_str, f"{itm.value}g")

        console.print(table)
        print(c.dim("\nUse 'buy <item>' to purchase or 'sell <item>' to sell."))


class MapCommand(Command):
    """Renders an ASCII map of the world graph, highlighting the player's current room."""

    def execute(self, args: list):
        MapRenderer.render(self.engine_sys.state)


class QuestsCommand(Command):
    """Shows the player's active and completed quests."""

    def execute(self, args: list):
        player = self.engine_sys.state.player
        quests = self.engine_sys.state.quests

        active = [quests[q_id] for q_id in player.active_quests if q_id in quests]
        if active:
            table = Table(title="📜 Active Quests", show_header=True, header_style="bold cyan", expand=True)
            table.add_column("Type", justify="center", style="bold")
            table.add_column("Quest", style="yellow")
            table.add_column("Description", style="italic white")
            table.add_column("Status", justify="center")
            table.add_column("Reward", justify="right")

            for quest in active:
                type_icon = {"kill": "⚔️", "collect": "🎒", "deliver": "📦"}.get(quest.quest_type, "❓")
                
                # Show progress hint
                if quest.quest_type == "kill":
                    target_alive = quest.target_id in self.engine_sys.state.npcs
                    status = c.damage("Not defeated yet") if target_alive else c.success("Target eliminated!")
                elif quest.quest_type == "collect":
                    has_item = any(itm.id == quest.target_id for itm in player.inventory)
                    status = c.success("Item collected!") if has_item else c.damage("Item not found yet")
                elif quest.quest_type == "deliver":
                    has_item = any(itm.id == quest.target_id for itm in player.inventory)
                    if has_item:
                        deliver_npc = self.engine_sys.state.npcs.get(quest.deliver_to)
                        npc_name = deliver_npc.name if deliver_npc else quest.deliver_to
                        status = c.warning(f"Deliver to {npc_name}")
                    else:
                        status = c.damage("Item not found yet")
                
                table.add_row(type_icon, quest.name, quest.description, status, f"{quest.reward_gold}g")
            console.print(table)
        else:
            console.print(Panel("No active quests. Talk to NPCs to find quests!", title="📜 Quest Journal", border_style="dim"))

        # Completed quests
        completed = [quests[q_id] for q_id in player.completed_quests if q_id in quests]
        if completed:
            comp_table = Table(title="✅ Completed Quests", show_header=False, header_style="bold green")
            comp_table.add_column("Icon")
            comp_table.add_column("Quest", style="dim")
            for quest in completed:
                comp_table.add_row("✅", quest.name)
            console.print(comp_table)
