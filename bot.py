import os
import asyncio
import logging
import json
from datetime import datetime
import pytz
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

ARTISTS = [
    {"name": "Иероним Босх", "years": "1450–1516", "era": "Северное Возрождение"},
    {"name": "Питер Брейгель Старший", "years": "1525–1569", "era": "Северное Возрождение"},
    {"name": "Рембрандт ван Рейн", "years": "1606–1669", "era": "Золотой век Голландии"},
    {"name": "Ян Вермер", "years": "1632–1675", "era": "Золотой век Голландии"},
    {"name": "Франсиско Гойя", "years": "1746–1828", "era": "Романтизм"},
    {"name": "Иван Айвазовский", "years": "1817–1900", "era": "Романтизм / Реализм"},
    {"name": "Илья Репин", "years": "1844–1930", "era": "Передвижники"},
    {"name": "Клод Моне", "years": "1840–1926", "era": "Импрессионизм"},
    {"name": "Михаил Врубель", "years": "1856–1910", "era": "Символизм / Модерн"},
    {"name": "Густав Климт", "years": "1862–1918", "era": "Венский сецессион"},
    {"name": "Эдвард Мунк", "years": "1863–1944", "era": "Экспрессионизм"},
    {"name": "Василий Кандинский", "years": "1866–1944", "era": "Абстракционизм"},
    {"name": "Пауль Клее", "years": "1879–1940", "era": "Баухаус"},
    {"name": "Казимир Малевич", "years": "1879–1935", "era": "Супрематизм"},
    {"name": "Рене Магритт", "years": "1898–1967", "era": "Сюрреализм"},
    {"name": "Марк Ротко", "years": "1903–1970", "era": "Абстрактный экспрессионизм"},
    {"name": "Фрида Кало", "years": "1907–1954", "era": "Автобиографизм"},
    {"name": "Фрэнсис Бэкон", "years": "1909–1992", "era": "Фигуративный экспрессионизм"},
    {"name": "Луиз Буржуа", "years": "1911–2010", "era": "Феминизм / Психоанализ в скульптуре"},
    {"name": "Эндрю Уайет", "years": "1917–2009", "era": "Магический реализм"},
    {"name": "Сай Твомбли", "years": "1928–2011", "era": "Абстрактный экспрессионизм / Живопись действия"},
    {"name": "Яёи Кусама", "years": "1929–н.в.", "era": "Психоделический поп-арт / Инсталляция"},
    {"name": "Герхард Рихтер", "years": "1932–н.в.", "era": "Фотореализм / Абстракция"},
    {"name": "Йоко Оно", "years": "1933–н.в.", "era": "Флюксус / Концептуализм"},
    {"name": "Илья Кабаков", "years": "1933–2023", "era": "Московский концептуализм"},
    {"name": "Синди Шерман", "years": "1954–н.в.", "era": "Феминизм / Концептуальная фотография"},
    {"name": "Марина Абрамович", "years": "1946–н.в.", "era": "Перформанс"},
    {"name": "Айвейвэй", "years": "1957–н.в.", "era": "Политический концептуализм"},
    {"name": "Кит Харинг", "years": "1958–1990", "era": "Стрит-арт / Поп-арт"},
    {"name": "Жан-Мишель Баския", "years": "1960–1988", "era": "Нео-экспрессионизм"},
    {"name": "Такаси Мураками", "years": "1962–н.в.", "era": "Суперфлэт"},
    {"name": "Джефф Кунс", "years": "1955–н.в.", "era": "Нео-поп / Китч как искусство"},
    {"name": "Дэмиен Херст", "years": "1965–н.в.", "era": "Молодые британские художники (YBA)"},
    {"name": "Вольфганг Тильманс", "years": "1968–н.в.", "era": "Концептуальная фотография"},
    {"name": "Бэнкси", "years": "1974?–н.в.", "era": "Стрит-арт / Политическое искусство"},
]


def get_artist_of_the_day() -> dict:
    day_of_year = datetime.now(MOSCOW_TZ).timetuple().tm_yday
    index = (day_of_year - 1) % len(ARTISTS)
    return ARTISTS[index]


