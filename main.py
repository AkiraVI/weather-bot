import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ============================
TELEGRAM_TOKEN = "8690207690:AAFbUy-dd1akU1xelht_fD72EGbpnrAiS8o"
WEATHER_API_KEY = "3813f517bca011b6230db64ff9907de5"
# ============================

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

CHOOSING_LANG, CHOOSING_CITY = range(2)

user_languages = {}

TEXTS = {
    "ru": {
        "welcome": (
            "👋 *Добро пожаловать в бот Погода и Одежда!*\n\n"
            "Я скажу тебе текущую погоду и что лучше надеть! 🌤️👕\n\n"
            "Просто *напиши название города* (например: `Москва`, `Берлин`, `Токио`)\n"
            "или поделись своим 📍 местоположением!"
        ),
        "help": (
            "ℹ️ *Как пользоваться ботом:*\n\n"
            "1️⃣ Напиши название города (например: `Париж`, `Дубай`, `Лондон`)\n"
            "2️⃣ Или нажми кнопку 📎 и поделись геолокацией\n"
            "3️⃣ Я покажу погоду и советы по одежде!\n\n"
            "Команды:\n"
            "/start — Приветственное сообщение\n"
            "/language — Сменить язык\n"
            "/help — Это сообщение"
        ),
        "choose_lang": "🌐 Выбери язык / Choose language / Оберіть мову:",
        "lang_set": "✅ Язык установлен: *Русский*\n\nНапиши название города чтобы узнать погоду!",
        "searching": "🔍 Ищу погоду для *{}*...",
        "not_found": (
            "❌ Город *{}* не найден!\n\n"
            "Проверь написание и попробуй снова.\n"
            "Пример: `Лондон`, `Нью-Йорк`, `Токио`\n\n"
            "💡 Попробуй написать город на английском, например: `Moscow`, `Berlin`"
        ),
        "location_error": "❌ Не удалось получить погоду для твоего местоположения. Попробуй ещё раз!",
        "location_instructions": (
            "📍 Чтобы поделиться локацией:\n\n"
            "1️⃣ Нажми на скрепку 📎 внизу\n"
            "2️⃣ Выбери *Геопозиция*\n"
            "3️⃣ Отправь своё местоположение"
        ),
        "enter_city": "📝 Напиши название города, например: `Москва` или `Токио`",
        "weather_title": "Погода в",
        "temperature": "🌡️ Температура",
        "feels_like": "ощущается как",
        "condition": "🌈 Состояние",
        "humidity": "💧 Влажность",
        "wind": "💨 Ветер",
        "outfit_title": "👗 *Что надеть сегодня:*",
        "footer": "_Напиши другой город, чтобы проверить погоду там!_",
        "api_lang": "ru",
        "keyboard": [["📍 Моё местоположение"], ["🌐 Сменить язык"]],
        "clothing": {
            "very_cold_1": "🧥 Тёплое зимнее пальто, термобельё, шерстяной свитер",
            "very_cold_2": "🧣 Плотный шарф, тёплая шапка, перчатки — обязательно!",
            "very_cold_3": "👢 Утеплённые непромокаемые сапоги или ботинки",
            "cold_1": "🧥 Зимняя куртка или пальто",
            "cold_2": "🧣 Шарф и лёгкие перчатки не помешают",
            "cold_3": "👟 Закрытая тёплая обувь или ботинки",
            "cool_1": "🧣 Демисезонная куртка или толстовка",
            "cool_2": "👖 Длинные брюки, можно надеть свитер",
            "cool_3": "👟 Закрытая обувь",
            "mild_1": "👕 Лёгкая куртка или кардиган",
            "mild_2": "👖 Джинсы или лёгкие брюки",
            "mild_3": "👟 Кроссовки или повседневная обувь",
            "warm_1": "👕 Футболка или лёгкая рубашка — комфортная погода!",
            "warm_2": "👖 Джинсы или чиносы",
            "warm_3": "👟 Кроссовки или мокасины",
            "hot_1": "👕 Лёгкая футболка или летняя рубашка",
            "hot_2": "🩳 Шорты или лёгкое платье/юбка",
            "hot_3": "👡 Сандалии или дышащая обувь",
            "rain_1": "☔ Возьми зонт или надень водонепроницаемую куртку!",
            "rain_2": "👢 Лучше надеть непромокаемую обувь",
            "snow_1": "❄️ Нескользящие сапоги — очень рекомендуется",
            "snow_2": "🧤 Водонепроницаемые перчатки",
            "wind": "💨 Ветрено! Надень ветровку или крепче держи шапку",
        }
    },
    "uk": {
        "welcome": (
            "👋 *Ласкаво просимо до бота Погода та Одяг!*\n\n"
            "Я розкажу тобі про поточну погоду та що краще вдягнути! 🌤️👕\n\n"
            "Просто *напиши назву міста* (наприклад: `Київ`, `Берлін`, `Токіо`)\n"
            "або поділися своїм 📍 місцезнаходженням!"
        ),
        "help": (
            "ℹ️ *Як користуватися ботом:*\n\n"
            "1️⃣ Напиши назву міста (наприклад: `Париж`, `Дубай`, `Лондон`)\n"
            "2️⃣ Або натисни кнопку 📎 і поділися геолокацією\n"
            "3️⃣ Я покажу погоду та поради щодо одягу!\n\n"
            "Команди:\n"
            "/start — Привітальне повідомлення\n"
            "/language — Змінити мову\n"
            "/help — Це повідомлення"
        ),
        "choose_lang": "🌐 Виберіть мову / Choose language / Выбери язык:",
        "lang_set": "✅ Мову встановлено: *Українська*\n\nНапиши назву міста щоб дізнатися погоду!",
        "searching": "🔍 Шукаю погоду для *{}*...",
        "not_found": (
            "❌ Місто *{}* не знайдено!\n\n"
            "Перевір написання та спробуй знову.\n"
            "Приклад: `Лондон`, `Нью-Йорк`, `Токіо`\n\n"
            "💡 Спробуй написати місто англійською, наприклад: `Kyiv`, `Berlin`"
        ),
        "location_error": "❌ Не вдалося отримати погоду для твого місцезнаходження. Спробуй ще раз!",
        "location_instructions": (
            "📍 Щоб поділитися локацією:\n\n"
            "1️⃣ Натисни на скріпку 📎 внизу\n"
            "2️⃣ Вибери *Геопозиція*\n"
            "3️⃣ Відправ своє місцезнаходження"
        ),
        "enter_city": "📝 Напиши назву міста, наприклад: `Київ` або `Токіо`",
        "weather_title": "Погода в",
        "temperature": "🌡️ Температура",
        "feels_like": "відчувається як",
        "condition": "🌈 Стан",
        "humidity": "💧 Вологість",
        "wind": "💨 Вітер",
        "outfit_title": "👗 *Що вдягнути сьогодні:*",
        "footer": "_Напиши інше місто, щоб перевірити погоду там!_",
        "api_lang": "uk",
        "keyboard": [["📍 Моє місцезнаходження"], ["🌐 Змінити мову"]],
        "clothing": {
            "very_cold_1": "🧥 Тепле зимове пальто, термобілизна, вовняний светр",
            "very_cold_2": "🧣 Щільний шарф, тепла шапка, рукавиці — обов'язково!",
            "very_cold_3": "👢 Утеплені непромокаючі чоботи або черевики",
            "cold_1": "🧥 Зимова куртка або пальто",
            "cold_2": "🧣 Шарф і легкі рукавиці не завадять",
            "cold_3": "👟 Закрите тепле взуття або черевики",
            "cool_1": "🧣 Демісезонна куртка або худі",
            "cool_2": "👖 Довгі штани, можна вдягнути светр",
            "cool_3": "👟 Закрите взуття",
            "mild_1": "👕 Легка куртка або кардиган",
            "mild_2": "👖 Джинси або легкі штани",
            "mild_3": "👟 Кросівки або повсякденне взуття",
            "warm_1": "👕 Футболка або легка сорочка — комфортна погода!",
            "warm_2": "👖 Джинси або чіноси",
            "warm_3": "👟 Кросівки або мокасини",
            "hot_1": "👕 Легка футболка або літня сорочка",
            "hot_2": "🩳 Шорти або легка сукня/спідниця",
            "hot_3": "👡 Сандалі або дихаюче взуття",
            "rain_1": "☔ Візьми парасольку або вдягни водонепроникну куртку!",
            "rain_2": "👢 Краще вдягнути непромокаюче взуття",
            "snow_1": "❄️ Нековзаючі чоботи — дуже рекомендується",
            "snow_2": "🧤 Водонепроникні рукавиці",
            "wind": "💨 Вітряно! Вдягни вітровку або міцніше тримай шапку",
        }
    },
    "en": {
        "welcome": (
            "👋 *Welcome to the Weather & Outfit Bot!*\n\n"
            "I'll tell you the current weather and what to wear outside! 🌤️👕\n\n"
            "Just *type a city name* (e.g. `London`, `Berlin`, `Tokyo`)\n"
            "or share your 📍 location!"
        ),
        "help": (
            "ℹ️ *How to use this bot:*\n\n"
            "1️⃣ Type any city name (e.g. `Paris`, `Dubai`, `London`)\n"
            "2️⃣ Or tap 📎 and share your location\n"
            "3️⃣ I'll show the weather and outfit advice!\n\n"
            "Commands:\n"
            "/start — Welcome message\n"
            "/language — Change language\n"
            "/help — This message"
        ),
        "choose_lang": "🌐 Choose language / Выбери язык / Оберіть мову:",
        "lang_set": "✅ Language set: *English*\n\nType a city name to get the weather!",
        "searching": "🔍 Searching weather for *{}*...",
        "not_found": (
            "❌ City *{}* not found!\n\n"
            "Check the spelling and try again.\n"
            "Example: `London`, `New York`, `Tokyo`"
        ),
        "location_error": "❌ Couldn't get weather for your location. Please try again!",
        "location_instructions": (
            "📍 To share your location:\n\n"
            "1️⃣ Tap the paperclip 📎 below\n"
            "2️⃣ Select *Location*\n"
            "3️⃣ Send your current location"
        ),
        "enter_city": "📝 Type a city name, e.g. `London` or `Tokyo`",
        "weather_title": "Weather in",
        "temperature": "🌡️ Temperature",
        "feels_like": "feels like",
        "condition": "🌈 Condition",
        "humidity": "💧 Humidity",
        "wind": "💨 Wind",
        "outfit_title": "👗 *What to wear today:*",
        "footer": "_Type another city to check the weather there!_",
        "api_lang": "en",
        "keyboard": [["📍 My Location"], ["🌐 Change Language"]],
        "clothing": {
            "very_cold_1": "🧥 Heavy winter coat, thermal underwear, wool sweater",
            "very_cold_2": "🧣 Thick scarf, warm hat, gloves — essential!",
            "very_cold_3": "👢 Insulated waterproof boots",
            "cold_1": "🧥 Winter jacket or coat",
            "cold_2": "🧣 Scarf and light gloves recommended",
            "cold_3": "👟 Closed, warm shoes or boots",
            "cool_1": "🧣 Medium jacket or thick hoodie",
            "cool_2": "👖 Long pants, maybe layer with a sweater",
            "cool_3": "👟 Closed shoes",
            "mild_1": "👕 Light jacket or cardigan",
            "mild_2": "👖 Jeans or light trousers",
            "mild_3": "👟 Sneakers or casual shoes",
            "warm_1": "👕 T-shirt or light shirt — comfortable weather!",
            "warm_2": "👖 Jeans or chinos",
            "warm_3": "👟 Sneakers or loafers",
            "hot_1": "👕 Light t-shirt or summer shirt",
            "hot_2": "🩳 Shorts or a light dress/skirt",
            "hot_3": "👡 Sandals or breathable shoes",
            "rain_1": "☔ Bring an umbrella or wear a waterproof jacket!",
            "rain_2": "👢 Consider waterproof shoes/boots",
            "snow_1": "❄️ Non-slip boots strongly recommended",
            "snow_2": "🧤 Waterproof gloves",
            "wind": "💨 It's windy! Wear a windbreaker or hold on to your hat",
        }
    }
}

