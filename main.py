import os
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8690207690:AAFbUy-dd1akU1xelht_fD72EGbpnrAiS8o"
WEATHER_API_KEY = "3813f517bca011b6230db64ff9907de5"

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

user_languages = {}
user_state = {}  # "choosing_lang" or "choosing_city"

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
        "lang_set": "✅ Язык установлен: *Русский*\n\nНапиши название города чтобы узнать погоду!",
        "searching": "🔍 Ищу погоду для *{}*...",
        "not_found": (
            "❌ Город *{}* не найден!\n\n"
            "Проверь написание и попробуй снова.\n"
            "Пример: `Лондон`, `Нью-Йорк`, `Токио`\n\n"
            "💡 Попробуй написать город на английском, например: `Moscow`, `Berlin`"
        ),
        "location_error": "❌ Не удалось получить погоду. Попробуй ещё раз!",
        "location_instructions": (
            "📍 Чтобы поделиться локацией:\n\n"
            "1️⃣ Нажми на скрепку 📎 внизу\n"
            "2️⃣ Выбери *Геопозиция*\n"
            "3️⃣ Отправь своё местоположение"
        ),
        "weather_title": "Погода в",
        "temperature": "🌡️ Температура",
        "feels_like": "ощущается как",
        "condition": "🌈 Состояние",
        "humidity": "💧 Влажность",
        "wind": "💨 Ветер",
        "outfit_title": "👗 *Что надеть сегодня:*",
        "footer": "_Напиши другой город, чтобы проверить погоду там!_",
        "api_lang": "ru",
        "keyboard": [["📍 Моё местоположение", "🌐 Сменить язык"]],
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
        "lang_set": "✅ Мову встановлено: *Українська*\n\nНапиши назву міста щоб дізнатися погоду!",
        "searching": "🔍 Шукаю погоду для *{}*...",
        "not_found": (
            "❌ Місто *{}* не знайдено!\n\n"
            "Перевір написання та спробуй знову.\n"
            "Приклад: `Лондон`, `Нью-Йорк`, `Токіо`\n\n"
            "💡 Спробуй написати місто англійською, наприклад: `Kyiv`, `Berlin`"
        ),
        "location_error": "❌ Не вдалося отримати погоду. Спробуй ще раз!",
        "location_instructions": (
            "📍 Щоб поділитися локацією:\n\n"
            "1️⃣ Натисни на скріпку 📎 внизу\n"
            "2️⃣ Вибери *Геопозиція*\n"
            "3️⃣ Відправ своє місцезнаходження"
        ),
        "weather_title": "Погода в",
        "temperature": "🌡️ Температура",
        "feels_like": "відчувається як",
        "condition": "🌈 Стан",
        "humidity": "💧 Вологість",
        "wind": "💨 Вітер",
        "outfit_title": "👗 *Що вдягнути сьогодні:*",
        "footer": "_Напиши інше місто, щоб перевірити погоду там!_",
        "api_lang": "uk",
        "keyboard": [["📍 Моє місцезнаходження", "🌐 Змінити мову"]],
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
            "I'll tell you the current weather and what to wear! 🌤️👕\n\n"
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
        "weather_title": "Weather in",
        "temperature": "🌡️ Temperature",
        "feels_like": "feels like",
        "condition": "🌈 Condition",
        "humidity": "💧 Humidity",
        "wind": "💨 Wind",
        "outfit_title": "👗 *What to wear today:*",
        "footer": "_Type another city to check the weather there!_",
        "api_lang": "en",
        "keyboard": [["📍 My Location", "🌐 Change Language"]],
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

