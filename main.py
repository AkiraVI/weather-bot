import os
import json
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TELEGRAM_TOKEN = "8690207690:AAFbUy-dd1akU1xelht_fD72EGbpnrAiS8o"
WEATHER_API_KEY = "3813f517bca011b6230db64ff9907de5"

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
AIR_URL = "https://api.openweathermap.org/data/2.5/air_pollution"

user_languages = {}
user_state = {}
user_cities = {}       # saved home city
user_notif_time = {}   # saved notification time "HH:MM"
user_notif_on = {}     # notification enabled True/False

scheduler = AsyncIOScheduler()

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
            "1️⃣ Напиши название города — получи погоду\n"
            "2️⃣ Или нажми 📍 и поделись геолокацией\n"
            "3️⃣ Нажми 📅 для прогноза на 5 дней\n"
            "4️⃣ Нажми ⏰ для настройки утренних уведомлений\n\n"
            "Команды:\n"
            "/start — Приветствие\n"
            "/language — Сменить язык\n"
            "/notify — Настроить уведомления\n"
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
        "today_range": "Сегодня",
        "condition": "🌈 Состояние",
        "humidity": "💧 Влажность",
        "wind": "💨 Ветер",
        "air_quality": "🌿 Качество воздуха",
        "air_levels": ["Отличное", "Хорошее", "Умеренное", "Плохое", "Очень плохое"],
        "outfit_title": "👗 *Что надеть сегодня:*",
        "footer": "_Напиши другой город, чтобы проверить погоду там!_",
        "forecast_btn": "📅 Прогноз на 5 дней",
        "forecast_title": "📅 Прогноз на 5 дней для",
        "forecast_ask": "🏙️ Для какого города показать прогноз?\nНапиши название города:",
        "notif_btn": "⏰ Уведомления",
        "notif_menu": (
            "⏰ *Настройка утренних уведомлений*\n\n"
            "Каждое утро я буду отправлять тебе погоду для твоего города!\n\n"
            "Текущий город: *{}*\n"
            "Время уведомления: *{}*\n"
            "Статус: *{}*"
        ),
        "notif_on": "✅ Включены",
        "notif_off": "❌ Выключены",
        "notif_set_city": "🏙️ Напиши название своего города для уведомлений:",
        "notif_set_time": "🕐 Напиши время уведомления в формате *ЧЧ:ММ*\nНапример: `07:30` или `08:00`",
        "notif_city_saved": "✅ Город сохранён: *{}*",
        "notif_time_saved": "✅ Время установлено: *{}*\nУведомления включены! 🎉",
        "notif_time_invalid": "❌ Неверный формат! Напиши время как `07:30` или `08:00`",
        "notif_enabled": "✅ Утренние уведомления *включены!*\nБудешь получать погоду каждый день в *{}* для города *{}*",
        "notif_disabled": "❌ Утренние уведомления *выключены*",
        "notif_no_city": "⚠️ Сначала сохрани свой город! Нажми ⏰ Уведомления",
        "morning_msg": "🌅 *Доброе утро!* Вот погода на сегодня:",
        "sunrise": "🌅 Восход",
        "sunset": "🌇 Закат",
        "currency_btn": "💱 Курс валют",
        "currency_title": "💱 *Курс валют к EUR:*",
        "currency_loading": "💱 Загружаю курс валют...",
        "currency_error": "❌ Не удалось загрузить курс валют. Попробуй позже.",
        "api_lang": "ru",
        "keyboard": [["📍 Моё местоположение", "🌐 Сменить язык"], ["📅 Прогноз на 5 дней", "⏰ Уведомления"], ["💱 Курс валют"]],
        "notif_keyboard": [["🏙️ Сменить город", "🕐 Сменить время"], ["✅ Включить", "❌ Выключить"], ["🔙 Назад"]],
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
            "1️⃣ Напиши назву міста — отримай погоду\n"
            "2️⃣ Або натисни 📍 і поділися геолокацією\n"
            "3️⃣ Натисни 📅 для прогнозу на 5 днів\n"
            "4️⃣ Натисни ⏰ для налаштування ранкових сповіщень\n\n"
            "Команди:\n"
            "/start — Привітання\n"
            "/language — Змінити мову\n"
            "/notify — Налаштувати сповіщення\n"
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
        "today_range": "Сьогодні",
        "condition": "🌈 Стан",
        "humidity": "💧 Вологість",
        "wind": "💨 Вітер",
        "air_quality": "🌿 Якість повітря",
        "air_levels": ["Відмінна", "Добра", "Помірна", "Погана", "Дуже погана"],
        "outfit_title": "👗 *Що вдягнути сьогодні:*",
        "footer": "_Напиши інше місто, щоб перевірити погоду там!_",
        "forecast_btn": "📅 Прогноз на 5 днів",
        "forecast_title": "📅 Прогноз на 5 днів для",
        "forecast_ask": "🏙️ Для якого міста показати прогноз?\nНапиши назву міста:",
        "notif_btn": "⏰ Сповіщення",
        "notif_menu": (
            "⏰ *Налаштування ранкових сповіщень*\n\n"
            "Щоранку я буду надсилати тобі погоду для твого міста!\n\n"
            "Поточне місто: *{}*\n"
            "Час сповіщення: *{}*\n"
            "Статус: *{}*"
        ),
        "notif_on": "✅ Увімкнено",
        "notif_off": "❌ Вимкнено",
        "notif_set_city": "🏙️ Напиши назву свого міста для сповіщень:",
        "notif_set_time": "🕐 Напиши час сповіщення у форматі *ГГ:ХХ*\nНаприклад: `07:30` або `08:00`",
        "notif_city_saved": "✅ Місто збережено: *{}*",
        "notif_time_saved": "✅ Час встановлено: *{}*\nСповіщення увімкнено! 🎉",
        "notif_time_invalid": "❌ Невірний формат! Напиши час як `07:30` або `08:00`",
        "notif_enabled": "✅ Ранкові сповіщення *увімкнено!*\nБудеш отримувати погоду щодня о *{}* для міста *{}*",
        "notif_disabled": "❌ Ранкові сповіщення *вимкнено*",
        "notif_no_city": "⚠️ Спочатку збережи своє місто! Натисни ⏰ Сповіщення",
        "morning_msg": "🌅 *Доброго ранку!* Ось погода на сьогодні:",
        "sunrise": "🌅 Схід сонця",
        "sunset": "🌇 Захід сонця",
        "currency_btn": "💱 Курс валют",
        "currency_title": "💱 *Курс валют до EUR:*",
        "currency_loading": "💱 Завантажую курс валют...",
        "currency_error": "❌ Не вдалося завантажити курс валют. Спробуй пізніше.",
        "api_lang": "uk",
        "keyboard": [["📍 Моє місцезнаходження", "🌐 Змінити мову"], ["📅 Прогноз на 5 днів", "⏰ Сповіщення"], ["💱 Курс валют"]],
        "notif_keyboard": [["🏙️ Змінити місто", "🕐 Змінити час"], ["✅ Увімкнути", "❌ Вимкнути"], ["🔙 Назад"]],
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
            "1️⃣ Type a city name — get the weather\n"
            "2️⃣ Or tap 📍 and share your location\n"
            "3️⃣ Tap 📅 for 5-day forecast\n"
            "4️⃣ Tap ⏰ to set up morning notifications\n\n"
            "Commands:\n"
            "/start — Welcome\n"
            "/language — Change language\n"
            "/notify — Set up notifications\n"
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
        "today_range": "Today",
        "condition": "🌈 Condition",
        "humidity": "💧 Humidity",
        "wind": "💨 Wind",
        "air_quality": "🌿 Air Quality",
        "air_levels": ["Excellent", "Good", "Moderate", "Poor", "Very Poor"],
        "outfit_title": "👗 *What to wear today:*",
        "footer": "_Type another city to check the weather there!_",
        "forecast_btn": "📅 5-Day Forecast",
        "forecast_title": "📅 5-Day Forecast for",
        "forecast_ask": "🏙️ Which city do you want the forecast for?\nType a city name:",
        "notif_btn": "⏰ Notifications",
        "notif_menu": (
            "⏰ *Morning Notification Settings*\n\n"
            "Every morning I'll send you the weather for your city!\n\n"
            "Current city: *{}*\n"
            "Notification time: *{}*\n"
            "Status: *{}*"
        ),
        "notif_on": "✅ Enabled",
        "notif_off": "❌ Disabled",
        "notif_set_city": "🏙️ Type your home city name for notifications:",
        "notif_set_time": "🕐 Type notification time in *HH:MM* format\nExample: `07:30` or `08:00`",
        "notif_city_saved": "✅ City saved: *{}*",
        "notif_time_saved": "✅ Time set: *{}*\nNotifications enabled! 🎉",
        "notif_time_invalid": "❌ Invalid format! Type time like `07:30` or `08:00`",
        "notif_enabled": "✅ Morning notifications *enabled!*\nYou'll get weather every day at *{}* for *{}*",
        "notif_disabled": "❌ Morning notifications *disabled*",
        "notif_no_city": "⚠️ Save your home city first! Tap ⏰ Notifications",
        "morning_msg": "🌅 *Good morning!* Here's today's weather:",
        "sunrise": "🌅 Sunrise",
        "sunset": "🌇 Sunset",
        "currency_btn": "💱 Exchange Rates",
        "currency_title": "💱 *Exchange Rates to EUR:*",
        "currency_loading": "💱 Loading exchange rates...",
        "currency_error": "❌ Couldn't load exchange rates. Try again later.",
        "api_lang": "en",
        "keyboard": [["📍 My Location", "🌐 Change Language"], ["📅 5-Day Forecast", "⏰ Notifications"], ["💱 Exchange Rates"]],
        "notif_keyboard": [["🏙️ Change City", "🕐 Change Time"], ["✅ Enable", "❌ Disable"], ["🔙 Back"]],
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
FORECAST_BUTTONS = ["📅 Прогноз на 5 дней", "📅 Прогноз на 5 днів", "📅 5-Day Forecast"]
NOTIF_BUTTONS = ["⏰ Уведомления", "⏰ Сповіщення", "⏰ Notifications"]
NOTIF_CITY_BUTTONS = ["🏙️ Сменить город", "🏙️ Змінити місто", "🏙️ Change City"]
NOTIF_TIME_BUTTONS = ["🕐 Сменить время", "🕐 Змінити час", "🕐 Change Time"]
NOTIF_ENABLE_BUTTONS = ["✅ Включить", "✅ Увімкнути", "✅ Enable"]
NOTIF_DISABLE_BUTTONS = ["❌ Выключить", "❌ Вимкнути", "❌ Disable"]
BACK_BUTTONS = ["🔙 Назад", "🔙 Назад", "🔙 Back"]


