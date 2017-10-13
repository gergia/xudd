'''
Created on Feb 15, 2016

@author: gavran
'''
# from __future__ import print_function
# 
# import sys
# import logging
# import select
# import socket
# import traceback
# import pdb
# import asyncio
# import json
# 
# try:
#     import urlparse
# except ImportError:
#     import urllib.parse as urlparse
# 
# from tornado import httputil, escape
# 
# try:
#     from io import BytesIO # python 3
# except ImportError:
#     from cStringIO import StringIO as BytesIO # python 2
# 
# from xudd.actor import Actor
# from xudd.hive import Hive
# from xudd.tools import join_id
# from xudd.message import Message
# from collections import namedtuple
# 
# logging.basicConfig(level=logging.DEBUG)
# _log = logging.getLogger(__name__)
# 
# Client = namedtuple('Client', 'reader writer')
# class NetworkHive(Hive):
#     def __init__(self, hive_id=None):
#         super(NetworkHive, self).__init__(hive_id)
#         self.message_routing.update({
#             'respond': self.respond,
#             'start_listening': self.listen
#         })
# #         self.message_routing.update(
# #             {"register_hive": self.register_hive}
# #              )
#         self.requests = {}
#         self.loop = asyncio.get_event_loop()
#         self.registered_hives = {}
#     
#     @asyncio.coroutine
#     def listen(self, message):
#         _log.debug("in listen")
#         print("in listen")
#         self.host = message.body.get("host")
#         self.port = message.body.get("port")
#         
#         try:
#             self.server = yield from asyncio.start_server(self.client_connected, self.host, self.port)
#             _log.debug('Running server on {}:{}'.format(self.host, self.port))
#         except OSError:
#             _log.error('Cannot bind to this port! Is the server already running?')
# 
# 
#     @asyncio.coroutine
#     def client_connected(self, reader, writer):
#         print('Client connected.')
#         #getting the name of a client (could it be chosen?). many other info can be gathered from the extra info
#         #client here is just a named tuple
#         new_client = Client(reader, writer)
#         #storing it into a list of all clients
#     
#         while not reader.at_eof():
#             try:
#                 msg = yield from reader.readline()
#                 if msg:
#                     
#                     pdb.set_trace()
#                     
#                     msg = json.loads(msg.decode())
#                     received_message = Message.from_dict(msg)
#                     _log.debug('Server Received: "{}"'.format(received_message))
#             except ConnectionResetError as e:
#                 print('ERROR: {}'.format(e))
#                 del self.clients[hive_id]
#                 return
# 
#  
#     def respond(self, message):
#         _log.debug('Responding')
#  
#         sock, bind = self.requests.get(message.in_reply_to)
#         sock.sendall(message.body['response'])
#         sock.close()
#         del self.requests[message.in_reply_to]
#         _log.info('Responded')
#         
# class WebSocketHandler(Actor):
#     def __init__(self, hive, id):
#         super(WebSocketHandler, self).__init__(hive, id)
#         self.message_routing.update({
#             'handle_request': self.handle_request
#         })
# 
#     def handle_request(self, message):
#         _log.debug("handling message...")
#         _log.debug(message.body['request'])
#         request = message.body['request']
#         socket = request[0]
#         message = ""
#         while True:
#             data = socket.recv(2048)
#             message += data.decode()
#             if not data: 
#                 break
#         _log.debug(message)
            
        
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
from xudd.demos.NetworkHive import NetworkHive
Client = namedtuple('Client', 'reader writer')
logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)   





if __name__ == '__main__':
    
    hive = NetworkHive()
    hive.send_message(to=hive.id, directive="start_listening", body={"port":8000, "host":"127.0.0.1"})
    hive.run()