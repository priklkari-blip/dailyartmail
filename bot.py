import os
import asyncio
import logging
from datetime import datetime
import pytz
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8844820302:AAFS6_28kldGAb3FUKWK-zs-9OhjkiNxm8A")
CHAT_ID = os.environ.get("CHAT_ID", "195474826")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

# Список художников — каждый день новый, по порядку
ARTISTS = [
    "Иван Айвазовский",
    "Винсент ван Гог",
    "Леонардо да Винчи",
    "Клод Моне",
    "Сальвадор Дали",
    "Фрида Кало",
    "Пабло Пикассо",
    "Рембрандт ван Рейн",
    "Иероним Босх",
    "Густав Климт",
    "Эдвард Мунк",
    "Казимир Малевич",
    "Илья Репин",
    "Михаил Врубель",
    "Василий Кандинский",
    "Поль Гоген",
    "Анри Матисс",
    "Ян Вермер",
    "Питер Брейгель Старший",
    "Франсиско Гойя",
    "Эдгар Дега",
    "Пьер Огюст Ренуар",
    "Джорджо де Кирико",
    "Марк Шагал",
    "Василий Суриков",
    "Исаак Левитан",
    "Валентин Серов",
    "Андрей Рублёв",
    "Рафаэль Санти",
    "Микеланджело Буонарроти",
]


def get_artist_of_the_day() -> str:
    """Выбирает художника по номеру дня года."""
    day_of_year = datetime.now(MOSCOW_TZ).timetuple().tm_yday
    index = (day_of_year - 1) % len(ARTISTS)
    return ARTISTS[index]


async def generate_digest(artist: str) -> dict:
    """Запрашивает у Claude сводку по художнику в JSON."""
    prompt = f"""Ты — автор ежедневного арт-дайджеста. Напиши сводку про художника: {artist}

Верни ТОЛЬКО валидный JSON без markdown-обёртки, строго в этом формате:
{{
  "name": "Полное имя",
  "years": "1817–1900",
  "country": "Россия / Армения",
  "genre": "маринист",
  "count": "~6000 картин",
  "quote": "Цитата самого художника о творчестве или жизни (реальная)",
  "why_theme": {{
    "title": "Короткий заголовок (5-7 слов)",
    "body": "2-3 предложения о том, почему он рисовал именно это и что вкладывал"
  }},
  "technique": {{
    "title": "Короткий заголовок про технику",
    "body": "2-3 предложения про уникальный приём или метод работы"
  }},
  "paintings": [
    {{
      "name": "Название картины, год",
      "fact": "1-2 предложения — нетривиальный факт именно об этой картине"
    }},
    {{
      "name": "Название картины, год",
      "fact": "1-2 предложения"
    }},
    {{
      "name": "Название картины, год",
      "fact": "1-2 предложения"
    }}
  ],
  "personality": {{
    "title": "Заголовок про личность",
    "body": "3-4 предложения — характер, происхождение, неочевидные черты личности"
  }},
  "love_life": {{
    "title": "Заголовок про личную жизнь",
    "body": "2-3 предложения — что-то человеческое и интересное, как это повлияло на творчество"
  }},
  "quotes": [
    {{
      "text": "Цитата о художнике",
      "author": "Имя и кто это"
    }},
    {{
      "text": "Вторая цитата",
      "author": "Имя и кто это"
    }}
  ],
  "insights": [
    {{
      "label": "О работе",
      "text": "Глубокий неочевидный вывод — не банальный, реально применимый"
    }},
    {{
      "label": "О теме",
      "text": "Инсайт про специализацию или подход"
    }},
    {{
      "label": "О деньгах и смысле",
      "text": "Инсайт про деньги, репутацию или наследие"
    }}
  ],
  "links": [
    {{
      "lang": "RU",
      "title": "Название статьи",
      "source": "Название сайта",
      "url": "https://...",
      "minutes": 10
    }},
    {{
      "lang": "RU",
      "title": "Название статьи",
      "source": "Название сайта",
      "url": "https://...",
      "minutes": 8
    }},
    {{
      "lang": "EN",
      "title": "Article title",
      "source": "Site name",
      "url": "https://...",
      "minutes": 12
    }}
  ]
}}

Важно:
- Все факты должны быть реальными и точными
- Инсайты — глубокие, не банальные, применимые и подросткам и предпринимателям
- Ссылки — только реально существующие качественные источники
- Цитаты — только реальные, с указанием кто это сказал"""

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        data = response.json()
        text = data["content"][0]["text"].strip()

        # Убираем возможные markdown-обёртки
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        import json
        return json.loads(text)


def format_telegram_message(d: dict, artist: str) -> str:
    """Форматирует JSON-сводку в красивое Telegram-сообщение."""
    day = datetime.now(MOSCOW_TZ).timetuple().tm_yday

    lines = []

    # Шапка
    lines.append(f"🎨 *Художник дня · выпуск \\#{day}*")
    lines.append("")
    lines.append(f"*{escape(d['name'])}*")
    lines.append(f"_{escape(d['years'])} · {escape(d['country'])} · {escape(d['genre'])} · {escape(d['count'])}_")
    lines.append("")
    lines.append(f"_{escape(d['quote'])}_")

    # Почему эта тема
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🌊 *{escape(d['why_theme']['title'])}*")
    lines.append(escape(d['why_theme']['body']))

    # Техника
    lines.append("")
    lines.append(f"⚡ *{escape(d['technique']['title'])}*")
    lines.append(escape(d['technique']['body']))

    # Картины
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("🖼 *Топ картин*")
    for p in d['paintings']:
        lines.append(f"\n*{escape(p['name'])}*")
        lines.append(escape(p['fact']))

    # Личность
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🧬 *{escape(d['personality']['title'])}*")
    lines.append(escape(d['personality']['body']))

    # Личная жизнь
    lines.append("")
    lines.append(f"💍 *{escape(d['love_life']['title'])}*")
    lines.append(escape(d['love_life']['body']))

    # Цитаты современников
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("💬 *Что говорили современники*")
    for q in d['quotes']:
        lines.append(f"\n_{escape(q['text'])}_")
        lines.append(f"— {escape(q['author'])}")

    # Инсайты
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 *Инсайты*")
    for ins in d['insights']:
        lines.append(f"\n*{escape(ins['label'])}*")
        lines.append(escape(ins['text']))

    # Ссылки
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("📚 *Читать подробнее*")
    for lnk in d['links']:
        flag = "🇷🇺" if lnk['lang'] == "RU" else "🇬🇧"
        lines.append(f"\n{flag} [{escape(lnk['title'])}]({lnk['url']})")
        lines.append(f"_{escape(lnk['source'])} · ⏱ {lnk['minutes']} мин_")

    return "\n".join(lines)


def escape(text: str) -> str:
    """Экранирует спецсимволы для Telegram MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


async def send_daily_digest():
    """Основная функция отправки дайджеста."""
    artist = get_artist_of_the_day()
    logger.info(f"Отправляю дайджест про: {artist}")

    bot = Bot(token=BOT_TOKEN)

    try:
        # Генерируем контент
        digest = await generate_digest(artist)
        message = format_telegram_message(digest, artist)

        # Отправляем текст
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        logger.info("Дайджест отправлен успешно")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        # Отправляем простое сообщение об ошибке
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"⚠️ Не удалось сгенерировать дайджест про {artist}. Попробую завтра.",
        )


async def main():
    logger.info("Бот запущен")

    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(
        send_daily_digest,
        trigger="cron",
        hour=20,
        minute=10,
    )
    scheduler.start()
    logger.info("Расписание установлено: 20:10 по Москве")

    # Держим процесс живым
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
