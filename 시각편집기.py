from tkinter import *
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from datetime import datetime
import re

using_font = "맑은 고딕"  # 사용할 폰트
textsize = 15  # 폰트 크기

TABLE_ROW_LIMIT = 20
TABLE_COLUMN_LIMIT = 20


def format_table_cell(content, alignment="center", spans=None,
                      attributes=None, table_attributes=None):
    spans = spans or {}
    attributes = attributes or {}
    table_attributes = table_attributes or {}
    content = content.strip()

    prefixes = []
    col_span = max(1, int(spans.get("col", 1)))
    row_span = max(1, int(spans.get("row", 1)))
    if col_span > 1:
        prefixes.append(f"<-{col_span}>")
    if row_span > 1:
        prefixes.append(f"<|{row_span}>")

    for name, value in attributes.items():
        prefixes.append(f"<{name}={value}>")
    for name, value in table_attributes.items():
        prefixes.append(f"<{name}={value}>")

    prefix = "".join(prefixes)
    if alignment == "left":
        return f"{prefix}{content} "
    if alignment == "right":
        return f"{prefix} {content}"
    return f"{prefix} {content} "


TABLE_TEXT_STYLES = ("bold", "italic", "underline", "strikethrough", "footnote")


def get_styled_text(widget):
    result = []
    for index in range(1, int(widget.index("end-1c").split(".")[0]) + 1):
        line_start = f"{index}.0"
        line_end = widget.index(f"{line_start} lineend")
        line_text = widget.get(line_start, line_end)
        char_index = 0

        while char_index < len(line_text):
            position = f"{line_start}+{char_index}c"
            tags = set(widget.tag_names(position))
            segment = ""

            while char_index < len(line_text):
                next_position = f"{line_start}+{char_index}c"
                if set(widget.tag_names(next_position)) != tags:
                    break
                segment += line_text[char_index]
                char_index += 1

            if "bold" in tags:
                segment = f"'''{segment}'''"
            if "italic" in tags:
                segment = f"''{segment}''"
            if "underline" in tags:
                segment = f"__{segment}__"
            if "strikethrough" in tags:
                segment = f"--{segment}--"
            if "footnote" in tags:
                segment = f"[* {segment}]"
            result.append(segment)

        if index < int(widget.index("end-1c").split(".")[0]):
            result.append("\n")

    return "".join(result)


def generate_namumark_table(rows, cols, cells, table_attributes=None):
    table_attributes = table_attributes or {}
    occupied = [[False for _ in range(cols)] for _ in range(rows)]
    lines = []
    table_attributes_added = False

    for row in range(rows):
        line_cells = []
        for col in range(cols):
            if occupied[row][col]:
                continue

            cell = cells.get((row, col), {
                "content": "",
                "alignment": "center",
                "col_span": 1,
                "row_span": 1,
                "attributes": {},
            })
            col_span = max(1, min(int(cell.get("col_span", 1)), cols - col))
            row_span = max(1, min(int(cell.get("row_span", 1)), rows - row))

            for span_row in range(row, row + row_span):
                for span_col in range(col, col + col_span):
                    occupied[span_row][span_col] = True

            cell_table_attributes = {}
            if not table_attributes_added:
                cell_table_attributes = table_attributes
                table_attributes_added = True

            line_cells.append(format_table_cell(
                cell.get("content", ""),
                alignment=cell.get("alignment", "center"),
                spans={"col": col_span, "row": row_span},
                attributes=cell.get("attributes", {}),
                table_attributes=cell_table_attributes,
            ))

        if line_cells:
            lines.append("||" + "||".join(line_cells) + "||")

    return "\n".join(lines)