async def generate_digest(artist: dict) -> dict:
    prompt = f"""Ты — автор ежедневного арт-дайджеста для широкой аудитории — от подростков до предпринимателей.

Художник: {artist['name']} ({artist['years']})
Эпоха: {artist['era']}

Верни ТОЛЬКО валидный JSON без markdown-обёртки, строго в этом формате:
{{
  "name": "Полное имя",
  "years": "{artist['years']}",
  "country": "Страна",
  "genre": "Жанр коротко",
  "era_title": "{artist['era']}",
  "era_context": "2-3 предложения про эпоху",
  "quote": "Реальная цитата художника",
  "why_theme": {{"title": "Заголовок", "body": "2-3 предложения"}},
  "technique": {{"title": "Заголовок", "body": "2-3 предложения"}},
  "paintings": [
    {{"name": "Название, год", "fact": "Факт"}},
    {{"name": "Название, год", "fact": "Факт"}},
    {{"name": "Название, год", "fact": "Факт"}}
  ],
  "personality": {{"title": "Заголовок", "body": "3-4 предложения"}},
  "love_life": {{"title": "Заголовок", "body": "2-3 предложения"}},
  "quotes": [
    {{"text": "Цитата", "author": "Имя и кто это"}},
    {{"text": "Цитата", "author": "Имя и кто это"}}
  ],
  "insights": [
    {{"label": "О работе", "text": "Глубокий инсайт"}},
    {{"label": "О теме", "text": "Инсайт"}},
    {{"label": "О деньгах и репутации", "text": "Инсайт"}}
  ],
  "links": [
    {{"lang": "RU", "title": "Название", "source": "Сайт", "url": "https://...", "minutes": 10}},
    {{"lang": "RU", "title": "Название", "source": "Сайт", "url": "https://...", "minutes": 8}},
    {{"lang": "EN", "title": "Title", "source": "Site", "url": "https://...", "minutes": 12}}
  ]
}}

Только реальные факты. Только реальные ссылки. Инсайты — глубокие, не банальные."""

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

        data = response.json()
        logger.info(f"API status: {response.status_code}")
        logger.info(f"API response keys: {list(data.keys())}")

        if "error" in data:
            raise Exception(f"API error: {data['error']}")

        if "content" not in data:
            raise Exception(f"No content in response: {json.dumps(data)[:500]}")

        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        return json.loads(text)


def escape(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


def format_telegram_message(d: dict) -> str:
    day = datetime.now(MOSCOW_TZ).timetuple().tm_yday
    lines = []

    lines.append(f"🎨 *Художник дня · выпуск \\#{day}*")
    lines.append("")
    lines.append(f"*{escape(d['name'])}*")
    lines.append(f"_{escape(d['years'])} · {escape(d['country'])} · {escape(d['genre'])}_")
    lines.append("")
    lines.append(f"_{escape(d['quote'])}_")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕰 *Эпоха: {escape(d['era_title'])}*")
    lines.append(escape(d['era_context']))

    lines.append("")
    lines.append(f"🌊 *{escape(d['why_theme']['title'])}*")
    lines.append(escape(d['why_theme']['body']))

    lines.append("")
    lines.append(f"⚡ *{escape(d['technique']['title'])}*")
    lines.append(escape(d['technique']['body']))

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("🖼 *Ключевые работы*")
    for p in d['paintings']:
        lines.append(f"\n*{escape(p['name'])}*")
        lines.append(escape(p['fact']))

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🧬 *{escape(d['personality']['title'])}*")
    lines.append(escape(d['personality']['body']))

    lines.append("")
    lines.append(f"💍 *{escape(d['love_life']['title'])}*")
    lines.append(escape(d['love_life']['body']))

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("💬 *Что говорили современники*")
    for q in d['quotes']:
        lines.append(f"\n_{escape(q['text'])}_")
        lines.append(f"— {escape(q['author'])}")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 *Инсайты*")
    for ins in d['insights']:
        lines.append(f"\n*{escape(ins['label'])}*")
        lines.append(escape(ins['text']))

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("📚 *Читать подробнее*")
    for lnk in d['links']:
        flag = "🇷🇺" if lnk['lang'] == "RU" else "🇬🇧"
        lines.append(f"\n{flag} [{escape(lnk['title'])}]({lnk['url']})")
        lines.append(f"_{escape(lnk['source'])} · ⏱ {lnk['minutes']} мин_")

    return "\n".join(lines)


async def send_daily_digest():
    artist = get_artist_of_the_day()
    logger.info(f"Отправляю дайджест про: {artist['name']}")
    bot = Bot(token=BOT_TOKEN)
    try:
        digest = await generate_digest(artist)
        message = format_telegram_message(digest)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        logger.info("Дайджест отправлен успешно")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка: {error_msg}")
        try:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"⚠️ Ошибка для {artist['name']}:\n\n{error_msg[:1000]}",
            )
        except Exception as e2:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e2}")


async def main():
    logger.info("Бот запущен")
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        send_daily_digest,
        trigger="cron",
        hour=19,
        minute=55,
    )
    scheduler.start()
    logger.info("Расписание установлено: 19:55 по Москве")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
