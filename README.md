# 🎨 DailyArtBot

Телеграм-бот, который каждый день в 11:11 по Москве присылает сводку про художника.

## Деплой на Railway (бесплатно, ~10 минут)

### 1. Получи Anthropic API ключ
- Зайди на https://console.anthropic.com
- Создай аккаунт и перейди в API Keys
- Нажми "Create Key" и скопируй ключ

### 2. Загрузи код на GitHub
- Зайди на https://github.com и создай новый репозиторий (например `dailyartbot`)
- Загрузи три файла: `bot.py`, `requirements.txt`, `Procfile`

### 3. Задеплой на Railway
- Зайди на https://railway.app
- Войди через GitHub
- Нажми "New Project" → "Deploy from GitHub repo"
- Выбери свой репозиторий

### 4. Добавь переменные окружения
В Railway перейди в Settings → Variables и добавь:
```
BOT_TOKEN=8844820302:AAFS6_28kldGAb3FUKWK-zs-9OhjkiNxm8A
CHAT_ID=195474826
ANTHROPIC_API_KEY=твой_ключ_от_anthropic
```

### 5. Готово!
Railway автоматически запустит бота. Завтра в 11:11 придёт первое сообщение.

## Проверить что бот работает
Можно временно изменить время в bot.py:
```python
hour=11, minute=11  # поменяй на текущее время + 2 минуты
```

## Список художников
30 художников в файле bot.py в переменной ARTISTS. 
Можно добавить любых других.
