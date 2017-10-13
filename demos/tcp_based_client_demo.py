'''
Created on Feb 15, 2016

@author: gavran
'''
import socket
import select
import logging

from xudd.actor import Actor
from xudd.hive import Hive
_log = logging.getLogger(__name__)
class Client(Actor):
    """TCP client

    Client can't do any processing on its own, it relies on another actor to
    take the data it receives.

    Once connected it will gather data and send chunks it receives to the
    other actor like this:

        self.send_message(
            to=self.chunk_handler,
            directive='handle_chunk',
            body={'chunk': b'some bytes'})

    """
    def __init__(self, hive, id, chunk_handler=None, poll_timeout=10):
        """Initialize the client

        - *chunk_handler*: ID of the actor that will be given data as we
        receive it through the socket. *Must* have a directive called
        'handle_chunk'
        - *poll_timeout*: number of milliseconds to wait for data before
        returning collected (if any) data
        """
        super(Client, self).__init__(hive, id)

        self.message_routing.update({
            'connect': self.connect,
            'send': self.send
        })

        self.poll_timout = poll_timeout
        self.chunk_handler = chunk_handler

    def connect(self, message):
        """Connect to a server

        The body of the message should be dict that contains the following keys:
        - *host*: domain name or IP address of server to connect to
        - *port*: port number to connect to

        It may also contain the following options:
        - *timeout*: the integer amount of time in seconds a connection will
        wait with no data before closing itself. Defaults to no timeout or the
        last value give to socket.setdefaulttimeout() (see Python docs)
        - *chunk_size*: size of the receive buffer, idealy a smaller power of 2.
        Defaults to 1024
        """
        try:
            host = message.body['host']
            port = message.body['port']
        except KeyError:
            raise ValueError('{klass}.connect must be called with `host` and\
                             `port` arguments in the message body'.format(
                             self.__class__.__name__))

        # Options
        timeout = message.body.get('timeout', socket.getdefaulttimeout())
        chunk_size = message.body.get('chunk_size', 1024)

        self.socket = socket.create_connection((host, port), timeout)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much
        # M says: docs aren't clear on a non-zero timeout + the above

        READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP \
            | select.POLLERR

        poller = select.poll()
        poller.register(self.socket, READ_ONLY)

        socket_from_fd = {
            self.socket.fileno(): self.socket
        }

        _log.info('Connected to {host}:{port}'.format(host=host, port=port))
        message_text = ""
        while True:
            events = poller.poll(self.poll_timout)

            for fd, flag in events:
                sock = socket_from_fd[fd]

                if flag & (select.POLLIN | select.POLLPRI):
                    
                    if sock is self.socket:
                        chunk = self.socket.recv(chunk_size)

                        if chunk in ['', b'']:
                            self.send_message(
                                to=self.chunk_handler,
                                directive='handle_chunk',
                                body={'chunk': chunk}
                                )
                            message_text = ""


                        message_text += chunk.decode()

            yield self.wait_on_self()

    def send(self, message):
        """Send

        Does what it says on the tin.
        """
        out = message.body['message']
        print("sending message: ")
        print(out)
        length = len(out)
        total_sent = 0
        while total_sent < length:
            sent = self.socket.send(out[total_sent:].encode())

            if sent == 0:
                raise RuntimeError('socket connection broken')

            total_sent += sent

class WebSocketHandler(Actor):
    def __init__(self, hive, id):
        super(WebSocketHandler, self).__init__(hive, id)
        self.message_routing.update({
            'handle_incoming_message': self.handle_incoming_message
        })

    def handle_incoming_message(self, message):
        _log.debug("handling message...")
        _log.debug(message.body)

class Overseer(Actor):
    """
    Actor that initializes the world of this demo and starts the mission.
    """
    def __init__(self, hive, id):
        super(Overseer, self).__init__(hive, id)

        self.message_routing.update(
            {"init_world": self.init_world})

    def init_world(self, message):
        """
        Initialize the world we're operating in for this demo.
        """
        handler = hive.create_actor(WebSocketHandler, id="handler")
        client = hive.create_actor(Client, id="client", chunk_handler=handler)
        yield self.wait_on_message(to=client, directive="connect", body={"host":'127.0.0.1', "port":8000})
        for i in range(10):
            self.send_message(to=client, directive="send", body={"message":"Message number "+str(i)})
        
if __name__ == '__main__':
    # create basic Hive
    hive = Hive()
    overseer_id = hive.create_actor(Overseer)
    hive.send_message(to=overseer_id, directive="init_world")
    
    
    
    hive.run()
    