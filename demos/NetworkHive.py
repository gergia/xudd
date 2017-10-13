from __future__ import print_function

import sys
import logging
import select
import socket
import traceback
import pdb
import asyncio
from time import sleep
import json

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
from xudd.tools import split_id
from xudd.hive import Hive
from xudd.tools import join_id
from collections import namedtuple
from xudd.message import Message

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)
Client = namedtuple('Client', 'reader writer')

class NetworkHive(Hive):
    def __init__(self, hive_id=None):
        super(NetworkHive, self).__init__(hive_id)
        self.message_routing.update({
            'connect': self.connect_and_communicate,
            'start_listening': self.listen})
        self._actor_registry[self.hive_id] = self
        self.known_distant_hives = {}
        self.loop = asyncio.get_event_loop()
        
    
    
#     def handle_hi(self, message):
#         print("received hi message")
#         print(message.directive)
#         print(message.body)
#     
#     def dummy_reply(self, message):
#         self.send_message(to=message.from_id, directive="hi")
    
    
    @asyncio.coroutine
    def listen(self, message):
        _log.debug("in listen")
#         self.listening_host = self.central_server_address
#         self.listening_port = self.central_server_port
        self.listening_host = message.body['host']
        self.listening_port = message.body['port']
        
        try:
            self.server = yield from asyncio.start_server(self.client_connected, self.listening_host, self.listening_port)
            _log.debug('Running server on {}:{}'.format(self.listening_host, self.listening_port))
        except OSError:
            _log.error('Cannot bind to this port! Is the server already running?')
    
    def _unpack_received_message(self, msg):
        msg = json.loads(msg.decode())
        received_message = Message.from_dict(msg)
        return received_message
    
    def _pack_message_to_send(self, msg):
        msg = json.dumps(msg.to_dict())
        msg = msg + '\n'
        msg = msg.encode()
        return msg
    
    def _register_client(self, client_id, writer):
        _, sender_hive_id = split_id(client_id)
        if sender_hive_id not in self.known_distant_hives:
            self.known_distant_hives[sender_hive_id] = writer
            
    
    @asyncio.coroutine
    def client_connected(self, reader, writer):
        _log.debug('Client connected.')
        
        while not reader.at_eof():
            try:
                msg = yield from reader.readline()
                if msg:
                    received_message = self._unpack_received_message(msg)
                    _log.debug('Server Received: "{}"'.format(received_message))
#                     pdb.set_trace()
                    self._register_client(received_message.from_id, writer)
                    self.send_message(to=received_message.to, directive=received_message.directive, from_id=received_message.from_id, body=received_message.body)
                    
            except ConnectionResetError as e:
                _log.error('ERROR: {}'.format(e))
                return

    
    @asyncio.coroutine
    def connect_and_communicate(self, message):
        _log.debug('Connecting...')
        try:
            host = message.body["host"]
            port = message.body["port"]
            distant_hive_id = message.body["distant_hive_id"]

            self.reader, self.writer = yield from asyncio.open_connection(host, port)
            self.send_message(to = message.from_id, directive="connected")
            #connected_hives_id
            self.known_distant_hives[distant_hive_id] = self.writer
            
            self.communicate(reader=self.reader, writer=self.writer)
            
            
        except ConnectionRefusedError as e:
            print('Connection refused: {}'.format(e))
            self.close()
    
    @asyncio.coroutine        
    def communicate(self, reader, writer):
        while not self.reader.at_eof():
            msg = yield from self.reader.readline()
            if msg:
                received_message=self._unpack_received_message(msg)
                self.send_message(to=received_message.to, directive=received_message.directive, from_id=received_message.from_id, body=received_message.body)
            _log.info('The server closed the connection, press <enter> to exit.')
    
    
    
    def _process_message(self, message):
        
     
        actor_id, hive_id = split_id(message.to)
#         if hive_id == "general":
#             pdb.set_trace()
        
        if hive_id==None and actor_id == self.hive_id:
            hive_id = actor_id
        
        
        ## Is the actor local?  Send it!
        if hive_id == self.hive_id:
            try:
                actor = self._actor_registry[actor_id]
            except IndexError:
                # For some reason this actor wasn't found, so we may need to
                # inform the original sender
                _log.warning('recipient not found for message: {0}'.format(
                    message))

                self.return_to_sender(message)

            # Maybe not the most opportune place to attach this
            message.hive_proxy = actor.hive

            # TODO: More error handling here! ;)
            actor.handle_message(message)

        ## Looks like the actor must be remote, forward it!
        else:
            
            if hive_id not in self.known_distant_hives:
                
                _log.critical("unknown hive")
                pdb.set_trace()
            else:
                self._send_distant_message(message)
            

    def _send_distant_message(self, msg):
        _, hive_id = split_id(msg.to)
        try:
            writer = self.known_distant_hives[hive_id]
        except:
            pdb.set_trace()
            _log.critical("this hive is not known to us")
        message_to_send = self._pack_message_to_send(msg)
        writer.write(message_to_send)
