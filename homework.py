import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (DateError, StatusError, UnavailableEndpointError,
                        WrongTokenError)

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
    for key, var in env_vars.items():
        if var is None:
            message = (
                f'Отсутствует обязательная переменная окружения: "{key}".\n'
                f'Программа принудительно остановлена.'
            )
            logger.critical(message)
            sys.exit(message)


def send_message(bot, message):
    """Отправляет сообщение в соответствующий Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: "{message}".')
    except Exception:
        logger.error('Сбой при отправке сообщения в Telegram.')


def get_api_answer(timestamp):
    """Запрос к API-сервису."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            raise UnavailableEndpointError(endpoint=ENDPOINT)
    except Exception:
        raise UnavailableEndpointError(endpoint=ENDPOINT)


def check_response(response):
    """
    Проверка корректности ответа API-сервиса.
    Ответ сервиса при отправки некорректных данных в параметре from_date:
    {
        'code': 'UnknownError',
        'error': {'error': 'Wrong from_date format'}
    }.
    Ответ сервиса при запросе с недействительным токеном:
    {
        'code': 'not_authenticated',
        'message': 'Учетные данные не были предоставлены.',
        'source': '__response__'
    }.
    """
    if not isinstance(response, dict):
        raise TypeError('Получен некорректный тип данных в ответе API.')
    elif 'error' in response:
        raise DateError
    elif 'message' in response:
        raise WrongTokenError
    elif 'homeworks' not in response:
        raise KeyError('Отсутствуют ожидаемые ключи в ответе API.')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Некорректный тип данных '
                        'под ключом "homeworks" в ответе API.')


def parse_status(homework):
    """Возвращает информацию об изменении статуса проверки домашней работы."""
    if homework:
        try:
            homework_name = homework['homework_name']
        except KeyError:
            raise KeyError('Отсутствует ключ "homework_name" в ответе API.')
        try:
            verdict = HOMEWORK_VERDICTS[homework['status']]
        except KeyError:
            raise StatusError
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks']:
                send_message(bot, parse_status(response['homeworks'][0]))
            else:
                logger.debug('Статус проверки домашней работы не изменился.')
        except Exception as error:
            message = f'Сбой в работе программы. {error}'
            logger.error(message)
            if message != last_error_message:
                send_message(bot, message)
                last_error_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
