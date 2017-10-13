'''
Created on Feb 15, 2016

@author: gavran
'''

        
from __future__ import print_function

import logging

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

from collections import namedtuple
from xudd.demos.NetworkHive import NetworkHive
Client = namedtuple('Client', 'reader writer')
logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)   



class GameStarter(Actor):
    def __init__(self, hive, id):
        super(GameStarter, self).__init__(hive, id)
        self.message_routing.update({"start_the_game":self.start_listening})

    def start_listening(self, message):
        self.hive.send_message(to=self.hive.hive_id,\
                               directive="start_listening",\
                               body={"host":"127.0.0.1", "port":8000})
        
    

        
class ServerHive(NetworkHive):
    def __init__(self, hive_id=None):
        super(ServerHive, self).__init__(hive_id)
        self.message_routing.update({"greeting":self.greeting_received})
    
    def greeting_received(self, message):
        _log.info("greeting received")
        _log.info(message.body["content"])    
    
                                    
        

def main():
    hive = ServerHive(hive_id="s_hive_id")
    gameStarter = hive.create_actor(GameStarter)
    hive.send_message(to=gameStarter, directive="start_the_game")
    hive.run()

if __name__ == '__main__':
    main()
    
