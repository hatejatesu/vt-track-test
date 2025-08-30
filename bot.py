import telebot
import schedule
import time
import threading
from datetime import datetime
import logging

from config import BOT_TOKEN
from database import Database
from parser import get_player_status

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Бот для отслеживания статуса игроков на Vimeworld\n\n"
        "📋 Доступные команды:\n"
        "/spectate <ник> - начать отслеживание игрока\n"
        "/list - показать отслеживаемых игроков\n"
        "/stop <ник> - отслеживание игрока\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['spectate'])
def spectate_player(message):
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Укажите ник игрока: /spectate <ник>")
            return

        player_nickname = message.text.split()[1].strip()
        user_id = message.from_user.id

        # Проверяем существование игрока
        current_status = get_player_status(player_nickname)
        if current_status is None:
            bot.reply_to(message, "❌ Игрок не найден или произошла ошибка при проверке")
            return

        # Добавляем в базу данных
        if db.add_tracked_player(user_id, player_nickname):
            db.update_player_status(player_nickname, current_status)
            bot.reply_to(
                message,
                f"✅ Теперь отслеживаю игрока {player_nickname}\n"
                f"📊 Текущий статус: {current_status}"
            )
        else:
            bot.reply_to(message, "⚠️ Вы уже отслеживаете этого игрока")

    except Exception as e:
        logger.error(f"Ошибка в spectate: {e}")
        bot.reply_to(message, "❌ Произошла ошибка, попробуйте позже")

@bot.message_handler(commands=['list'])
def list_players(message):
    try:
        user_id = message.from_user.id
        tracked_players = [
            player for user, player in db.get_tracked_players() 
            if user == user_id
        ]
        
        if not tracked_players:
            bot.reply_to(message, "📝 Вы не отслеживаете ни одного игрока")
            return
        
        players_list = "\n".join([
            f"• {player} - {db.get_player_status(player) or 'неизвестно'}"
            for player in tracked_players
        ])
        
        bot.reply_to(message, f"📋 Ваши отслеживаемые игроки:\n{players_list}")
    
    except Exception as e:
        logger.error(f"Ошибка в list: {e}")
        bot.reply_to(message, "❌ Произошла ошибка, попробуйте позже")

@bot.message_handler(commands=['stop'])
def stop_tracking(message):
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ Укажите ник игрока: /stop <ник>")
            return

        player_nickname = message.text.split()[1].strip()
        user_id = message.from_user.id

        if db.remove_tracking(user_id, player_nickname):
            bot.reply_to(message, f"❌ Прекратил отслеживание игрока {player_nickname}")
        else:
            bot.reply_to(message, "⚠️ Вы не отслеживаете этого игрока")

    except Exception as e:
        logger.error(f"Ошибка в stop: {e}")
        bot.reply_to(message, "❌ Произошла ошибка, попробуйте позже")

def check_statuses_job():
    """Фоновая задача проверки статусов"""
    logger.info(f"🔍 Проверка статусов игроков... {datetime.now()}")
    
    try:
        all_players = set(player for _, player in db.get_tracked_players())
        
        for player_nickname in all_players:
            try:
                current_status = get_player_status(player_nickname)
                if current_status is None:
                    continue
                    
                last_status = db.get_player_status(player_nickname)
                
                if last_status != current_status:
                    logger.info(f"🔄 Изменение статуса {player_nickname}: {last_status} -> {current_status}")
                    db.update_player_status(player_nickname, current_status)
                    
                    # Уведомляем всех пользователей
                    user_ids = db.get_users_tracking_player(player_nickname)
                    for user_id in user_ids:
                        try:
                            bot.send_message(
                                user_id,
                                f"⚡ Изменение статуса!\n"
                                f"Игрок: {player_nickname}\n"
                                f"Был: {last_status}\n"
                                f"Стал: {current_status}"
                            )
                        except Exception as e:
                            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
                            
            except Exception as e:
                logger.error(f"Ошибка проверки статуса для {player_nickname}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в check_statuses_job: {e}")

def run_scheduler():
    """Запуск планировщика в отдельном потоке"""
    schedule.every(30).seconds.do(check_statuses_job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    """Основная функция запуска бота"""
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("🤖 Бот запущен! Ожидаем сообщения...")
    logger.info("📊 Фоновая проверка статусов запущена каждые 30 секунд")
    
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()