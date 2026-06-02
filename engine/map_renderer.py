from engine import colors as c
from engine.ui import console

class MapRenderer:
    """Handles rendering the ASCII map graph for the terminal."""
    
    DIR_OFFSETS = {
        "north": (-1, 0),
        "south": (1, 0),
        "east": (0, 1),
        "west": (0, -1),
    }

    @classmethod
    def render(cls, state):
        if not state.rooms:
            console.print("No map data available.")
            return

        # 1. Place rooms on a grid using BFS from the player's current room
        grid = {}
        placed = {}
        player_room_id = state.player.current_room_id
        queue = [player_room_id]
        
        placed[player_room_id] = (0, 0)
        grid[(0, 0)] = state.rooms[player_room_id]

        while queue:
            current_id = queue.pop(0)
            current_pos = placed[current_id]
            room = state.rooms.get(current_id)
            if not room:
                continue

            for direction, target_id in room.exits.items():
                if target_id in placed:
                    continue
                offset = cls.DIR_OFFSETS.get(direction)
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

        # 2. Place disconnected rooms
        max_col = max(col for _, col in grid.keys()) if grid else 0
        for room_id, room in state.rooms.items():
            if room_id not in placed:
                max_col += 2
                pos = (0, max_col)
                grid[pos] = room
                placed[room_id] = pos

        # 3. Calculate canvas size
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

        # 4. Draw rooms and connections onto canvas
        for (gr, gc), room in grid.items():
            canvas_col = (gc - min_c) * (CELL_W + CONN_W)
            canvas_row = (gr - min_r) * (CELL_H + CONN_H)

            is_current = (room.id == player_room_id)
            name = room.name[:CELL_W - 4]
            label = f"[*{name}*]" if is_current else f"[ {name} ]"
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

        # 5. Print the colored map
        console.print("\n[bold cyan]🗺️  WORLD MAP[/]  [dim](You are at \\[[green]*...*[/green]])[/]")
        console.print(f"[dim]{'=' * min(canvas_w, 60)}[/]")
        for row in canvas:
            line = "".join(row).rstrip()
            if line:
                from rich.text import Text
                if "[*" in line and "*]" in line:
                    start = line.find("[*")
                    end = line.find("*]") + 2
                    text = Text(line[:start])
                    text.append(line[start:end], style="bold green")
                    text.append(line[end:])
                    console.print(text)
                else:
                    console.print(Text(line))
        console.print(f"[dim]{'=' * min(canvas_w, 60)}[/]")