def parse_namumark_table(table_text):
    lines = [line for line in table_text.strip().splitlines() if line.strip()]
    rows = len(lines)
    cells = {}
    occupied = [set() for _ in range(rows)]
    cols = 0
    for row, line in enumerate(lines):
        parts = re.split(r"\|\|", line)
        if parts and parts[0] == "":
            parts.pop(0)
        if parts and parts[-1] == "":
            parts.pop()
        col = 0
        for part in parts:
            while col in occupied[row]:
                col += 1
            raw_part = part
            alignment_part = raw_part
            while alignment_part.startswith("<") and ">" in alignment_part:
                alignment_part = alignment_part[alignment_part.index(">") + 1:]
            part = part.strip()
            col_span = 1
            row_span = 1
            while True:
                match = re.match(r"<-(\d+)>\s*", part)
                if not match:
                    break
                col_span = int(match.group(1))
                part = part[match.end():]
            while True:
                match = re.match(r"<\|(\d+)>\s*", part)
                if not match:
                    break
                row_span = int(match.group(1))
                part = part[match.end():]
            alignment = "center"
            if alignment_part.startswith(" ") and not alignment_part.endswith(" "):
                alignment = "right"
            elif alignment_part.endswith(" ") and not alignment_part.startswith(" "):
                alignment = "left"
            content = part.strip()
            cells[(row, col)] = {
                "content": content,
                "alignment": alignment,
                "col_span": col_span,
                "row_span": row_span,
                "attributes": {},
            }
            for span_row in range(row, min(rows, row + row_span)):
                for span_col in range(col, col + col_span):
                    occupied[span_row].add(span_col)
            col += col_span
            cols = max(cols, col)
    return rows, cols, cells


