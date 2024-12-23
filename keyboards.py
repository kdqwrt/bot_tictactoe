from telebot import types

# Клавиатура выбора игры
choice_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
choice_keyboard.add("Да", "Нет", "Выход")

# Клавиатура выбора режима игры
game_mode_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
game_mode_keyboard.add("Против бота", "Против игрока", "Выход")

# Клавиатура выбора размера поля
field_size_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
field_size_keyboard.row("Поле 3x3", "Поле 4x4", "Выход")

# Клавиатура выбора символа
play_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
play_keyboard.add("Крестик", "Нолик", "Выход")

# Клавиатура выхода из очереди
exit_queue_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
exit_queue_keyboard.add("Выйти из очереди", "Выход")

# Клавиатура выхода из игры
exit_game_keyboard = types.ReplyKeyboardMarkup(
    resize_keyboard=True, one_time_keyboard=True
)
exit_game_keyboard.add("Выход")
