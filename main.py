import telebot
import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

# === ТОКЕН БОТА ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8366428807:AAGqmjS8NdusUgWxDI2IWxV-gB1SChbm5_E")
bot = telebot.TeleBot(BOT_TOKEN)

# === GOOGLE ТАБЛИЦА (через переменную окружения) ===
try:
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
    CLIENT = gspread.authorize(CREDS)
    SHEET = CLIENT.open("Акварель - Записи").sheet1  # ← Замени на имя твоей таблицы!
except Exception as e:
    print("Ошибка подключения к Google Таблице:", e)
    SHEET = None

# === СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ===
user_state = {}

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add("💅 Записаться", "✨ Услуги", "📍 Контакты")
    return markup

# === СТАРТ ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! 👋 Это студия маникюра и педикюра *«Акварель»* 💅\n\n"
        "Меня зовут Кристина — я помогу вам найти идеальное время для ухода за собой!\n"
        "Что вас интересует?",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# === УСЛУГИ ===
@bot.message_handler(func=lambda m: m.text == "✨ Услуги")
def services(message):
    bot.send_message(
        message.chat.id,
        "У нас вы найдёте всё для ухода за руками и ногами:\n\n"
        "• *Базовый маникюр с покрытием* — 1200 ₽\n"
        "• *SPA-педикюр с аромамаслами* — 2200 ₽\n"
        "• *Наращивание гель-лаком* — от 1800 ₽\n"
        "• *Коррекция ногтей* — 1500 ₽\n\n"
        "Хочу честно сказать — места на выходные разлетаются быстро! 😊\n"
        "Может, посмотрим, что свободно?",
        reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("💅 Записаться"),
        parse_mode="Markdown"
    )

# === КОНТАКТЫ ===
@bot.message_handler(func=lambda m: m.text == "📍 Контакты")
def contacts(message):
    bot.send_message(
        message.chat.id,
        "📍 *Адрес*: ул. Цветочная, 15 (рядом с парком)\n"
        "📞 *Телефон*: +7 (XXX) XXX-XX-XX\n"
        "🕒 *Режим работы*: ежедневно с 10:00 до 20:00\n\n"
        "Мы в Instagram: [@akvarel_nails](https://instagram.com/akvarel_nails)\n\n"
        "Жду вас! 💖",
        parse_mode="Markdown"
    )

# === НАЧАЛО ЗАПИСИ ===
@bot.message_handler(func=lambda m: m.text == "💅 Записаться")
def book_start(message):
    bot.send_message(
        message.chat.id,
        "Отлично! 💖 Давайте подберём удобное время.\n"
        "Как вас зовут?"
    )
    user_state[message.chat.id] = {"step": "name"}

# === СБОР ДАННЫХ ===
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "name")
def get_name(message):
    user_state[message.chat.id]["name"] = message.text.strip()
    bot.send_message(message.chat.id, "Напишите, пожалуйста, ваш номер телефона (можно с +7):")
    user_state[message.chat.id]["step"] = "phone"

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "phone")
def get_phone(message):
    user_state[message.chat.id]["phone"] = message.text.strip()
    bot.send_message(message.chat.id, "На какую дату хотите записаться? (Например: 15 июня)")
    user_state[message.chat.id]["step"] = "date"

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "date")
def get_date(message):
    user_state[message.chat.id]["date"] = message.text.strip()
    bot.send_message(message.chat.id, "На какое время? (Например: 14:30)")
    user_state[message.chat.id]["step"] = "time"

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "time")
def get_time(message):
    user_state[message.chat.id]["time"] = message.text.strip()
    bot.send_message(message.chat.id, "Какая услуга вас интересует?")
    user_state[message.chat.id]["step"] = "service"

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "service")
def get_service(message):
    chat_id = message.chat.id
    data = user_state[chat_id]
    data["service"] = message.text.strip()

    # Сохраняем в Google Таблицу
    success = False
    if SHEET:
        try:
            SHEET.append_row([
                data["date"],
                data["time"],
                data["name"],
                data["phone"],
                data["service"],
                "Новая"
            ])
            success = True
        except Exception as e:
            print("Ошибка записи в таблицу:", e)

    if success:
        bot.send_message(
            chat_id,
            f"Готово! 💫\n"
            f"Вы записаны на *{data['date']} в {data['time']}* на *{data['service']}*.\n\n"
            f"За день напомню — и пришлю, как нас найти 📍\n"
            f"А пока — отличного вам дня! ✨",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            chat_id,
            "Ой, что-то пошло не так с записью... 😕\n"
            "Но я всё равно запомнила вашу заявку!\n"
            "Администратор скоро свяжется с вами по телефону."
        )

    del user_state[chat_id]

# === ОБРАБОТКА ЛЮБОГО ТЕКСТА (мягкий ответ) ===
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "Не уверены, с чего начать? 😊\n"
        "Нажмите на кнопку ниже — я помогу найти то, что нужно!\n\n"
        "А ещё могу прислать фото наших работ — просто скажите «Покажи»!",
        reply_markup=main_menu()
    )

# === ЗАПУСК ===
if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)
