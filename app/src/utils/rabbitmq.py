import pika

class Rabbit():

    channel = None
    connection = None
    queue_name = None

    def __init__(self) -> None:
        self.queue_name = 'pending_queries'

        connection_params = pika.ConnectionParameters(
            host='localhost',  # Замените на адрес вашего RabbitMQ сервера
            port=5672,          # Порт по умолчанию для RabbitMQ
            virtual_host='/',   # Виртуальный хост (обычно '/')
            credentials=pika.PlainCredentials(
                username='guest',  # Имя пользователя по умолчанию
                password='guest'   # Пароль по умолчанию
            )
        )

        # Установка соединения
        self.connection = pika.BlockingConnection(connection_params)

        # Создание канала
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name)  # Создание очереди (если не существует)

        # self.subscribe_to_queue(queue_name=self.queue_name)
    
    
    def put_message(self, queue_name, message = None):
        # Отправка сообщения
        print('start of put message')
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=message
        )

        print(f"Sent: '{message}'")

        # Закрытие соединения
        # self.connection.close()

        # Функция, которая будет вызвана при получении сообщения
    def callback(self, ch, method, properties, body):
        print(f"Received: '{body}'")

    def subscribe_to_queue(self, queue_name = None):
        # Подписка на очередь и установка обработчика сообщений
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.callback,
            auto_ack=True  # Автоматическое подтверждение обработки сообщений
        )

        print('Waiting for messages. To exit, press Ctrl+C')
        self.channel.start_consuming()