# ─── Weather & Clothing ───────────────────────────────────────────

def get_weather(city: str, lang: str) -> dict | None:
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": lang
    }
    response = requests.get(WEATHER_URL, params=params)
    print(response.json())
    if response.status_code == 200:
        return response.json()
    return None


def get_clothing_advice(temp: float, weather_desc: str, wind_speed: float, t: dict) -> str:
    advice = []
    c = t["clothing"]

    if temp <= 0:
        advice += [c["very_cold_1"], c["very_cold_2"], c["very_cold_3"]]
    elif temp <= 8:
        advice += [c["cold_1"], c["cold_2"], c["cold_3"]]
    elif temp <= 15:
        advice += [c["cool_1"], c["cool_2"], c["cool_3"]]
    elif temp <= 20:
        advice += [c["mild_1"], c["mild_2"], c["mild_3"]]
    elif temp <= 26:
        advice += [c["warm_1"], c["warm_2"], c["warm_3"]]
    else:
        advice += [c["hot_1"], c["hot_2"], c["hot_3"]]

    rain_keywords = ["дождь", "ливень", "морось", "гроза", "дощ", "злива", "rain", "drizzle", "shower", "storm"]
    if any(word in weather_desc.lower() for word in rain_keywords):
        advice += [c["rain_1"], c["rain_2"]]

    if any(word in weather_desc.lower() for word in ["снег", "сніг", "snow"]):
        advice += [c["snow_1"], c["snow_2"]]

    if wind_speed > 10:
        advice.append(c["wind"])

    return "\n".join(f"  {item}" for item in advice)


