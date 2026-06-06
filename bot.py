"""
VK-бот для привлечения курьеров-партнёров Яндекс Еды — Санкт-Петербург
Запуск: python bot.py
"""

import logging
import random
import json
from datetime import datetime

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import VK_TOKEN, ADMIN_VK_ID, GROUP_ID

# ── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Инициализация ─────────────────────────────────────────────────────────────
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session, group_id=GROUP_ID)

# ── Хранилище состояний пользователей (в памяти) ──────────────────────────────
# Структура: { user_id: { "state": "...", "data": {...} } }
users: dict = {}

# ── Состояния диалога ─────────────────────────────────────────────────────────
STATE_START      = "start"
STATE_CITY       = "city"
STATE_CITY_OTHER = "city_other"
STATE_AGE        = "age"
STATE_TRANSPORT  = "transport"
STATE_SCHEDULE   = "schedule"
STATE_DOCUMENTS  = "documents"
STATE_NAME       = "name"
STATE_PHONE      = "phone"
STATE_CONSENT    = "consent"
STATE_DONE       = "done"

# ── Тексты ────────────────────────────────────────────────────────────────────
FAQ_TEXT = """❓ Частые вопросы

🔹 Можно ли совмещать с учёбой или основной занятостью?
Да, многие рассматривают доставку как подработку в свободное время. Режим зависит от выбранных слотов.

🔹 Можно ли доставлять рядом с домом?
Можно подбирать удобные районы и зоны доставки. Доступность зависит от города и актуальных условий сервиса.

🔹 Нужен ли транспорт?
Не всегда. Можно рассмотреть пеший формат, велосипед, самокат или авто. Подходящий вариант уточните при подключении.

🔹 Каков доход курьера-партнёра?
Вознаграждение зависит от города, количества заказов, времени выходов и формата доставки. Мы не обещаем фиксированных сумм.

🔹 Это официальное сообщество Яндекс Еды?
Нет. Это страница партнёрского привлечения. Мы помогаем разобраться с подключением через партнёрскую ссылку.

🔹 Заявка к чему-то обязывает?
Нет. Вы просто отвечаете на несколько вопросов и узнаёте, какой формат может вам подойти."""

CONDITIONS_TEXT = """💡 Условия сотрудничества

✅ Минимальная оплата в отдельных слотах
В некоторых слотах может быть предусмотрена минимальная оплата при соблюдении условий выхода.

🛡 Страховые программы
Для курьеров-партнёров могут быть доступны страховые программы. Уточняйте при подключении.

⚖️ Поддержка и консультации
В отдельных случаях могут быть доступны консультации и справочные материалы.

🎁 Чаевые и бонусы
Курьеру-партнёру могут быть доступны чаевые, бонусы и дополнительные условия.

📈 Повышенные коэффициенты
Система предлагает слоты с повышенным коэффициентом вознаграждения.

⏱ Оплата ожидания
Если заказ в ресторане ещё не готов — время ожидания может быть оплачено.

Все условия зависят от города, формата и актуальных правил сервиса."""

# ── Клавиатуры ────────────────────────────────────────────────────────────────

