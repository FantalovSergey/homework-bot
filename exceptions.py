class UnavailableEndpointError(Exception):
    """Исключение при неудачной попытке подключения к эндпойнту."""

    def __init__(self, message=None, endpoint=None):
        """
        Укажите эндпойнт или сообщение об ошибке.
        Допускается создание экземпляра класса без аргументов.
        """
        self.endpoint = endpoint
        if message:
            self.message = message
        elif endpoint:
            self.message = f'Эндпойнт {endpoint} недоступен.'
        else:
            self.message = 'Запрашиваемый эндпойнт недоступен.'
        super().__init__(self.message)


class DateError(Exception):
    """Исключение при некорректном формате даты в запросе к API."""

    def __init__(self, message=('Указан некорректный формат '
                                'даты в запросе к API.')):
        """Исключение при некорректном формате даты в запросе к API."""
        self.message = message
        super().__init__(self.message)


class WrongTokenError(Exception):
    """Исключение при отправке недействительного токена в запросе к API."""

    def __init__(self, message=('Некорректные учётные данные '
                                'при запросе к API.')):
        """Исключение при отправке недействительного токена в запросе к API."""
        self.message = message
        super().__init__(self.message)


class StatusError(Exception):
    """Исключение при некорректном статусе проверки в ответе API."""

    def __init__(self, message='Неожиданный статус проверки в ответе API.'):
        """Исключение при некорректном статусе проверки в ответе API."""
        self.message = message
        super().__init__(self.message)
