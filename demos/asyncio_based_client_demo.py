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

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)
Client = namedtuple('Client', 'reader writer')
   
    
        
class Sender(Actor):
    def __init__(self, hive, id):
        super(Sender, self).__init__(hive, id)
        self.message_routing.update(
            {"send_random": self.send_random})
        
    def send_random(self, message):
        self.hive.send_message(to="general@general", directive="bokbok", body={"message":"kak si? pa tak"})
        

class GameStarter(Actor):
    def __init__(self, hive, id):
        super(GameStarter, self).__init__(hive, id)
        self.message_routing.update({"start_the_game":self.start,
                                    "connected":self.send_messages})
        
    def start(self, message):
        print("starting the game")
        self.hive.send_message(to=self.hive.hive_id, directive="connect", body={"host":"127.0.0.1", "port":8000})
    def send_messages(self, message):
        crazy_sender = self.hive.create_actor(Sender)
        self.hive.send_message(to=crazy_sender, directive="send_random")
        print("tam")

def main():
    print("main")
    hive = NetworkHive()
    gameStarter = hive.create_actor(GameStarter)
    hive.send_message(to=gameStarter, directive="start_the_game")
    hive.run()

if __name__ == '__main__':
    main()
    