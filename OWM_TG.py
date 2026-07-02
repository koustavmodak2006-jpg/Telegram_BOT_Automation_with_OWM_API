import requests
import os
from datetime import datetime
from urllib.parse import unquote
from google import genai
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

parameters = {
    "lat": 24.618538,
    "lon": 72.766403,
    "appid": os.getenv("OWM_KEY"),
    "units": "metric",
    "cnt": 5,
}

response = requests.get(
    "https://api.openweathermap.org/data/2.5/forecast",
    params=parameters
)
response.raise_for_status()
data = response.json()

zenquote = requests.get(os.getenv("ZENQUOTE_API"))
zenquote.raise_for_status()
quote = zenquote.json()

trivia = requests.get(os.getenv("OPENTRIVIA_API"))
trivia.raise_for_status()
quiz = trivia.json()
answers = ""

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not found.")

client = genai.Client(api_key=api_key)

city = data.get("city", {}).get("name", "Your Location")
today = datetime.now().strftime("%A, %d %b %Y")

sunrise = datetime.fromtimestamp(data['city']['sunrise'],ZoneInfo("Asia/Kolkata")).strftime("%I:%M %p")
sunset = datetime.fromtimestamp(data['city']['sunset'],ZoneInfo("Asia/Kolkata")).strftime("%I:%M %p")
# ---------- Header ----------
text_message = (
    f"🌤 *WEATHER FORECAST*\n"
    f"📍 {city}   📅 {today}\n"
    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
)

# ---------- Forecast Table ----------
text_message += "```\n"
text_message += f"{'Time':<8}{'Temp':<8}{'Feels':<8}{'Hum':<6}\n"
text_message += f"{'-'*30}\n"

for forecast in data["list"]:
    dt = datetime.fromtimestamp(forecast["dt"]).strftime("%I %p")
    temp = round(forecast["main"]["temp"])
    feels = round(forecast["main"]["feels_like"])
    humidity = forecast["main"]["humidity"]

    text_message += (
        f"{dt:<8}{str(temp)+'°C':<8}"
        f"{str(feels)+'°C':<8}{str(humidity)+'%':<6}\n")
text_message += "```\n"

#---------------- SunRise & SunSet ----------------
text_message += "\n☀️ *SUN TIME-LINE*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
text_message += f"Sun-Rise = {sunrise}\nSun-Set = {sunset}\n"

# ---------- Weather Conditions ----------
text_message += "\n☁️ *CONDITIONS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

weather_icons = {
    "clear": "☀️", "cloud": "☁️", "rain": "🌧",
    "thunderstorm": "⛈", "snow": "❄️", "mist": "🌫", "haze": "🌫"
}

details_gemini = ""
for forecast in data["list"]:
    dt = datetime.fromtimestamp(forecast["dt"]).strftime("%I %p")
    weather_main = forecast["weather"][0]["main"].lower()
    weather_desc = forecast["weather"][0]["description"].title()
    details_gemini+=weather_desc

    icon = "🌡"
    for key, emoji in weather_icons.items():
        if key in weather_main:
            icon = emoji
            break

    text_message += f"{icon} `{dt}` → {weather_desc}\n"

gemini_response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"It's the weather details of Mount Abu for 12 hours, I want you to generate summary on the basis of it in only 50 words:-{details_gemini}",
)
text_message += (
    "\n*SUMMARY of Weather ..!*"
    "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"{gemini_response.text}\n")



text_message += (
    "\n*QUOTE of the Day..!*"
    "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"{quote[0]["q"]}\n"
    f"By - {quote[0]["a"]}\n"
)

text_message += (
    "\n10 *Quizzes for Today*..!!"
    "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)

for i in range(0,10):
        text_message+= f"{i+1}. {(unquote(quiz["results"][i]["question"]))}\n"
        answers += f"({i + 1}. {unquote(quiz["results"][i]["correct_answer"])}) -> "

text_message +=("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"*Answers*: {answers}")

# ---------- Footer ----------
text_message += (
    "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "\n💧 *Stay Hydrated*  ☀️ *Have a Great Day!*"
)

print(text_message)
# ---------- Telegram Send ----------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = 7614505023
# CHAT_ID = -1003949713233

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

payload = {
    "chat_id": CHAT_ID,
    "text": text_message,
    "parse_mode": "Markdown",
}

telegram_response = requests.post(url, data=payload)

if telegram_response.status_code == 200:
    print("✅ Message sent successfully!")
else:
    print("❌ Failed to send message.")
    print(telegram_response.text)
