import logging
import os
import sys
import time
from functools import lru_cache
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import apihelper, TeleBot

from exceptions import UnavailableEndpointError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

format = '%(asctime)s %(levelname)s %(message)s'
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(format))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens():
    """Проверка доступности переменных окружения."""
    env_vars = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    absent_env_vars = [key for key, var in env_vars.items() if var is None]
    if absent_env_vars:
        message = ('Отсутствуют следующие обязательные переменные окружения: '
                   f'"{', '.join(absent_env_vars)}".\n'
                   'Программа принудительно остановлена.')
        logger.critical(message)
        raise ValueError(message)


@lru_cache(maxsize=1)
def send_message(bot, message):
    """Отправляет сообщение в соответствующий Telegram-чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.debug(f'Бот отправил сообщение: "{message}".')


def get_api_answer(timestamp):
    """Запрос к API-сервису."""
    params = {'from_date': timestamp}
    logger.debug(f'Отправка запроса по адресу {ENDPOINT} '
                 f'с параметром from_date = {timestamp}.')
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    except requests.RequestException as error:
        raise UnavailableEndpointError(error)
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        raise UnavailableEndpointError(
            (f'Ошибка при запросе к эндпойнту {ENDPOINT}. '
             f'Код ответа API: {status_code}.')
        )
    return response.json()


def check_response(response):
    """Проверка корректности ответа API-сервиса."""
    if not isinstance(response, dict):
        raise TypeError('Получен некорректный тип данных '
                        f'{type(response)} в ответе API.')
    elif 'homeworks' not in response:
        raise ValueError('Отсутствует ключ "homeworks" в ответе API.')
    elif not isinstance(response['homeworks'], list):
        raise TypeError(
            (f'Некорректный тип данных {type(response['homeworks'])} '
             'под ключом "homeworks" в ответе API.')
        )


def parse_status(homework):
    """Возвращает информацию об изменении статуса проверки домашней работы."""
    absent_keys = [f'"{key}"' for key in ('homework_name', 'status')
                   if key not in homework]
    if absent_keys:
        raise KeyError(
            ('В ответе API в словаре "homework" отсутствуют следующие ключи: '
             f'{', '.join(absent_keys)}.')
        )
    homework_name = homework['homework_name']
    status = homework['status']
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        raise ValueError(f'Неожиданный статус проверки {status} в ответе API.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            message = parse_status(homeworks[0]) if homeworks else None
            if not message:
                logger.debug('Статус проверки домашней работы не изменился.')
                continue
            send_message(bot, message)
            timestamp = response.get('current_date', timestamp)
        except (apihelper.ApiException, requests.exceptions.RequestException):
            logger.exception('Сбой при отправке сообщения в Telegram.')
        except Exception as error:
            message = f'Сбой в работе программы. {error}'
            logger.exception(message)
            try:
                send_message(bot, message)
            except (apihelper.ApiException,
                    requests.exceptions.RequestException):
                logger.exception('Сбой при отправке сообщения в Telegram.')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
