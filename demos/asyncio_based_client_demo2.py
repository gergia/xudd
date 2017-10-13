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


try:
    from io import BytesIO # python 3
except ImportError:
    from cStringIO import StringIO as BytesIO # python 2

from xudd.actor import Actor

from xudd.tools import join_id
from collections import namedtuple
from xudd.demos.NetworkHive import NetworkHive

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)
Client = namedtuple('Client', 'reader writer')
   

class GameStarter(Actor):
    def __init__(self, hive, id):
        super(GameStarter, self).__init__(hive, id)
        self.message_routing.update({"connected":self.send_the_message,
                                          "start_the_game":self.connect})
        self.server_hive_id = "s_hive_id"
    def connect(self, message):
        self.hive.send_message(to=self.hive.hive_id,\
                               directive="connect",\
                               body={"host":"127.0.0.1", "port":8000, "distant_hive_id":self.server_hive_id})
        
    def send_the_message(self, message):
        self.hive.send_message(to=join_id(self.server_hive_id, self.server_hive_id), directive="greeting", body={"content":"hi, how are yuo"})

        
class ClientHive(NetworkHive):
    def __init__(self, hive_id=None):
        super(ClientHive, self).__init__(hive_id)
        
    
                                    
        

def main():
    print("main")
    hive = ClientHive()
    gameStarter = hive.create_actor(GameStarter)
    hive.send_message(to=gameStarter, directive="start_the_game")
    hive.run()

if __name__ == '__main__':
    main()
    