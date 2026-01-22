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

def get_seasons_keyboard(seasons, tv_id):
    buttons = []
    for season in seasons:
        season_number = season.get('season_number')
        season_name = season.get('name', f'Season {season_number}')
        episode_count = season.get('episode_count', 0)
        # Include episode_count in callback data
        callback_data = f"season_{tv_id}_{season_number}_{episode_count}"
        buttons.append(InlineKeyboardButton(text=season_name, callback_data=callback_data))

    keyboard_rows = []
    current_row = []
    row_width = 2
    for button in buttons:
        current_row.append(button)
        if len(current_row) == row_width:
            keyboard_rows.append(current_row)
            current_row = []
    if current_row:
        keyboard_rows.append(current_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_episodes_keyboard(tv_id, season_number, episode_count):
    buttons = []
    for episode_num in range(1, episode_count + 1):
        url = f"https://www.vidking.net/embed/tv/{tv_id}/{season_number}/{episode_num}"
        buttons.append(InlineKeyboardButton(text=str(episode_num), url=url))

    keyboard_rows = []
    current_row = []
    row_width = 5  # More buttons per row for episodes (since they are just numbers)
    for button in buttons:
        current_row.append(button)
        if len(current_row) == row_width:
            keyboard_rows.append(current_row)
            current_row = []
    if current_row:
        keyboard_rows.append(current_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