def get_lang(user_id):
    return user_languages.get(user_id, "en")


def get_air_quality(lat, lon):
    response = requests.get(AIR_URL, params={"lat": lat, "lon": lon, "appid": WEATHER_API_KEY})
    if response.status_code == 200:
        return response.json()
    return None


def get_aqi_label(aqi, t):
    icons = ["🟢", "🟢", "🟡", "🟠", "🔴"]
    levels = t["air_levels"]
    if 1 <= aqi <= 5:
        return f"{icons[aqi-1]} {levels[aqi-1]}"
    return "N/A"


def get_weather(city, lang):
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": lang}
    response = requests.get(WEATHER_URL, params=params)
    if response.status_code != 200:
        return None
    data = response.json()
    forecast_params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": lang, "cnt": 8}
    forecast = requests.get(FORECAST_URL, params=forecast_params)
    if forecast.status_code == 200:
        temps = [item["main"]["temp"] for item in forecast.json()["list"]]
        data["temp_min"] = min(temps)
        data["temp_max"] = max(temps)
    else:
        data["temp_min"] = data["main"]["temp_min"]
        data["temp_max"] = data["main"]["temp_max"]
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]
    air = get_air_quality(lat, lon)
    if air:
        data["aqi"] = air["list"][0]["main"]["aqi"]
    return data


