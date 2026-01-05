from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_pagination_keyboard(page: int = 0, total_pages: int = 0):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"prev_{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"next_{page+1}"))

    # Arrange buttons in rows based on row_width
    keyboard_rows = []
    current_row = []
    row_width = 2  # Assuming row_width of 2 for pagination buttons
    for button in buttons:
        current_row.append(button)
        if len(current_row) == row_width:
            keyboard_rows.append(current_row)
            current_row = []
    if current_row:  # Add any remaining buttons
        keyboard_rows.append(current_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
