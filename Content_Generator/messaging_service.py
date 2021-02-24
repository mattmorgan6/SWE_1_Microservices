import threading
import pika
import sys
import os
import time
import json

# NOTE: Code from this file is shared by each group member. 
# I recieved approval for it over email on 2/19. -Matthew Morgan

recv_data = None

def get_recv_data():
    """
    Returns the global variable recv_data
    """
    return recv_data
    
def clr_recv_data():
    """
    Sets the global variable recv_data to None to clear it. 
    """
    recv_data = None
    return recv_data

class Sender(threading.Thread):
    def run(self):
        """
        Create a thread to send messages on.
        """
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self._channel = self._connection.channel()
        self._channel.queue_declare(queue='channel_2')

    def send(self):
        """
        Send a message over RabbitMQ. Setup RabbitMQ.
        """
        self._channel.basic_publish(
            exchange='', routing_key='channel_2', body='Hello World!')
        print(" [x] Sent 'Hello World !'")

    def stop(self):
        """
        Close the sender connection for RabbitMQ.
        """
        self._connection.close()

class Reciever(threading.Thread):
    def run(self):
        """
        Create a thread to recieve messages on. Setup RabbitMQ.
        """
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self._channel = connection.channel()

        self._channel.queue_declare(queue='channel_1')

        def callback(ch, method, properties, body):
            global recv_data
            print(" [x] Received %r in channel_1" % body)
            # ContentGenerator.insertText(body)
            results = json.loads(body)
            recv_data = results["name"].split(' ')
            

        self._channel.basic_consume(
            queue='channel_1', on_message_callback=callback, auto_ack=True)

        print('READY. To send "hello world" as a message, type "send". To exit type "exit".')
        self._channel.start_consuming()

    def stop(self):
        """
        Stop recieving messages from RabbitMQ. Ends the thread.
        """
        print("Exiting, please wait one moment.")
        self._channel.stop_consuming()


class Messenger():

    def __init__(self):
        """
        Starts the Sender and Reciever objects as threads.
        Once complete, RabbitMQ is ready.
        """
        self._reciever = Reciever()
        self._sender = Sender()
        self._reciever.start()
        self._sender.start()

    def send(self):
        self._sender.send()
    
    def end_threads(self):
        self._sender.stop()
        self._reciever.stop()
        

def main():
    """
    Use for testing out this Messenger class interface.
    """

    messager = Messenger()

    while True:
        time.sleep(0.6) # For testing: use so the processing threads have time to print
        line = input()
        if line == "exit":
            messager.end_threads()
            break

        if line == "send":
            messager.send()
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