def get_forecast(city, lang):
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "lang": lang}
    response = requests.get(FORECAST_URL, params=params)
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
    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M")
    sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")
    clothing = get_clothing_advice(data.get("temp_max", temp), description, wind_speed, t)
    aqi_text = get_aqi_label(data.get("aqi", 0), t)
    return (
        f"{sky} *{t['weather_title']} {city}, {country}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{t['temperature']}: *{temp:.1f}°C* ({t['feels_like']} {feels_like:.1f}°C)\n"
        f"📊 {t['today_range']}: 🔵 {data.get('temp_min', temp):.1f}°C — 🔴 {data.get('temp_max', temp):.1f}°C\n"
        f"{t['condition']}: {description}\n"
        f"{t['humidity']}: {humidity}%\n"
        f"{t['wind']}: {wind_speed} м/с\n"
        f"{t['air_quality']}: {aqi_text}\n"
        f"{t['sunrise']}: {sunrise} — {t['sunset']}: {sunset}\n\n"
        f"{t['outfit_title']}\n"
        f"{clothing}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{t['footer']}"
    )


def format_forecast_message(data, lang, t):
    city = data["city"]["name"]
    country = data["city"]["country"]
    days = {}
    for item in data["list"]:
        date = item["dt_txt"].split(" ")[0]
        if date not in days:
            days[date] = []
        days[date].append(item)
    sky_emojis = {"01": "☀️", "02": "🌤️", "03": "⛅", "04": "☁️",
                  "09": "🌧️", "10": "🌦️", "11": "⛈️", "13": "❄️", "50": "🌫️"}
    msg = f"{t['forecast_title']} *{city}, {country}*\n━━━━━━━━━━━━━━━━━━\n"
    for i, (date, items) in enumerate(days.items()):
        if i >= 5:
            break
        temps = [item["main"]["temp"] for item in items]
        descriptions = [item["weather"][0]["description"] for item in items]
        icons = [item["weather"][0]["icon"] for item in items]
        temp_min = min(temps)
        temp_max = max(temps)
        description = descriptions[len(descriptions) // 2].capitalize()
        icon = icons[len(icons) // 2]
        sky = sky_emojis.get(icon[:2], "🌡️")
        days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        days_uk = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"]
        months_ru = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
        months_uk = ["", "Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"]
        day = datetime.strptime(date, "%Y-%m-%d")
        if lang == "ru":
            day_name = f"{days_ru[day.weekday()]}, {day.day:02d} {months_ru[day.month]}"
        elif lang == "uk":
            day_name = f"{days_uk[day.weekday()]}, {day.day:02d} {months_uk[day.month]}"
        else:
            day_name = day.strftime("%A, %d %b")
        msg += f"\n{sky} *{day_name}*\n"
        msg += f"  🔵 {temp_min:.1f}°C — 🔴 {temp_max:.1f}°C — {description}\n"
        if lang == "ru":
            if temp_max <= 0:
                outfit = "🧥 Тёплое пальто, перчатки, шапка"
            elif temp_max <= 8:
                outfit = "🧥 Зимняя куртка, шарф, перчатки"
            elif temp_max <= 15:
                outfit = "🧣 Куртка или толстовка"
            elif temp_max <= 20:
                outfit = "👕 Лёгкая куртка или кардиган"
            elif temp_max <= 26:
                outfit = "👕 Футболка и джинсы"
            else:
                outfit = "🩳 Лёгкая одежда, шорты или платье"
            if any("дождь" in d.lower() or "rain" in d.lower() for d in descriptions):
                outfit += " + ☔ зонт"
            if any("снег" in d.lower() or "snow" in d.lower() for d in descriptions):
                outfit += " + ❄️ сапоги"
        elif lang == "uk":
            if temp_max <= 0:
                outfit = "🧥 Тепле пальто, рукавиці, шапка"
            elif temp_max <= 8:
                outfit = "🧥 Зимова куртка, шарф, рукавиці"
            elif temp_max <= 15:
                outfit = "🧣 Куртка або худі"
            elif temp_max <= 20:
                outfit = "👕 Легка куртка або кардиган"
            elif temp_max <= 26:
                outfit = "👕 Футболка та джинси"
            else:
                outfit = "🩳 Легкий одяг, шорти або сукня"
            if any("дощ" in d.lower() or "rain" in d.lower() for d in descriptions):
                outfit += " + ☔ парасолька"
            if any("сніг" in d.lower() or "snow" in d.lower() for d in descriptions):
                outfit += " + ❄️ чоботи"
        else:
            if temp_max <= 0:
                outfit = "🧥 Heavy winter coat, gloves, warm hat"
            elif temp_max <= 8:
                outfit = "🧥 Winter jacket, scarf, gloves"
            elif temp_max <= 15:
                outfit = "🧣 Medium jacket or hoodie"
            elif temp_max <= 20:
                outfit = "👕 Light jacket or cardigan"
            elif temp_max <= 26:
                outfit = "👕 T-shirt and jeans"
            else:
                outfit = "🩳 Light clothes, shorts or dress"
            if any("rain" in d.lower() for d in descriptions):
                outfit += " + ☔ umbrella"
            if any("snow" in d.lower() for d in descriptions):
                outfit += " + ❄️ boots"
        msg += f"  👗 {outfit}\n"
    msg += "\n━━━━━━━━━━━━━━━━━━"
    return msg


def show_lang_keyboard():
    keyboard = [["🇷🇺 Русский", "🇺🇦 Українська", "🇬🇧 English"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def show_notif_menu(user_id, t):
    city = user_cities.get(user_id, "—")
    time = user_notif_time.get(user_id, "—")
    status = t["notif_on"] if user_notif_on.get(user_id) else t["notif_off"]
    text = t["notif_menu"].format(city, time, status)
    keyboard = ReplyKeyboardMarkup(t["notif_keyboard"], resize_keyboard=True)
    return text, keyboard


async def send_morning_weather(app, user_id):
    lang = get_lang(user_id)
    t = TEXTS[lang]
    city = user_cities.get(user_id)
    if not city:
        return
    data = get_weather(city, t["api_lang"])
    if data:
        msg = t["morning_msg"] + "\n\n" + format_weather_message(data, lang)
        try:
            await app.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send morning weather to {user_id}: {e}")


def schedule_notification(app, user_id, time_str):
    hour, minute = map(int, time_str.split(":"))
    job_id = f"morning_{user_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        send_morning_weather,
        CronTrigger(hour=hour, minute=minute),
        args=[app, user_id],
        id=job_id
    )


def remove_notification(user_id):
    job_id = f"morning_{user_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


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


async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = get_lang(user_id)
    t = TEXTS[lang]
    user_state[user_id] = "notif_menu"
    text, keyboard = show_notif_menu(user_id, t)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


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
        data = response.json()
        data["temp_min"] = data["main"]["temp_min"]
        data["temp_max"] = data["main"]["temp_max"]
        air = get_air_quality(location.latitude, location.longitude)
        if air:
            data["aqi"] = air["list"][0]["main"]["aqi"]
        await update.message.reply_text(format_weather_message(data, lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(t["location_error"])
        
CURRENCY_BUTTONS = ["💱 Курс валют", "💱 Exchange Rates"]
CURRENCY_URL = "https://api.exchangerate-api.com/v4/latest/EUR"
CURRENCIES = ["USD", "GBP", "UAH", "RUB", "PLN", "CHF", "JPY"]
CURRENCY_FLAGS = {
    "USD": "🇺🇸", "GBP": "🇬🇧", "UAH": "🇺🇦",
    "RUB": "🇷🇺", "PLN": "🇵🇱", "CHF": "🇨🇭", "JPY": "🇯🇵"
}
CRYPTO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"


def get_exchange_rates():
    try:
        response = requests.get(CURRENCY_URL, timeout=5)
        if response.status_code == 200:
            return response.json().get("rates", {})
    except Exception:
        pass
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = user_state.get(user_id, "choosing_city")
    app = context.application

    # ── Language selection ──────────────────────────────
    if text in LANG_BUTTONS:
        if text == "🇺🇦 Українська":
            user_languages[user_id] = "uk"
            lang = "uk"
        elif text == "🇬🇧 English":
            user_languages[user_id] = "en"
            lang = "en"
        else:
            user_languages[user_id] = "ru"
            lang = "ru"
        user_state[user_id] = "choosing_city"
        t = TEXTS[lang]
        reply_markup = ReplyKeyboardMarkup(t["keyboard"], resize_keyboard=True)
        await update.message.reply_text(t["lang_set"], parse_mode="Markdown", reply_markup=reply_markup)
        await update.message.reply_text(t["welcome"], parse_mode="Markdown")
        return

    if state == "choosing_lang":
        await update.message.reply_text(
            "🌐 Выбери язык / Оберіть мову / Choose language:",
            reply_markup=show_lang_keyboard()
        )
        return

    lang = get_lang(user_id)
    t = TEXTS[lang]

    # ── Switch language ─────────────────────────────────
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

    # ── Forecast button ─────────────────────────────────
    if text in FORECAST_BUTTONS:
        user_state[user_id] = "choosing_forecast_city"
        await update.message.reply_text(t["forecast_ask"], parse_mode="Markdown")
        return

    # ── Notifications menu ──────────────────────────────
    if text in NOTIF_BUTTONS:
        user_state[user_id] = "notif_menu"
        msg, keyboard = show_notif_menu(user_id, t)
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
        return

    # ── Back button ─────────────────────────────────────
    if text in BACK_BUTTONS:
        user_state[user_id] = "choosing_city"
        reply_markup = ReplyKeyboardMarkup(t["keyboard"], resize_keyboard=True)
        await update.message.reply_text(t["welcome"], parse_mode="Markdown", reply_markup=reply_markup)
        return

    # ── Notification sub-menu buttons ───────────────────
    if text in NOTIF_CITY_BUTTONS:
        user_state[user_id] = "notif_set_city"
        await update.message.reply_text(t["notif_set_city"], parse_mode="Markdown")
        return

    if text in NOTIF_TIME_BUTTONS:
        user_state[user_id] = "notif_set_time"
        await update.message.reply_text(t["notif_set_time"], parse_mode="Markdown")
        return

    if text in NOTIF_ENABLE_BUTTONS:
        city = user_cities.get(user_id)
        time_str = user_notif_time.get(user_id)
        if not city:
            await update.message.reply_text(t["notif_no_city"], parse_mode="Markdown")
            return
        if not time_str:
            user_state[user_id] = "notif_set_time"
            await update.message.reply_text(t["notif_set_time"], parse_mode="Markdown")
            return
        user_notif_on[user_id] = True
        schedule_notification(app, user_id, time_str)
        await update.message.reply_text(
            t["notif_enabled"].format(time_str, city),
            parse_mode="Markdown"
        )
        return

    if text in NOTIF_DISABLE_BUTTONS:
        user_notif_on[user_id] = False
        remove_notification(user_id)
        await update.message.reply_text(t["notif_disabled"], parse_mode="Markdown")
        return

    # ── Notification city input ─────────────────────────
    if state == "notif_set_city":
        weather_check = get_weather(text, t["api_lang"])
        if weather_check:
            user_cities[user_id] = text
            user_state[user_id] = "notif_menu"
            await update.message.reply_text(t["notif_city_saved"].format(text), parse_mode="Markdown")
            msg, keyboard = show_notif_menu(user_id, t)
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.message.reply_text(t["not_found"].format(text), parse_mode="Markdown")
        return

    # ── Notification time input ─────────────────────────
    if state == "notif_set_time":
        try:
            parts = text.strip().split(":")
            if len(parts) != 2:
                raise ValueError
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            time_str = f"{h:02d}:{m:02d}"
            user_notif_time[user_id] = time_str
            user_notif_on[user_id] = True
            schedule_notification(app, user_id, time_str)
            user_state[user_id] = "notif_menu"
            await update.message.reply_text(t["notif_time_saved"].format(time_str), parse_mode="Markdown")
            msg, keyboard = show_notif_menu(user_id, t)
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=keyboard)
        except ValueError:
            await update.message.reply_text(t["notif_time_invalid"], parse_mode="Markdown")
        return
        
    # ── Currency button ─────────────────────────────────
    if text in CURRENCY_BUTTONS:
        await update.message.reply_text(t["currency_loading"])
        rates = get_exchange_rates()
        if not rates:
            await update.message.reply_text(t["currency_error"])
            return
        msg = t["currency_title"] + "\n━━━━━━━━━━━━━━━━━━\n"
        msg += f"🇪🇺 1 EUR =\n\n"
        for code in CURRENCIES:
            if code in rates:
                flag = CURRENCY_FLAGS.get(code, "")
                rate = rates[code]
                if rate >= 100:
                    msg += f"{flag} {code}: *{rate:.2f}*\n"
                else:
                    msg += f"{flag} {code}: *{rate:.4f}*\n"
                    
    # Crypto rates
        try:
            crypto_resp = requests.get(CRYPTO_URL, timeout=5)
            if crypto_resp.status_code == 200:
                crypto = crypto_resp.json()
                btc = crypto["bitcoin"]["usd"]
                eth = crypto["ethereum"]["usd"]
                msg += f"\n₿ BTC: *${btc:,.0f} USDT*\n"
                msg += f"⟠ ETH: *${eth:,.0f} USDT*\n"
                msg += "━━━━━━━━━━━━━━━━━━"
        except Exception:
            pass
        await update.message.reply_text(msg, parse_mode="Markdown")
        return
    
    # ── City search or forecast ─────────────────────────
    await update.message.reply_text(t["searching"].format(text), parse_mode="Markdown")

    if user_state.get(user_id) == "choosing_forecast_city":
        user_state[user_id] = "choosing_city"
        forecast_data = get_forecast(text, t["api_lang"])
        if forecast_data:
            msg = format_forecast_message(forecast_data, lang, t)
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(t["not_found"].format(text), parse_mode="Markdown")
    else:
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
    app.add_handler(CommandHandler("notify", notify_command))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def post_init(application):
        scheduler.start()
        print("✅ Scheduler started!")

    app.post_init = post_init
    print("✅ Бот работает!")
    app.run_polling()


if __name__ == "__main__":
    main()
