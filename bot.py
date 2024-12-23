import logging
import json
import os
import asyncio
from config import API_TOKEN
from telebot.async_telebot import AsyncTeleBot
from display import format_board_as_emoji, create_game_keyboard
from game import TicTacToeGame
from telebot import types
from keyboards import (
    choice_keyboard,
    play_keyboard,
    game_mode_keyboard,
    field_size_keyboard,
    exit_queue_keyboard,
    exit_game_keyboard,
)
from player_queue import PlayerQueue


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

class TicTacToeBot:
    def __init__(self, api_token):
        self.bot = AsyncTeleBot(api_token)
        self.games = {}
        self.player_queue = PlayerQueue()

        self._register_handlers()
        self.leaderboard = self.load_leaderboard()

    def _register_handlers(self):
        @self.bot.message_handler(func=lambda message: message.text == "Выход")
        async def handle_exit(message):
            await self.handle_exit_game(message)

        @self.bot.message_handler(func=lambda message: message.text == "Выйти из очереди")
        async def handle_exit_queue(message):
            await self.handle_exit_from_queue(message)

        @self.bot.message_handler(func=lambda message: message.text in ["Да", "Нет"])
        async def handle_yes_no(message):
            await self.handle_yes_no(message)

        @self.bot.message_handler(
            func=lambda message: message.text in ["Против бота", "Против игрока"]
        )
        async def handle_game_mode_choice(message):
            await self.handle_game_mode_choice(message)

        @self.bot.message_handler(
            func=lambda message: message.text in ["Крестик", "Нолик"]
        )
        async def handle_symbol_choice(message):
            await self.handle_symbol_choice(message)

        @self.bot.message_handler(
            func=lambda message: message.text in ["Поле 3x3", "Поле 4x4"]
        )
        async def handle_field_size_choice(message):
            await self.handle_field_size_choice(message)

        @self.bot.callback_query_handler(func=lambda call: True)
        async def handle_callback(call):
            if call.data.startswith("move_"):
                await self.handle_move(call)
            elif call.data == "surrender":
                await self.handle_surrender(call)
            else:
                await self.bot.answer_callback_query(call.id, "Неизвестная команда.")

        @self.bot.message_handler(func=lambda message: True)
        async def handle_any_text(message):
            await self.handle_any_text(message)

        @self.bot.message_handler(commands=['/instruction'])
        async def handle_instruction(message):
            await self.send_instruction(message.chat.id)

        @self.bot.message_handler(commands=['/leaderboard'])
        async def handle_leaderboard(message):
            await self.send_leaderboard(message.chat.id)

    async def set_bot_commands(self):
        commands = [
            types.BotCommand("start", "Начать игру"),
            types.BotCommand("exit", "Выйти из игры"),
            types.BotCommand("leaderboard", "Показать лидерборд"),
            types.BotCommand("instruction", "Показать инструкцию"),
        ]
        await self.bot.set_my_commands(commands)

    async def send_main_menu(self, chat_id):
        menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        menu_keyboard.add("Инструкция", "Лидерборд")
        await self.bot.send_message(
            chat_id,
            "Добро пожаловать! Выберите действие из меню:",
            reply_markup=menu_keyboard,
        )

    async def send_instruction(self, chat_id):
        instruction_text = (
            "Добро пожаловать в Крестики-Нолики! 🎮\n\n"
            "Вот как играть:\n"
            "1. Выберите режим: против бота или другого игрока.\n"
            "2. Выберите размер поля (3x3 или 4x4).\n"
            "3. Дождитесь начала игры и делайте ходы, нажимая на кнопки на игровом поле.\n\n"
            "Цель: собрать три  символа подряд по горизонтали, вертикали или диагонали. Удачи!"
        )
        await self.bot.send_message(chat_id, instruction_text)

    def load_leaderboard(self):

        if os.path.exists("leaderboard.json"):
            with open("leaderboard.json", "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    def save_leaderboard(self):

        with open("leaderboard.json", "w", encoding="utf-8") as file:
            json.dump(self.leaderboard, file, ensure_ascii=False, indent=4)

    async def update_leaderboard(self, user_id):
        try:

            user = await self.bot.get_chat(user_id)
        except Exception as e:
            logging.error(f"Ошибка получения объекта пользователя для ID {user_id}: {e}")
            return


        if user.username:
            identifier = user.username.lstrip('@')
        elif user.first_name:
            identifier = user.first_name
        else:
            identifier = f"User_{user_id}"


        if identifier not in self.leaderboard:
            self.leaderboard[identifier] = 0
        self.leaderboard[identifier] += 1


        self.save_leaderboard()


        logging.info(f"Лидерборд обновлен для пользователя: {identifier}")

    async def send_leaderboard(self, chat_id):
        if not self.leaderboard:
            await self.bot.send_message(chat_id, "🏆 Лидерборд пока пуст. Сыграйте, чтобы попасть в таблицу!")
            return

        sorted_leaderboard = sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = "🏆 Лидерборд:\n"
        for idx, (identifier, wins) in enumerate(sorted_leaderboard, start=1):

            if "@" not in identifier:
                identifier = f"@{identifier}"

            leaderboard_text += f"{idx}. {identifier} - Побед: {wins}\n"

        await self.bot.send_message(chat_id, leaderboard_text)

    def is_game_active(self, chat_id):
        return chat_id in self.games

    async def send_game_invite(self, chat_id):
        await self.bot.send_message(
            chat_id, "Привет! Хочешь сыграть в игру?", reply_markup=choice_keyboard
        )

    async def handle_exit_game(self, message):
        chat_id = message.chat.id
        if not self.is_game_active(chat_id):
            await self.send_game_invite(chat_id)
            return

        game_data = self.games.pop(chat_id, None)
        if game_data and game_data.get("opponent"):
            opponent_id = game_data["opponent"]
            await self.bot.send_message(opponent_id, "Противник вышел из игры. Игра завершена.")
            self.games.pop(opponent_id, None)

        await self.bot.send_message(chat_id, "Вы вышли из игры. Увидимся в следующий раз!")

    async def handle_exit_from_queue(self, message):
        chat_id = message.chat.id

        field_size = self.games.get(chat_id, {}).get("field_size")
        if not field_size:
            await self.bot.send_message(chat_id, "Ошибка: вы не в очереди.")
            return


        if self.player_queue.remove_player(chat_id, field_size):
            await self.bot.send_message(chat_id, "Вы вышли из очереди. Увидимся в следующий раз!")
        else:
            await self.bot.send_message(chat_id, "Ошибка: не удалось выйти из очереди.")

    async def handle_yes_no(self, message):
        if message.text == "Да":
            await self.bot.send_message(
                message.chat.id, "Выберите режим игры:", reply_markup=game_mode_keyboard
            )
        else:
            await self.bot.send_message(message.chat.id, "Увидимся в следующий раз!")

    async def handle_game_mode_choice(self, message):
        chat_id = message.chat.id
        if self.is_game_active(chat_id):
            await self.bot.send_message(chat_id, "Игра уже идёт. Завершите текущую игру.")
            return

        game_mode = "bot" if message.text == "Против бота" else "player"
        self.games[chat_id] = {"mode": game_mode}
        await self.bot.send_message(chat_id, "Выберите размер поля:", reply_markup=field_size_keyboard)

    async def handle_field_size_choice(self, message):
        chat_id = message.chat.id
        if not self.is_game_active(chat_id):
            await self.send_game_invite(chat_id)
            return

        field_size = 3 if message.text == "Поле 3x3" else 4
        self.games[chat_id]["field_size"] = field_size
        game_mode = self.games[chat_id]["mode"]

        if game_mode == "bot":
            await self.send_symbol_choice(chat_id)
        elif game_mode == "player":
            self.player_queue.add_player(chat_id, field_size)
            opponent_id = self.player_queue.get_opponent(chat_id, field_size)
            if opponent_id:
                await self.start_game(chat_id, opponent_id, field_size)
            else:
                await self.bot.send_message(
                    chat_id, "Вы в очереди. Ожидайте другого игрока.", reply_markup=exit_queue_keyboard
                )

    async def send_symbol_choice(self, chat_id):
        await self.bot.send_message(
            chat_id, "Выберите: Крестик или Нолик", reply_markup=play_keyboard
        )

    async def handle_symbol_choice(self, message):
        chat_id = message.chat.id
        if not self.is_game_active(chat_id):
            await self.send_game_invite(chat_id)
            return

        player_symbol = "X" if message.text == "Крестик" else "O"
        game_mode = self.games[message.chat.id]["mode"]
        field_size = self.games[message.chat.id].get("field_size", 3)

        if game_mode == "bot":
            game = TicTacToeGame(
                player_symbol, mode=game_mode, field_size=field_size
            )
            self.games[message.chat.id]["game"] = game
            self.games[message.chat.id]["symbol"] = player_symbol
            self.games[message.chat.id]["message_id"] = None
            logging.debug(f"Игра против бота инициализирована для {message.chat.id}")

            await self.bot.send_message(
                message.chat.id,
                f"Ты выбрал {player_symbol}. Начинаем игру!",
                reply_markup=exit_game_keyboard
            )

            if player_symbol == "O":
                game.bot_move()
            await self.display_board(message.chat.id)
        else:
            await self.bot.send_message(message.chat.id, "Ожидаем второго игрока...", reply_markup=exit_game_keyboard)

    async def start_game(self, player_1_id, player_2_id, field_size):
        game = TicTacToeGame("X", mode="player", field_size=field_size)
        self.games[player_1_id] = {
            "game": game,
            "opponent": player_2_id,
            "symbol": "X",
            "message_id": None,
        }
        self.games[player_2_id] = {
            "game": game,
            "opponent": player_1_id,
            "symbol": "O",
            "message_id": None,
        }

        await self.bot.send_message(
            player_1_id, "Игра начинается! Вы играете за Крестики.", reply_markup=exit_game_keyboard
        )
        await self.bot.send_message(
            player_2_id, "Игра начинается! Вы играете за Нолики.", reply_markup=exit_game_keyboard
        )

        await self.display_board(player_1_id)
        await self.display_board(player_2_id)

    async def display_board(self, chat_id):
        if chat_id not in self.games:
            await self.bot.send_message(
                chat_id, "Игра не найдена. Начните новую игру."
            )
            logging.error(
                f"Попытка отобразить доску для отсутствующей игры: chat_id={chat_id}"
            )
            return

        game_data = self.games[chat_id]
        game = game_data["game"]
        field_size = game.field_size
        board_display = format_board_as_emoji(game.get_board(), field_size)
        keyboard = create_game_keyboard(
            game.get_board(), field_size, game_over=False
        )

        logging.debug(f"Отображение доски для {chat_id}")

        if game_data.get("message_id") is None:
            sent_message = await self.bot.send_message(
                chat_id, board_display, reply_markup=keyboard
            )
            self.games[chat_id]["message_id"] = sent_message.message_id
        else:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=game_data["message_id"],
                text=board_display,
                reply_markup=keyboard,
            )

    async def handle_move(self, call):
        chat_id = call.message.chat.id
        data = call.data
        if not data.startswith("move_"):
            return
        position = int(data.split("_")[1])

        if chat_id not in self.games:
            await self.bot.send_message(
                chat_id, "Игра не найдена. Начните новую игру."
            )
            logging.error(
                f"Попытка сделать ход без активной игры: chat_id={chat_id}"
            )
            return

        game_data = self.games[chat_id]
        game = game_data["game"]
        player_symbol = game_data["symbol"]

        if game.current_player != player_symbol:
            await self.bot.answer_callback_query(call.id, "Сейчас не ваш ход.")
            return

        if game.make_move(position):
            opponent_id = game_data.get("opponent")
            await self.display_board(chat_id)
            if opponent_id:
                await self.display_board(opponent_id)

            if game.winner:
                if game.winner == "Draw":
                    await self.bot.send_message(chat_id, "Поле заполнено. Игровое поле очищено и игра продолжается.")
                    if opponent_id:
                        await self.bot.send_message(opponent_id, "Поле заполнено. Игровое поле очищено и игра продолжается.")
                    game.reset_board()
                    await self.display_board(chat_id)
                    if opponent_id:
                        await self.display_board(opponent_id)


                    if game.mode == "bot" and game.bot_symbol == "X":
                        game.bot_move()
                        await self.display_board(chat_id)
                        if opponent_id:
                            await self.display_board(opponent_id)
                else:
                    result_message = f"Победитель: {game.winner}"
                    await self.bot.send_message(chat_id, result_message)
                    if opponent_id:
                        await self.bot.send_message(opponent_id, result_message)

                    if game.winner != "Draw":
                        winner_id = chat_id if game.winner == player_symbol else opponent_id
                        await self.update_leaderboard(winner_id)
                        leaderboard_text = f"🏆 Победитель: {game.winner}!\n\nОбновленный лидерборд:\n"
                        leaderboard_text += await self.format_leaderboard()
                        await self.bot.send_message(chat_id, leaderboard_text)
                        if opponent_id:
                            await self.bot.send_message(opponent_id, leaderboard_text)

                    del self.games[chat_id]
                    if opponent_id in self.games:
                        del self.games[opponent_id]
            else:
                if game.mode == "bot" and game.current_player == game.bot_symbol:
                    game.bot_move()
                    await self.display_board(chat_id)
                    if game.winner:
                        if game.winner == "Draw":
                            await self.bot.send_message(chat_id, "Поле заполнено. Игровое поле очищено и игра продолжается.")
                            game.reset_board()
                            await self.display_board(chat_id)
                        else:
                            result_message = f"Победитель: {game.winner}"
                            await self.bot.send_message(chat_id, result_message)
                            del self.games[chat_id]
        else:
            await self.bot.answer_callback_query(
                call.id, "Это место уже занято. Выберите другое."
            )

    async def handle_surrender(self, call):
        chat_id = call.message.chat.id

        if chat_id not in self.games:
            await self.bot.send_message(chat_id, "Игра не найдена. Начните новую игру.")
            logging.error(
                f"Попытка сдаться без активной игры: chat_id={chat_id}"
            )
            return

        game_data = self.games[chat_id]
        opponent_id = game_data.get("opponent")

        await self.bot.send_message(chat_id, "Вы сдались. Игра окончена. Увидимся в следующий раз!")
        if opponent_id:
            await self.bot.send_message(opponent_id, "Противник сдался. Вы победили! Увидимся в следующий раз.")
            del self.games[opponent_id]
        del self.games[chat_id]

    async def handle_callback(self, call):
        chat_id = call.message.chat.id
        if not self.is_game_active(chat_id):
            await self.bot.answer_callback_query(call.id, "Игра не начата. Начните новую игру.")
            await self.send_game_invite(chat_id)
            return

        if call.data.startswith("move_"):
            await self.handle_move(call)
        elif call.data == "surrender":
            await self.handle_surrender(call)
        else:
            await self.bot.answer_callback_query(call.id, "Неизвестная команда.")

    async def handle_any_text(self, message):
        chat_id = message.chat.id
        user_input = message.text

        if user_input == '/instruction':
            await self.send_instruction(chat_id)
            return

        if user_input == '/leaderboard':
            await self.send_leaderboard(chat_id)
            return

        if chat_id not in self.games:

            await self.send_game_invite(chat_id)
            return

        game_data = self.games[chat_id]
        game = game_data.get("game")
        current_state = {
            "mode": game_data.get("mode"),
            "field_size": game_data.get("field_size"),
            "symbol": game_data.get("symbol"),
            "is_player_turn": game.current_player == game_data["symbol"],
        }

        if user_input == "Выход" and current_state["mode"]:
            await self.handle_exit_game(message)
        elif user_input == "Выйти из очереди" and not current_state["mode"]:
            await self.handle_exit_from_queue(message)
        elif user_input in ["Крестик", "Нолик"] and not current_state["symbol"]:
            await self.handle_symbol_choice(message)
        elif user_input in ["Поле 3x3", "Поле 4x4"] and not current_state["field_size"]:
            await self.handle_field_size_choice(message)
        else:

            await self.bot.send_message(
                chat_id,
                "Мы уже начали игру! Следуйте инструкциям для текущего этапа игры.",
            )

    async def start_polling(self):
        await self.bot.infinity_polling()
        await self.set_bot_commands()

if __name__ == "__main__":
    bot = TicTacToeBot(API_TOKEN)
    asyncio.run(bot.start_polling())