def format_weather_message(data: dict, lang: str) -> str:
    t = TEXTS[lang]
    city = data["name"]
    country = data["sys"]["country"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    description = data["weather"][0]["description"].capitalize()
    weather_icon = data["weather"][0]["icon"]

    sky_emojis = {
        "01": "☀️", "02": "🌤️", "03": "⛅", "04": "☁️",
        "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"
    }
    sky = sky_emojis.get(weather_icon[:2], "🌡️")
    clothing = get_clothing_advice(temp, description, wind_speed, t)

    return (
        f"{sky} *{t['weather_title']} {city}, {country}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{t['temperature']}: *{temp:.1f}°C* ({t['feels_like']} {feels_like:.1f}°C)\n"
        f"{t['condition']}: {description}\n"
        f"{t['humidity']}: {humidity}%\n"
        f"{t['wind']}: {wind_speed} м/с\n\n"
        f"{t['outfit_title']}\n"
        f"{clothing}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{t['footer']}"
    )


# ─── Handlers ────────────────────────────────────────────────────

def get_lang(user_id: int) -> str:
    return user_languages.get(user_id, "en")


ALL_LANG_BUTTONS = [
    "🌐 Сменить язык", "🌐 Змінити мову", "🌐 Change Language",
    "🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English",
    "📍 Моё местоположение", "📍 Моє місцезнаходження", "📍 My Location"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "🌐 Выбери язык / Оберіть мову / Choose language:",
        reply_markup=reply_markup
    )
    return CHOOSING_LANG


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "🌐 Выбери язык / Оберіть мову / Choose language:",
        reply_markup=reply_markup
    )
    return CHOOSING_LANG


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if "Українська" in text or "🇺🇦" in text:
        user_languages[user_id] = "uk"
        lang = "uk"
    elif "English" in text or "🇬🇧" in text:
        user_languages[user_id] = "en"
        lang = "en"
    else:
        user_languages[user_id] = "ru"
        lang = "ru"

    t = TEXTS[lang]
    reply_markup = ReplyKeyboardMarkup(t["keyboard"], resize_keyboard=True)
    await update.message.reply_text(t["lang_set"], parse_mode="Markdown", reply_markup=reply_markup)
    await update.message.reply_text(t["welcome"], parse_mode="Markdown")
    return CHOOSING_CITY


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.from_user.id)
    await update.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    t = TEXTS[lang]

    location = update.message.location
    params = {
        "lat": location.latitude,
        "lon": location.longitude,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "lang": t["api_lang"]
    }
    response = requests.get(WEATHER_URL, params=params)
    if response.status_code == 200:
        msg = format_weather_message(response.json(), lang)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(t["location_error"])
    return CHOOSING_CITY


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    t = TEXTS[lang]
    city = update.message.text.strip()

    # Language switch buttons
    if city in ["🌐 Сменить язык", "🌐 Змінити мову", "🌐 Change Language",
                "🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]:
        keyboard = [["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "🌐 Выбери язык / Оберіть мову / Choose language:",
            reply_markup=reply_markup
        )
        return CHOOSING_LANG

    # Location button
    if city in ["📍 Моё местоположение", "📍 Моє місцезнаходження", "📍 My Location"]:
        await update.message.reply_text(t["location_instructions"], parse_mode="Markdown")
        return CHOOSING_CITY

    # Search weather
    await update.message.reply_text(t["searching"].format(city), parse_mode="Markdown")
    data = get_weather(city, t["api_lang"])
    if data:
        msg = format_weather_message(data, lang)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(t["not_found"].format(city), parse_mode="Markdown")
    return CHOOSING_CITY


# ─── Main ────────────────────────────────────────────────────────

def main():
    print("🤖 Погодный бот запускается...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("language", language_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city),
        ],
states={
            CHOOSING_LANG: [
                MessageHandler(filters.Regex("^(🇷🇺 Русский|🇺🇦 Українська|🇬🇧 English)$"), set_language),
            ],
            CHOOSING_CITY: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("language", language_command),
            CommandHandler("help", help_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city),
            MessageHandler(filters.LOCATION, handle_location),
        ],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("help", help_command))

    print("✅ Бот работает! Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
