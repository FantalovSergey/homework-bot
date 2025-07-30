# Описание
Telegram-бот, который каждые 10 минут обращается к API сервиса Практикум Домашка и узнаёт статус домашней работы: взята ли в ревью, проверена ли она, а если проверена — принял её ревьюер или вернул на доработку. При обновлении статуса бот анализирует ответ API и отправляет соответствующее уведомление в Telegram. Бот логирует свою работу и в случае возникновения проблем также отправляет сообщение в Telegram.

# Установка
Клонируйте репозиторий и перейдите в него в командной строке:

```
git clone https://github.com/FantalovSergey/homework-bot.git
```

```
cd homework-bot
```

Cоздайте и активируйте виртуальное окружение:

```
python3 -m venv venv
```

* Для Linux/macOS

    ```
    source venv/bin/activate
    ```

* Для Windows

    ```
    venv\Scripts\activate
    ```

Установите зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

# Стек
- Python 3.12.7
- pyTelegramBotAPI
- pytest

# Об авторе
Студент факультета Бэкенд платформы Яндекс.Практикум [Фанталов Сергей](https://github.com/FantalovSergey).
