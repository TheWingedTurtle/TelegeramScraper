import asyncio
from configparser import ConfigParser

import aio_pika
import aio_pika.abc

cp = ConfigParser()
cp.read('config.ini')


async def main(loop):
    # Connect with the givien parameters is also valiable.
    # aio_pika.connect_robust(host="host", login="login", password="password")
    # You can only choose one option to create a connection, url or kw-based params.
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@127.0.0.1/", loop=loop, timeout=60
    )

    async with connection:
        queue_name = cp['RabbitMQ']['queue_name']

        # Creating channel
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue = await channel.declare_queue(queue_name, auto_delete=True)
        await queue.consume(callback=println)


def println(message: aio_pika.abc.AbstractIncomingMessage):
    print(message.body.decode())


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