def open_table_dialog(existing_model=None, replace_range=None):
    dialog = Toplevel(window)
    dialog.title("표 수정" if existing_model else "표 삽입")
    dialog.transient(window)
    dialog.geometry("900x600")

    initial_rows = existing_model[0] if existing_model else 2
    initial_cols = existing_model[1] if existing_model else 2
    initial_cells = existing_model[2] if existing_model else {}

    size_frame = Frame(dialog)
    size_frame.pack(padx=10, pady=10, fill="x")
    row_var = StringVar(value=str(initial_rows))
    column_var = StringVar(value=str(initial_cols))
    Label(size_frame, text="행").pack(side="left")
    ttk.Spinbox(size_frame, from_=1, to=TABLE_ROW_LIMIT,
                textvariable=row_var, width=5).pack(side="left", padx=(5, 15))
    Label(size_frame, text="열").pack(side="left")
    ttk.Spinbox(size_frame, from_=1, to=TABLE_COLUMN_LIMIT,
                textvariable=column_var, width=5).pack(side="left", padx=(5, 15))

    toolbar = Frame(dialog)
    toolbar.pack(fill="x", padx=10, pady=(0, 8))

    ttk.Button(toolbar, text="셀 병합", command=lambda: merge_selection()).pack(side="left")
    ttk.Button(toolbar, text="병합 해제", command=lambda: unmerge_selection()).pack(
        side="left", padx=(5, 12))

    active_cell = {"position": (0, 0)}
    selection = {"anchor": (0, 0), "extent": (0, 0)}
    edit_cell = {"position": None}
    last_click = {"position": None, "time": 0}
    cell_widgets = {}
    cell_data = {}

    for row in range(initial_rows):
        for column in range(initial_cols):
            saved = initial_cells.get((row, column), {})
            cell_data[(row, column)] = {
                "alignment": saved.get("alignment", "center"),
                "col_span": saved.get("col_span", 1),
                "row_span": saved.get("row_span", 1),
                "attributes": saved.get("attributes", {}),
            }
    for (row, column), saved in initial_cells.items():
        row_span = saved.get("row_span", 1)
        col_span = saved.get("col_span", 1)
        for covered_row in range(row, min(initial_rows, row + row_span)):
            for covered_column in range(column, min(initial_cols, column + col_span)):
                if (covered_row, covered_column) != (row, column):
                    cell_data[(covered_row, covered_column)]["covered_by"] = (row, column)

    dialog_window = Frame(dialog)
    dialog_window.pack(padx=10, pady=(0, 10), fill="both", expand=True)
    grid_canvas = Canvas(dialog_window)
    y_scroll = ttk.Scrollbar(dialog_window, orient="vertical", command=grid_canvas.yview)
    x_scroll = ttk.Scrollbar(dialog_window, orient="horizontal", command=grid_canvas.xview)
    grid_canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    grid_canvas.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")
    dialog_window.grid_rowconfigure(0, weight=1)
    dialog_window.grid_columnconfigure(0, weight=1)

    grid_frame = Frame(grid_canvas)
    grid_canvas.create_window((0, 0), window=grid_frame, anchor="nw", tags="grid")
    grid_window_id = grid_canvas.find_withtag("grid")[0]

    def toggle_cell_style(cell_text, tag):
        try:
            current_tags = set(cell_text.tag_names("sel.first"))
            if tag in current_tags:
                cell_text.tag_remove(tag, "sel.first", "sel.last")
            else:
                cell_text.tag_add(tag, "sel.first", "sel.last")
        except TclError:
            messagebox.showerror("오류", "셀에서 서식을 적용할 텍스트를 선택해 주세요.")

    def apply_cell_alignment(cell_text, alignment):
        justify = {"left": "left", "center": "center", "right": "right"}[alignment]
        cell_text.tag_configure("cell_alignment", justify=justify)
        cell_text.tag_add("cell_alignment", "1.0", "end")

    def apply_active_style(tag):
        position = active_cell["position"]
        widgets = cell_widgets.get(position)
        if widgets:
            toggle_cell_style(widgets["content"], tag)

    def set_active_alignment(alignment):
        position = active_cell["position"]
        if position in cell_data:
            cell_data[position]["alignment"] = alignment
            apply_cell_alignment(cell_widgets[position]["content"], alignment)

    alignment_var = StringVar(value="center")
    ttk.Label(toolbar, text="정렬").pack(side="left", padx=(0, 3))
    alignment_combo = ttk.Combobox(
        toolbar, textvariable=alignment_var,
        values=("left", "center", "right"), state="readonly", width=8
    )
    alignment_combo.pack(side="left", padx=(0, 8))
    alignment_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: set_active_alignment(alignment_var.get()),
    )
    for tag, label in (
        ("bold", "볼드"), ("italic", "이탤릭"), ("underline", "밑줄"),
        ("strikethrough", "취소선"), ("footnote", "각주"),
    ):
        ttk.Button(
            toolbar, text=label, width=6,
            command=lambda style=tag: apply_active_style(style),
        ).pack(side="left", padx=1)

    def selected_bounds():
        anchor_row, anchor_col = selection["anchor"]
        end_row, end_col = selection["extent"]
        return (
            min(anchor_row, end_row), min(anchor_col, end_col),
            max(anchor_row, end_row), max(anchor_col, end_col),
        )

    def update_selection(position):
        selection["extent"] = position
        active_cell["position"] = position
        alignment_var.set(cell_data.get(position, {}).get("alignment", "center"))
        top, left, bottom, right = selected_bounds()
        for (row, column), widgets in cell_widgets.items():
            if row >= top and row <= bottom and column >= left and column <= right:
                widgets["frame"].configure(bg="#cfe5ff")
                widgets["content"].configure(bg="#eaf4ff")
            else:
                widgets["frame"].configure(bg="white")
                widgets["content"].configure(bg="white")

    def begin_selection(event, position):
        if edit_cell["position"] == position:
            return None
        if (last_click["position"] == position
                and 0 <= event.time - last_click["time"] <= 500):
            edit_cell["position"] = position
            active_cell["position"] = position
            return None

        last_click["position"] = position
        last_click["time"] = event.time
        edit_cell["position"] = None
        selection["anchor"] = position
        update_selection(position)
        cell_widgets[position]["content"].focus_set()
        return "break"

    def extend_selection(event):
        position = None
        for coordinate, widgets in cell_widgets.items():
            frame = widgets["frame"]
            if frame.winfo_manager() != "grid":
                continue
            left = frame.winfo_rootx()
            top = frame.winfo_rooty()
            if (left <= event.x_root < left + frame.winfo_width()
                    and top <= event.y_root < top + frame.winfo_height()):
                position = coordinate
                break

        if position is None:
            return "break"
        if edit_cell["position"] == position:
            return None
        edit_cell["position"] = None
        update_selection(position)
        return "break"

    def handle_cell_key(event, position, cell_text):
        if edit_cell["position"] == position:
            return None
        if event.keysym == "F2" or event.keysym == "Return":
            edit_cell["position"] = position
            cell_text.mark_set(INSERT, "end-1c")
            return "break"
        if event.char and event.char.isprintable() and not (event.state & 0x0004):
            cell_text.delete("1.0", "end")
            cell_text.insert("1.0", event.char)
            cell_text.mark_set(INSERT, "end-1c")
            edit_cell["position"] = position
            return "break"
        if event.keysym in ("BackSpace", "Delete"):
            cell_text.delete("1.0", "end")
            return "break"
        if event.keysym in (
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Caps_Lock",
        ):
            return "break"
        edit_cell["position"] = position
        return None

    def merge_selection():
        top, left, bottom, right = selected_bounds()
        if top == bottom and left == right:
            messagebox.showinfo("표 병합", "병합할 셀 범위를 드래그하여 선택하세요.")
            return
        for (row, column), data in cell_data.items():
            if row < top or row > bottom or column < left or column > right:
                continue
            span_bottom = row + data.get("row_span", 1) - 1
            span_right = column + data.get("col_span", 1) - 1
            if (row < top or column < left or span_bottom > bottom or span_right > right):
                messagebox.showerror("표 병합", "기존 병합 셀 전체가 포함되도록 선택하세요.")
                return

        cell_data[(top, left)]["row_span"] = bottom - top + 1
        cell_data[(top, left)]["col_span"] = right - left + 1
        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if (row, column) != (top, left):
                    cell_data[(row, column)]["col_span"] = 1
                    cell_data[(row, column)]["row_span"] = 1
                    cell_data[(row, column)]["covered_by"] = (top, left)
        layout_grid()

    def unmerge_selection():
        top, left, _bottom, _right = selected_bounds()
        owner = cell_data.get((top, left), {}).get("covered_by", (top, left))
        data = cell_data.get(owner)
        if data and (data.get("row_span", 1) > 1 or data.get("col_span", 1) > 1):
            for row in range(owner[0], owner[0] + data.get("row_span", 1)):
                for column in range(owner[1], owner[1] + data.get("col_span", 1)):
                    if (row, column) != owner:
                        cell_data[(row, column)].pop("covered_by", None)
            data["row_span"] = 1
            data["col_span"] = 1
            layout_grid()

    def save_table():
        try:
            rows = int(row_var.get())
            columns = int(column_var.get())
        except ValueError:
            messagebox.showerror("오류", "행과 열에는 숫자를 입력해 주세요.")
            return

        if not (1 <= rows <= TABLE_ROW_LIMIT and 1 <= columns <= TABLE_COLUMN_LIMIT):
            messagebox.showerror("오류", "행과 열은 1~20 사이로 입력해 주세요.")
            return

        cells = {}
        for row in range(rows):
            for column in range(columns):
                widgets = cell_widgets[(row, column)]
                data = cell_data[(row, column)]
                if data.get("covered_by"):
                    continue
                col_span = min(data.get("col_span", 1), columns - column)
                row_span = min(data.get("row_span", 1), rows - row)
                content = get_styled_text(widgets["content"])
                cells[(row, column)] = {
                    "content": content,
                    "alignment": data.get("alignment", "center"),
                    "col_span": col_span,
                    "row_span": row_span,
                    "attributes": data.get("attributes", {}),
                }
        table_text = generate_namumark_table(rows, columns, cells)
        if replace_range:
            text.delete(replace_range[0], replace_range[1])
            text.insert(replace_range[0], table_text)
            start = replace_range[0]
            end = text.index(f"{start}+{len(table_text)}c")
            text.tag_add("namumark_table", start, end)
        else:
            try:
                text.delete("sel.first", "sel.last")
                text.insert(INSERT, table_text)
                end = text.index(INSERT)
                start = text.index(f"{INSERT}-{len(table_text)}c")
            except TclError:
                text.insert(INSERT, table_text)
                end = text.index(INSERT)
                start = text.index(f"{INSERT}-{len(table_text)}c")
            text.tag_add("namumark_table", start, end)
        dialog.destroy()

    action_frame = Frame(dialog)
    action_frame.pack(padx=10, pady=(0, 10))
    ttk.Button(action_frame, text="표 수정" if existing_model else "표 삽입",
               command=save_table).pack(side="left")
    ttk.Button(action_frame, text="취소", command=dialog.destroy).pack(
        side="left", padx=(5, 0))

    def create_cell(row, column):
        saved = initial_cells.get((row, column), {})
        data = cell_data.setdefault((row, column), {
            "alignment": saved.get("alignment", "center"),
            "col_span": saved.get("col_span", 1),
            "row_span": saved.get("row_span", 1),
            "attributes": saved.get("attributes", {}),
        })
        frame = Frame(grid_frame, relief="solid", borderwidth=1, bg="white")
        cell_text = Text(
            frame, width=18, height=2, wrap="word", undo=True,
            font=(using_font, 10), borderwidth=0, padx=5, pady=4,
        )
        cell_text.pack(fill="both", expand=True)
        for tag, style in (
            ("bold", (using_font, 10, "bold")),
            ("italic", (using_font, 10, "italic")),
            ("underline", (using_font, 10, "underline")),
            ("strikethrough", (using_font, 10, "overstrike")),
            ("footnote", (using_font, 5)),
        ):
            cell_text.tag_config(tag, font=style)
        cell_text.bind(
            "<KeyRelease>",
            lambda _event, widget=cell_text, pos=(row, column):
                apply_cell_alignment(
                    widget, cell_data[pos].get("alignment", "center")
                ),
        )
        if saved.get("content"):
            cell_text.insert("1.0", saved["content"])
        apply_cell_alignment(cell_text, data.get("alignment", "center"))

        cell_widgets[(row, column)] = {"frame": frame, "content": cell_text}
        frame.bind("<Button-1>", lambda event, p=(row, column): begin_selection(event, p))
        cell_text.bind("<Button-1>", lambda event, p=(row, column): begin_selection(event, p))
        frame.bind("<B1-Motion>", extend_selection)
        cell_text.bind("<B1-Motion>", extend_selection)
        cell_text.bind(
            "<KeyPress>",
            lambda event, p=(row, column), widget=cell_text:
                handle_cell_key(event, p, widget),
        )
        cell_text.bind("<FocusIn>", lambda _event, p=(row, column): active_cell.update(position=p))
        return data

    def layout_grid():
        try:
            rows = max(1, min(TABLE_ROW_LIMIT, int(row_var.get())))
            columns = max(1, min(TABLE_COLUMN_LIMIT, int(column_var.get())))
        except ValueError:
            return

        for widget in grid_frame.winfo_children():
            widget.grid_forget()
        for row in range(rows):
            grid_frame.grid_rowconfigure(row, weight=1, uniform="table_rows")
        for column in range(columns):
            grid_frame.grid_columnconfigure(column, weight=1, uniform="table_columns")

        for row in range(rows):
            for column in range(columns):
                if (row, column) not in cell_widgets:
                    create_cell(row, column)
                data = cell_data[(row, column)]
                if data.get("covered_by"):
                    continue
                row_span = min(data.get("row_span", 1), rows - row)
                col_span = min(data.get("col_span", 1), columns - column)
                cell_widgets[(row, column)]["frame"].grid(
                    row=row, column=column, rowspan=row_span,
                    columnspan=col_span, sticky="nsew", padx=1, pady=1,
                )
        grid_frame.update_idletasks()
        grid_canvas.configure(scrollregion=grid_canvas.bbox("all"))
        grid_canvas.itemconfigure(grid_window_id, width=max(
            grid_canvas.winfo_width(), grid_frame.winfo_reqwidth()
        ))
        update_selection(selection["extent"])

    def resize_grid(*_args):
        try:
            rows = max(1, min(TABLE_ROW_LIMIT, int(row_var.get())))
            columns = max(1, min(TABLE_COLUMN_LIMIT, int(column_var.get())))
        except ValueError:
            return
        for row in range(rows):
            for column in range(columns):
                if (row, column) not in cell_widgets:
                    create_cell(row, column)
        for coordinate, widgets in cell_widgets.items():
            row, column = coordinate
            if row < rows and column < columns:
                data = cell_data[coordinate]
                apply_cell_alignment(
                    widgets["content"], data.get("alignment", "center")
                )
        layout_grid()

    for row in range(initial_rows):
        for column in range(initial_cols):
            create_cell(row, column)
    row_var.trace_add("write", resize_grid)
    column_var.trace_add("write", resize_grid)
    resize_grid()
    dialog.update_idletasks()

