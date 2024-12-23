import random

class TicTacToeAI:
    @staticmethod
    def get_best_move(game):
        board = game.get_board()
        empty_positions = [i for i, cell in enumerate(board) if cell == '']


        for move in empty_positions:
            board[move] = game.bot_symbol
            if game.check_winner():
                board[move] = ''
                return move
            board[move] = ''


        for move in empty_positions:
            board[move] = game.player_symbol
            if game.check_winner():
                board[move] = ''
                return move
            board[move] = ''


        center = (game.field_size * game.field_size) // 2
        if game.field_size % 2 == 1 and board[center] == '':
            return center


        return random.choice(empty_positions) if empty_positions else None
