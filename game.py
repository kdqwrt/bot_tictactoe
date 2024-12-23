import random

class TicTacToeGame:
    def __init__(self, player_symbol, mode="player", field_size=3):
        self.field_size = field_size
        self.board_size = field_size * field_size
        self.board = [""] * self.board_size
        self.player_symbol = player_symbol
        self.bot_symbol = "O" if player_symbol == "X" else "X"
        self.current_player = "X"
        self.mode = mode
        self.winner = None

        if field_size == 3:
            self.winning_length = 3
        elif field_size == 4:
            self.winning_length = 3
        else:
            self.winning_length = field_size

    def get_board(self):
        return self.board

    def make_move(self, position):
        if self.board[position] == "" and self.winner is None:
            self.board[position] = self.current_player
            if self.check_winner():
                self.winner = self.current_player
            elif self.is_draw():
                self.winner = "Draw"
            else:
                self.switch_player()
            return True
        return False

    def reset_board(self):
        self.board = [""] * self.board_size
        self.winner = None
        self.current_player = "X"
        if self.mode == "bot" and self.bot_symbol == "X":
            self.bot_move()

    def switch_player(self):
        self.current_player = "O" if self.current_player == "X" else "X"

    def bot_move(self):
        if self.mode == "bot" and self.current_player == self.bot_symbol:
            empty_positions = [
                i for i, cell in enumerate(self.board) if cell == ""
            ]

            winning_moves = []
            for move in empty_positions:
                board_copy = self.board.copy()
                board_copy[move] = self.bot_symbol
                if self.is_winner(board_copy, self.bot_symbol):
                    winning_moves.append(move)

            blocking_moves = []
            for move in empty_positions:
                board_copy = self.board.copy()
                board_copy[move] = self.player_symbol
                if self.is_winner(board_copy, self.player_symbol):
                    blocking_moves.append(move)

            possible_moves = []
            if winning_moves and blocking_moves:
                choice = random.choice(["win", "block"])
                if choice == "win":
                    possible_moves = winning_moves
                else:
                    possible_moves = blocking_moves
            elif winning_moves:
                possible_moves = winning_moves
            elif blocking_moves:
                possible_moves = blocking_moves
            else:
                possible_moves = empty_positions

            if possible_moves:
                move = random.choice(possible_moves)
                self.make_move(move)

    def check_winner(self):
        return self.is_winner(self.board, self.current_player)

    def is_winner(self, board, symbol):
        lines = []


        for row in range(self.field_size):
            for col in range(self.field_size - self.winning_length + 1):
                lines.append([row * self.field_size + col + i for i in range(self.winning_length)])


        for col in range(self.field_size):
            for row in range(self.field_size - self.winning_length + 1):
                lines.append([(row + i) * self.field_size + col for i in range(self.winning_length)])


        for row in range(self.field_size - self.winning_length + 1):
            for col in range(self.field_size - self.winning_length + 1):
                lines.append([(row + i) * self.field_size + col + i for i in range(self.winning_length)])


        for row in range(self.field_size - self.winning_length + 1):
            for col in range(self.winning_length - 1, self.field_size):
                lines.append([(row + i) * self.field_size + col - i for i in range(self.winning_length)])

        for line in lines:
            if all(board[pos] == symbol for pos in line):
                return True
        return False

    def is_draw(self):
        return all(cell != "" for cell in self.board) and self.winner is None
