from telebot import types

def format_board_as_emoji(board, field_size):
    symbols = {"X": "❌", "O": "⭕", "": "⬜"}
    display = ""
    for i, cell in enumerate(board):
        display += symbols[cell]
        if (i + 1) % field_size == 0:
            display += "\n"
    return display

def create_game_keyboard(board, field_size, game_over=False):
    keyboard = types.InlineKeyboardMarkup(row_width=field_size)
    buttons = []

    for i, cell in enumerate(board):
        emoji = "❌" if cell == "X" else "⭕" if cell == "O" else "⬜"
        callback_data = f"move_{i}" if not game_over and cell == "" else "disabled"
        buttons.append(
            types.InlineKeyboardButton(emoji, callback_data=callback_data)
        )

    keyboard.add(*buttons)

    if not game_over:

        keyboard.add(
            types.InlineKeyboardButton("Сдаться", callback_data="surrender")
        )

    return keyboard
