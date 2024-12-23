from collections import deque


class PlayerQueue:
    def __init__(self):
        self.queues = {}  # Ключ: размер поля, значение: очередь игроков

    def add_player(self, player_id, field_size):
        # Добавляет игрока в очередь для указанного размера поля
        if field_size not in self.queues:
            self.queues[field_size] = deque()
        if player_id not in self.queues[field_size]:
            self.queues[field_size].append(player_id)

    def get_opponent(self, player_id, field_size):
        # Возвращает ID противника и удаляет обоих из очереди
        if field_size in self.queues and len(self.queues[field_size]) >= 2:
            self.queues[field_size].remove(player_id)
            opponent_id = self.queues[field_size].popleft()
            return opponent_id
        return None

    def remove_player(self, player_id, field_size):
        # Удаляет игрока из очереди
        if field_size in self.queues and player_id in self.queues[field_size]:
            self.queues[field_size].remove(player_id)

    def __len__(self):
        return sum(len(queue) for queue in self.queues.values())
