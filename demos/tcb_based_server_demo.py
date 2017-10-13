'''
Created on Feb 15, 2016

@author: gavran
'''
from __future__ import print_function

import sys
import logging
import select
import socket
import traceback
import pdb

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from tornado import httputil, escape

try:
    from io import BytesIO # python 3
except ImportError:
    from cStringIO import StringIO as BytesIO # python 2

from xudd.actor import Actor
from xudd.hive import Hive
from xudd.tools import join_id

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)


class Server(Actor):
    def __init__(self, hive, id):
        super(Server, self).__init__(hive, id)
        self.message_routing.update({
            'respond': self.respond,
            'listen': self.listen
        })
        self.requests = {}
        hive.create_actor(WebSocketHandler, id="http")
 
    def listen(self, message):
        _log.debug("in listen")
        print("in listen")
        body = message.body
        port = body.get('port', 8000)
        host = body.get('host', '127.0.0.1')
 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(0)  # XXX: Don't know if this helps much
        self.socket.bind((host, port))
        self.socket.listen(5)  # Max 5 connections in queue
 
        while True:
            readable, writable, errored = select.select(
                [self.socket],
                [],
                [],
                .0000001)  # XXX: This will surely make it fast! (?)
 
            if readable:
                _log.info('Got new request ({0} in local index)'.format(len(self.requests)))
                print('Got new request ({0} in local index)'.format(len(self.requests)))
                req = self.socket.accept()
 
                # Use the message id as the internal id for the request
                message_id = self.send_message(
                    to=join_id('http', self.hive.hive_id),
                    directive='handle_request',
                    body={
                        'request': req
                    }
                )
 
                _log.debug('Sent request to worker')
 
                self.requests.update({
                    message_id: req
                })
 
            yield self.wait_on_self()
 
    def respond(self, message):
        _log.debug('Responding')
 
        sock, bind = self.requests.get(message.in_reply_to)
        sock.sendall(message.body['response'])
        sock.close()
        del self.requests[message.in_reply_to]
        _log.info('Responded')
        
class WebSocketHandler(Actor):
    def __init__(self, hive, id):
        super(WebSocketHandler, self).__init__(hive, id)
        self.message_routing.update({
            'handle_request': self.handle_request
        })

    def handle_request(self, message):
        _log.debug("handling message...")
        _log.debug(message.body['request'])
        request = message.body['request']
        socket = request[0]
        message = ""
        while True:
            data = socket.recv(2048)
            message += data.decode()
            if not data: 
                break
        _log.debug(message)
            
        




if __name__ == '__main__':
    hive = Hive()
    server_id = hive.create_actor(Server)
    hive.send_message(to=server_id, directive="listen")
    hive.run()