def kb_start():
    kb = VkKeyboard(one_time=False)
    kb.add_button("🚀 Хочу попробовать", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("💡 Узнать условия", color=VkKeyboardColor.PRIMARY)
    kb.add_button("❓ Частые вопросы", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_city():
    kb = VkKeyboard(one_time=True)
    kb.add_button("Санкт-Петербург", color=VkKeyboardColor.POSITIVE)
    kb.add_button("Другой город", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_age():
    kb = VkKeyboard(one_time=True)
    kb.add_button("Да, мне 18+", color=VkKeyboardColor.POSITIVE)
    kb.add_button("Нет, мне меньше 18", color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

def kb_transport():
    kb = VkKeyboard(one_time=True)
    kb.add_button("🚶 Пешком", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🚲 Велосипед", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("🛴 Самокат", color=VkKeyboardColor.PRIMARY)
    kb.add_button("🚗 Авто", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("Пока не знаю", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_schedule():
    kb = VkKeyboard(one_time=True)
    kb.add_button("По вечерам", color=VkKeyboardColor.PRIMARY)
    kb.add_button("В выходные", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("В свободное время", color=VkKeyboardColor.PRIMARY)
    kb.add_button("Хочу чаще", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("Пока не знаю", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_documents():
    kb = VkKeyboard(one_time=True)
    kb.add_button("Паспорт РФ", color=VkKeyboardColor.PRIMARY)
    kb.add_button("Документы ЕАЭС", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("Патент / другие", color=VkKeyboardColor.PRIMARY)
    kb.add_button("Хочу уточнить", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_consent():
    kb = VkKeyboard(one_time=True)
    kb.add_button("✅ Согласен", color=VkKeyboardColor.POSITIVE)
    kb.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_back():
    kb = VkKeyboard(one_time=True)
    kb.add_button("🔄 Вернуться в начало", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_final():
    kb = VkKeyboard(one_time=False)
    kb.add_button("🚀 Перейти к регистрации", color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button("❓ Частые вопросы", color=VkKeyboardColor.SECONDARY)
    kb.add_line()
    kb.add_button("🔄 Вернуться в начало", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def kb_empty():
    kb = VkKeyboard(one_time=True)
    return kb.get_keyboard()

# ── Отправка сообщения ────────────────────────────────────────────────────────

def send(user_id: int, text: str, keyboard: str = None):
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": random.randint(0, 2**31),
    }
    if keyboard:
        params["keyboard"] = keyboard
    try:
        vk.messages.send(**params)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения {user_id}: {e}")

# ── Получить состояние пользователя ───────────────────────────────────────────

def get_user(user_id: int) -> dict:
    if user_id not in users:
        users[user_id] = {"state": STATE_START, "data": {}}
    return users[user_id]

def set_state(user_id: int, state: str):
    get_user(user_id)["state"] = state

def set_data(user_id: int, key: str, value):
    get_user(user_id)["data"][key] = value

# ── Уведомление администратору ────────────────────────────────────────────────

def notify_admin(user_id: int):
    if not ADMIN_VK_ID:
        return
    data = get_user(user_id)["data"]
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    text = (
        f"🚀 Новый лид!\n\n"
        f"👤 Имя: {data.get('name', '—')}\n"
        f"📱 Телефон: {data.get('phone', '—')}\n"
        f"🔗 VK: vk.com/id{user_id}\n"
        f"📍 Город: {data.get('city', '—')}\n"
        f"🎂 Возраст: 18+\n"
        f"🚗 Формат: {data.get('transport', '—')}\n"
        f"🕐 Режим доставок: {data.get('schedule', '—')}\n"
        f"📄 Документы: {data.get('documents', '—')}\n"
        f"📅 Дата: {now}\n\n"
        f"🏷 Статус: новый лид"
    )
    try:
        vk.messages.send(
            user_id=ADMIN_VK_ID,
            message=text,
            random_id=random.randint(0, 2**31),
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")

# ── Обработка сообщений ────────────────────────────────────────────────────────

def handle_message(user_id: int, text: str):
    text = text.strip()
    user = get_user(user_id)
    state = user["state"]

    # ── Глобальные команды (работают из любого состояния) ──
    if text.lower() in ["/start", "начать", "старт", "привет", "start"]:
        return cmd_start(user_id)

    if text == "🔄 Вернуться в начало":
        return cmd_start(user_id)

    if text == "💡 Узнать условия":
        send(user_id, CONDITIONS_TEXT, kb_start())
        return

    if text == "❓ Частые вопросы":
        send(user_id, FAQ_TEXT, kb_start())
        return

    # ── Маршрутизация по состоянию ──
    if state == STATE_START:
        if text == "🚀 Хочу попробовать":
            set_state(user_id, STATE_CITY)
            send(user_id,
                 "В каком городе вы хотите выходить на доставку?",
                 kb_city())
        else:
            cmd_start(user_id)

    elif state == STATE_CITY:
        if text == "Санкт-Петербург":
            set_data(user_id, "city", "Санкт-Петербург")
            set_state(user_id, STATE_AGE)
            send(user_id,
                 "Отлично, начнём со СПб 👍\n\nВам уже есть 18 лет?",
                 kb_age())
        elif text == "Другой город":
            set_state(user_id, STATE_CITY_OTHER)
            send(user_id,
                 "Напишите ваш город — подскажу, можно ли рассмотреть подключение там.",
                 kb_empty())
        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_city())

    elif state == STATE_CITY_OTHER:
        set_data(user_id, "city", text)
        set_state(user_id, STATE_AGE)
        send(user_id,
             f"Понял, {text}. Уточним детали — вам уже есть 18 лет?",
             kb_age())

    elif state == STATE_AGE:
        if text == "Да, мне 18+":
            set_data(user_id, "age", "18+")
            set_state(user_id, STATE_TRANSPORT)
            send(user_id,
                 "Какой формат доставки вам ближе?",
                 kb_transport())
        elif text == "Нет, мне меньше 18":
            set_state(user_id, STATE_START)
            users[user_id]["data"] = {}
            send(user_id,
                 "Пока подключение невозможно — для старта нужен возраст от 18 лет.\n\n"
                 "Можете вернуться к боту позже 👍",
                 kb_back())
        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_age())

    elif state == STATE_TRANSPORT:
        valid = {"🚶 Пешком", "🚲 Велосипед", "🛴 Самокат", "🚗 Авто", "Пока не знаю"}
        if text in valid:
            set_data(user_id, "transport", text)
            set_state(user_id, STATE_SCHEDULE)
            send(user_id,
                 "Хорошо. Когда вам было бы удобно выходить на доставку?",
                 kb_schedule())
        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_transport())

    elif state == STATE_SCHEDULE:
        valid = {"По вечерам", "В выходные", "В свободное время", "Хочу чаще", "Пока не знаю"}
        if text in valid:
            set_data(user_id, "schedule", text)
            set_state(user_id, STATE_DOCUMENTS)
            send(user_id,
                 "Понял. Партнёрство с Яндекс Едой можно совмещать с учёбой, "
                 "основной занятостью или другими делами.\n\n"
                 "Какие документы у вас есть?",
                 kb_documents())
        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_schedule())

    elif state == STATE_DOCUMENTS:
        valid = {"Паспорт РФ", "Документы ЕАЭС", "Патент / другие", "Хочу уточнить"}
        if text in valid:
            set_data(user_id, "documents", text)
            set_state(user_id, STATE_NAME)
            send(user_id,
                 "Список документов для оформления зависит от формата сотрудничества — "
                 "уточним на следующем шаге.\n\n"
                 "Оставьте, пожалуйста, имя и номер телефона, чтобы мы могли помочь "
                 "с подключением, если возникнут вопросы.\n\n"
                 "Сначала напишите ваше имя:",
                 kb_empty())
        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_documents())

    elif state == STATE_NAME:
        if len(text) < 2:
            send(user_id, "Пожалуйста, введите корректное имя.", kb_empty())
            return
        set_data(user_id, "name", text)
        set_state(user_id, STATE_PHONE)
        send(user_id,
             f"Приятно познакомиться, {text}! 👋\n\n"
             "Теперь введите номер телефона в формате +7XXXXXXXXXX:",
             kb_empty())

    elif state == STATE_PHONE:
        digits = "".join(c for c in text if c.isdigit())
        if len(digits) < 10:
            send(user_id,
                 "Пожалуйста, введите корректный номер телефона, например +79001234567.",
                 kb_empty())
            return
        set_data(user_id, "phone", text)
        set_state(user_id, STATE_CONSENT)
        send(user_id,
             "Нажимая кнопку ниже, вы соглашаетесь на обработку ваших данных "
             "для связи по вопросу подключения к сервису.",
             kb_consent())

    elif state == STATE_CONSENT:
        if text == "✅ Согласен":
            set_state(user_id, STATE_DONE)
            send(user_id,
                 "Спасибо, заявка сохранена ✅\n\n"
                 "Дальше можно перейти к регистрации.\n"
                 "После перехода следуйте инструкции на странице подключения.\n\n"
                 "Если возникнут вопросы — напишите, я помогу разобраться.",
                 kb_final())
            notify_admin(user_id)

        elif text == "◀️ Назад":
            set_state(user_id, STATE_PHONE)
            send(user_id, "Введите номер телефона:", kb_empty())

        else:
            send(user_id, "Выберите вариант из кнопок 👇", kb_consent())

    elif state == STATE_DONE:
        if text == "🚀 Перейти к регистрации":
            
            send(user_id,
                 "Переходите по ссылке для подключения к сервису:\n"
                 "👉 https://reg.eda.yandex.ru/?advertisement_campaign=forms_for_agents&user_invite_code=acd568205bad49acafccbcf7ace44ca5&utm_content=blank&utm_source=vk\n\n"
                 "Следуйте инструкции на странице — там всё подробно описано.\n"
                 "Если что-то непонятно — напишите сюда, помогу 👍",
                 kb_final())
        else:
            send(user_id, "Выберите действие из кнопок 👇", kb_final())

    else:
        cmd_start(user_id)


def cmd_start(user_id: int):
    """Стартовое сообщение и сброс состояния."""
    users[user_id] = {"state": STATE_START, "data": {}}
    send(user_id,
         "Привет 👋\n\n"
         "Я помогу разобраться, подойдёт ли вам формат доставки заказов "
         "в Санкт-Петербурге.\n\n"
         "Здесь можно:\n"
         "🚀 узнать условия подключения к сервису\n"
         "🛵 выбрать удобный формат доставки\n"
         "📍 понять, можно ли выходить на слоты рядом с домом\n"
         "📲 получить инструкцию по регистрации\n\n"
         "Это займёт около 1 минуты.",
         kb_start())


# ── Главный цикл ──────────────────────────────────────────────────────────────

def main():
    logger.info("VK-бот запущен...")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text or ""
            logger.info(f"Сообщение от {user_id}: {text!r}")
            try:
                handle_message(user_id, text)
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения от {user_id}: {e}")
                send(user_id,
                     "Произошла ошибка. Попробуйте написать /start для перезапуска.",
                     kb_back())


if __name__ == "__main__":
    main()