def edit_table_at_cursor():
    try:
        index = text.index("insert")
        tags = text.tag_names(index)
        if "namumark_table" not in tags:
            messagebox.showerror("오류", "표 안의 위치에 커서를 놓은 후 표 수정 버튼을 누르세요.")
            return

        table_ranges = text.tag_ranges("namumark_table")
        for range_index in range(0, len(table_ranges), 2):
            start = table_ranges[range_index]
            end = table_ranges[range_index + 1]
            if text.compare(index, ">=", start) and text.compare(index, "<=", end):
                table_text = text.get(start, end)
                model = parse_namumark_table(table_text)
                open_table_dialog(model, (start, end))
                return
    except TclError:
        messagebox.showerror("오류", "표를 찾을 수 없습니다.")

def toggle_style(tag):
    try : 
        current_tags = text.tag_names("sel.first")
        if tag in current_tags : 
            text.tag_remove(tag, "sel.first", "sel.last")
        else :
            text.tag_add(tag, "sel.first", "sel.last")
    except TclError:
        messagebox.showerror("오류", "텍스트를 선택한 후 서식을 추가할 수 있습니다. 서식을 설정한 후 텍스트를 입력하는 기능은 추후 지원 예정입니다.")

def clear_selected_styles():
    try:
        # 선택된 영역의 모든 태그 제거
        text.tag_remove("bold", "sel.first", "sel.last")
        text.tag_remove("italic", "sel.first", "sel.last")
        text.tag_remove("underline", "sel.first", "sel.last")
        text.tag_remove("strikethrough", "sel.first", "sel.last")
        text.tag_remove("paragraph1", "sel.first", "sel.last")
        text.tag_remove("paragraph2", "sel.first", "sel.last")
        text.tag_remove("paragraph3", "sel.first", "sel.last")
        text.tag_remove("paragraph4", "sel.first", "sel.last")
        text.tag_remove("paragraph5", "sel.first", "sel.last")
        text.tag_remove("footnote", "sel.first", "sel.last")
    except TclError:
        messagebox.showerror("오류", "텍스트를 선택한 후 서식을 제거할 수 있습니다.")