LANG_BUTTONS = ["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]
LOCATION_BUTTONS = ["📍 Моё местоположение", "📍 Моє місцезнаходження", "📍 My Location"]
SWITCH_BUTTONS = ["🌐 Сменить язык", "🌐 Змінити мову", "🌐 Change Language"]


def get_lang(user_id: int) -> str:
    return user_languages.get(user_id, "en")


def get_weather(city: str, lang: str):
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": lang}
    response = requests.get(WEATHER_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_clothing_advice(temp, weather_desc, wind_speed, t):
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
    if any(w in weather_desc.lower() for w in rain_keywords):
        advice += [c["rain_1"], c["rain_2"]]
    if any(w in weather_desc.lower() for w in ["снег", "сніг", "snow"]):
        advice += [c["snow_1"], c["snow_2"]]
    if wind_speed > 10:
        advice.append(c["wind"])
    return "\n".join(f"  {item}" for item in advice)


def format_weather_message(data, lang):
    t = TEXTS[lang]
    city = data["name"]
    country = data["sys"]["country"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    description = data["weather"][0]["description"].capitalize()
    icon = data["weather"][0]["icon"]
    sky_emojis = {"01": "☀️", "02": "🌤️", "03": "⛅", "04": "☁️",
                  "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"}
    sky = sky_emojis.get(icon[:2], "🌡️")
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


def show_lang_keyboard():
    keyboard = [["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.message.from_user.id] = "choosing_lang"
    await update.message.reply_text(
        "🌐 Выбери язык / Оберіть мову / Choose language:",
        reply_markup=show_lang_keyboard()
    )


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.message.from_user.id] = "choosing_lang"
    await update.message.reply_text(
        "🌐 Выбери язык / Оберіть мову / Choose language:",
        reply_markup=show_lang_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.message.from_user.id)
    await update.message.reply_text(TEXTS[lang]["help"], parse_mode="Markdown")


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    t = TEXTS[lang]
    location = update.message.location
    params = {"lat": location.latitude, "lon": location.longitude,
              "appid": WEATHER_API_KEY, "units": "metric", "lang": t["api_lang"]}
    response = requests.get(WEATHER_URL, params=params)
    if response.status_code == 200:
        await update.message.reply_text(format_weather_message(response.json(), lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(t["location_error"])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_state.get(user_id, "choosing_city")

    # ── Language selection ──────────────────────────────
    if text in LANG_BUTTONS or state == "choosing_lang":
        if text == "🇺🇦 Українська":
            user_languages[user_id] = "uk"
            lang = "uk"
        elif text == "🇬🇧 English":
            user_languages[user_id] = "en"
            lang = "en"
        elif text == "🇷🇺 Русский":
            user_languages[user_id] = "ru"
            lang = "ru"
        else:
            # Still waiting for language selection
            await update.message.reply_text(
                "🌐 Выбери язык / Оберіть мову / Choose language:",
                reply_markup=show_lang_keyboard()
            )
            return

        user_state[user_id] = "choosing_city"
        t = TEXTS[lang]
        reply_markup = ReplyKeyboardMarkup(t["keyboard"], resize_keyboard=True)
        await update.message.reply_text(t["lang_set"], parse_mode="Markdown", reply_markup=reply_markup)
        await update.message.reply_text(t["welcome"], parse_mode="Markdown")
        return

    lang = get_lang(user_id)
    t = TEXTS[lang]

    # ── Switch language button ──────────────────────────
    if text in SWITCH_BUTTONS:
        user_state[user_id] = "choosing_lang"
        await update.message.reply_text(
            "🌐 Выбери язык / Оберіть мову / Choose language:",
            reply_markup=show_lang_keyboard()
        )
        return

    # ── Location button ─────────────────────────────────
    if text in LOCATION_BUTTONS:
        await update.message.reply_text(t["location_instructions"], parse_mode="Markdown")
        return

    # ── City search ─────────────────────────────────────
    await update.message.reply_text(t["searching"].format(text), parse_mode="Markdown")
    data = get_weather(text, t["api_lang"])
    if data:
        await update.message.reply_text(format_weather_message(data, lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(t["not_found"].format(text), parse_mode="Markdown")


def main():
    print("🤖 Бот запускается...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот работает!")
    app.run_polling()


if __name__ == "__main__":
    main()
