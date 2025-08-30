import sqlite3
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name: str = "bot_database.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Инициализация таблиц в базе данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица для отслеживаемых игроков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracked_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    player_nickname TEXT NOT NULL,
                    UNIQUE(user_id, player_nickname)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS player_statuses (
                    player_nickname TEXT PRIMARY KEY,
                    last_status TEXT,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def add_tracked_player(self, user_id: int, player_nickname: str) -> bool:
        """Добавление игрока в список отслеживания"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO tracked_players (user_id, player_nickname) VALUES (?, ?)',
                    (user_id, player_nickname)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления игрока: {e}")
            return False

    def get_tracked_players(self) -> List[Tuple[int, str]]:
        """Получение всех отслеживаемых игроков"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT user_id, player_nickname FROM tracked_players')
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения игроков: {e}")
            return []

    def get_users_tracking_player(self, player_nickname: str) -> List[int]:
        """Получение всех пользователей, отслеживающих конкретного игрока"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT user_id FROM tracked_players WHERE player_nickname = ?',
                    (player_nickname,)
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []

    def update_player_status(self, player_nickname: str, status: str) -> bool:
        """Обновление статуса игрока"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO player_statuses (player_nickname, last_status, last_checked)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (player_nickname, status))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            return False

    def get_player_status(self, player_nickname: str) -> Optional[str]:
        """Получение последнего известного статуса игрока"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT last_status FROM player_statuses WHERE player_nickname = ?',
                    (player_nickname,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return None

    def remove_tracking(self, user_id: int, player_nickname: str) -> bool:
        """Удаление игрока из списка отслеживания"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM tracked_players WHERE user_id = ? AND player_nickname = ?',
                    (user_id, player_nickname)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка удаления отслеживания: {e}")
            return False