def convert():
    full_text = text.get("1.0", "end-1c")
    formatted_text = ""
    current_line = 1

    while True:
        line_start = f"{current_line}.0"
        
        try:
            line_end = text.index(f"{line_start} lineend")
            line_text = text.get(line_start, line_end)
            
            # 현재 라인의 변환된 텍스트를 저장할 리스트
            transformed_segments = []
            char_idx = 0
            
            while char_idx < len(line_text):
                # 현재 문자의 위치
                current_pos = f"{line_start}+{char_idx}c"
                current_tags = set(text.tag_names(current_pos))
                
                # 현재 위치에서 시작하는 연속된 텍스트 세그먼트를 찾음
                segment = ""
                segment_start = char_idx
                
                while char_idx < len(line_text):
                    next_pos = f"{line_start}+{char_idx}c"
                    next_tags = set(text.tag_names(next_pos))
                    
                    # 태그가 변경되면 세그먼트 종료
                    if next_tags != current_tags:
                        break
                        
                    segment += line_text[char_idx]
                    char_idx += 1
                
                # 세그먼트에 스타일 적용
                transformed_segment = segment
                
                # 전체 세그먼트에 대해 스타일 한 번만 적용
                if "bold" in current_tags:
                    transformed_segment = f"'''{transformed_segment}'''"
                if "italic" in current_tags:
                    transformed_segment = f"''{transformed_segment}''"
                if "underline" in current_tags:
                    transformed_segment = f"__{transformed_segment}__"
                if "strikethrough" in current_tags:
                    transformed_segment = f"--{transformed_segment}--"
                if "footnote" in current_tags:
                    transformed_segment = f"[* {transformed_segment}]"
                if "paragraph1" in current_tags:
                    transformed_segment = f"= {transformed_segment} ="
                if "paragraph2" in current_tags:
                    transformed_segment = f"== {transformed_segment} =="
                if "paragraph3" in current_tags:
                    transformed_segment = f"=== {transformed_segment} ==="
                if "paragraph4" in current_tags:
                    transformed_segment = f"==== {transformed_segment} ===="
                if "paragraph5" in current_tags:
                    transformed_segment = f"===== {transformed_segment} ====="
                
                transformed_segments.append(transformed_segment)
            
            # 변환된 세그먼트들을 합쳐서 한 줄로 만듦
            formatted_text += "".join(transformed_segments) + "\n"
            
            # 다음 라인으로 이동
            current_line += 1
            
            # 마지막 라인인지 확인
            next_line_start = f"{current_line}.0"
            if text.compare(next_line_start, ">=", "end"):
                break
                
        except TclError:
            break
    
    index_add = messagebox.askyesno(title="목차", message="목차를 삽입할까요?")
    if index_add == True : 
        formatted_text = "[목차]\n" + formatted_text

    category = simpledialog.askstring("분류", "추가할 분류를 입력하세요. 추가할 분류가 여러 개인 경우, 띄어쓰기 없이 쉼표로 구분하여 입력해 주세요. 추가할 분류가 없다면 아무것도 입력하지 않습니다.")
    if category != "" : 
        category_list = category.split(",")
        category_text = "\n"
        for i in category_list : 
            category_text = f"[[분류:{i}]]" + category_text
        
        formatted_text = category_text + formatted_text

    # 파일로 저장
    now = datetime.now()
    default_filename = now.strftime("%Y%m%d%H%M%S")
    filename_base = simpledialog.askstring(
        "파일 이름",
        "저장할 파일 이름을 입력하세요.",
        initialvalue=default_filename,
    )
    if filename_base is None:
        messagebox.showerror("오류", "비정상적인 입력입니다.")
        return
    filename_base = filename_base.strip()
    if not filename_base:
        messagebox.showerror("오류", "파일 이름을 입력해 주세요.")
        return
    if filename_base.lower().endswith(".txt"):
        filename_base = filename_base[:-4]
    filename = f"{filename_base}.txt"
    
    try:
        suffix = 0
        while True:
            try:
                with open(filename, "x", encoding="utf-8") as file:
                    file.write(formatted_text)
                break
            except FileExistsError:
                suffix += 1
                filename = f"{filename_base} ({suffix}).txt"
        messagebox.showinfo("알림", f"파일이 저장되었습니다\n\n파일 이름: {filename}")
    except Exception as e:
        messagebox.showerror("오류", f"파일 저장 중 오류가 발생했습니다. 오류 내용: \n\n{e}")

