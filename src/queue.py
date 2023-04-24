from typing import List, Union, Callable

import boto3
from injector import inject

from src.env import Environment


class Queue:
    def __init__(self, queue_url: str):
        self.__queue = boto3.resource('sqs').Queue(queue_url)

    def enqueue(self, messages: Union[str, List[str]]) -> None:
        if not isinstance(messages, list):
            messages = [messages]
        batch_size = 10
        batches = [messages[i:i + batch_size] for i in range(0, len(messages), batch_size)]
        for batch in batches:
            self.__queue.send_messages(Entries=[{'Id': str(i), 'MessageBody': x} for i, x in enumerate(batch)])

    def process(self, handle_message: Callable[[str], None]) -> None:
        while True:
            messages = self.__queue.receive_messages(MaxNumberOfMessages=10)
            if not messages:
                return
            for message in messages:
                try:
                    handle_message(message.body)
                finally:
                    message.delete()


class UnderlyingsQueue(Queue):
    @inject
    def __init__(self, env: Environment):
        super().__init__(env.underlyings_queue_url)