# GUI 설정
window = Tk()
window.title("나무마크 시각 편집기")
window.geometry("1200x700")

button_frame = Frame(window)
button_frame.pack()

bold_button = Button(button_frame, text="볼드", command=lambda: toggle_style("bold"))
bold_button.grid(row=0, column=0, padx=5, pady=5)

italic_button = Button(button_frame, text="이탤릭", command=lambda: toggle_style("italic"))
italic_button.grid(row=0, column=1, padx=5, pady=5)

underline_button = Button(button_frame, text="밑줄", command=lambda: toggle_style("underline"))
underline_button.grid(row=0, column=2, padx=5, pady=5)

strikethrough_button = Button(button_frame, text="취소선", command=lambda: toggle_style("strikethrough"))
strikethrough_button.grid(row=0, column=3, padx=5, pady=5)

footnote_button = Button(button_frame, text="각주", command=lambda: toggle_style("footnote"))
footnote_button.grid(row=0, column=4, padx=5, pady=5)

paragraph1_button = Button(button_frame, text="1단계 문단 제목", command=lambda: toggle_style("paragraph1"))
paragraph1_button.grid(row=0, column=5, padx=5, pady=5)

paragraph2_button = Button(button_frame, text="2단계 문단 제목", command=lambda: toggle_style("paragraph2"))
paragraph2_button.grid(row=0, column=6, padx=5, pady=5)

paragraph3_button = Button(button_frame, text="3단계 문단 제목", command=lambda: toggle_style("paragraph3"))
paragraph3_button.grid(row=0, column=7, padx=5, pady=5)

paragraph4_button = Button(button_frame, text="4단계 문단 제목", command=lambda: toggle_style("paragraph4"))
paragraph4_button.grid(row=0, column=8, padx=5, pady=5)

paragraph5_button = Button(button_frame, text="5단계 문단 제목", command=lambda: toggle_style("paragraph5"))
paragraph5_button.grid(row=0, column=9, padx=5, pady=5)

clear_styles_button = Button(button_frame, text="서식 제거", command=clear_selected_styles)
clear_styles_button.grid(row=0, column=10, padx=5, pady=5)

convert_button = Button(button_frame, text="나무마크로 변환하기", command=convert)
convert_button.grid(row=0, column=11, padx=5, pady=5)

table_button = Button(button_frame, text="표 삽입", command=open_table_dialog)
table_button.grid(row=0, column=12, padx=5, pady=5)

edit_table_button = Button(button_frame, text="표 수정", command=edit_table_at_cursor)
edit_table_button.grid(row=0, column=13, padx=5, pady=5)

text = Text(window, font=(using_font, textsize), wrap="word", undo=True)
text.pack(expand=True, fill="both")
text.tag_config("namumark_table", background="#ddd")

text.tag_config("bold", font=(using_font, textsize, "bold"))
text.tag_config("italic", font=(using_font, textsize, "italic"))
text.tag_config("underline", font=(using_font, textsize, "underline"))
text.tag_config("strikethrough", font=(using_font, textsize, "overstrike"))
text.tag_config("footnote", font=(using_font, int(textsize * 0.5)), background="lightgray")
text.tag_config("paragraph1", font=(using_font, int(textsize * 2.5), "bold"))
text.tag_config("paragraph2", font=(using_font, textsize * 2, "bold"))
text.tag_config("paragraph3", font=(using_font, int(textsize * 1.8), "bold"))
text.tag_config("paragraph4", font=(using_font, int(textsize * 1.6), "bold"))
text.tag_config("paragraph5", font=(using_font, int(textsize * 1.4), "bold"))

window.mainloop()
