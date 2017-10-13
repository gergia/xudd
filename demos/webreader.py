"""
"""
from __future__ import print_function

import urllib.parse
try:
    # Use builtin asyncio on Python 3.4+, or asyncio on Python 3.3
    import asyncio
except ImportError:
    # Use Trollius on Python <= 3.2
    import trollius as asyncio
import time
import argparse

from xudd.tools import join_id
from xudd.hive import Hive
from xudd.actor import Actor
from xudd.lib.multiprocess import MultiProcessAmbassador


# Taken from asyncio docs
@asyncio.coroutine
def print_http_headers(url):
    url = urllib.parse.urlsplit(url)
    reader, writer = yield from asyncio.open_connection(url.hostname, 80)
    query = (
        "HEAD {url.path} HTTP/1.0\r\n"
        "Host: {url.hostname}\r\n"
        "\r\n").format(url=url)
    writer.write(query.encode("latin-1"))
    while True:
        line = yield from reader.readline()
        if not line:
            break

        line = line.decode("latin1").rstrip()
        if line:
            print("HTTP header> %s" % line)


class WebReader(Actor):
    def __init__(self, hive, id):
        super(WebReader, self).__init__(hive, id)

        self.message_routing.update(
            {"read_webs": self.read_webs,
             "chuckle_end": self.chuckle_end})

    def _setup_chuckle_end(self, future):
        self.hive.send_message(to=self.id, directive="chuckle_end")

    def chuckle_end(self, message):
        print("Haha!  Guess that's the end of that...")
        self.hive.send_shutdown()

    def read_webs(self, message):
        # Okay, first let's try doing this the "wait on future" style hack..
        # This is like asyncio support where we get the result back as a
        # message.
        # Pretty weird.
        print("first run via future_async()...")
        future = asyncio.async(print_http_headers(message.body["url"]))
        response = yield self.wait_on_future(future)
        print("after first run")

        # Next... Okay... This is Real Bona Fide asyncio style
        # "yield from" calls.
        #
        # It looks like yield *or* yield from both work :o
        print("now doing intermediate evil_print_http_headers...")
        url = message.body["url"]

        url = urllib.parse.urlsplit(url)
        reader, writer = yield from asyncio.open_connection(url.hostname, 80)
        query = ('HEAD {url.path} HTTP/1.0\r\n'
                 'Host: {url.hostname}\r\n'
                 '\r\n').format(url=url)
        writer.write(query.encode('latin-1'))
        while True:
            line = yield from reader.readline()
            if not line:
                break

            line = line.decode("latin1").rstrip()
            if line:
                print("HTTP header> %s" % line)
        print("Ultimate evil complete.")

        # Lastly, use the asyncio loop pretty much just connecting back to the
        # XUDDiverse manually
        print("before second one")
        future = asyncio.async(print_http_headers(message.body["url"]))
        future.add_done_callback(self._setup_chuckle_end)
        print("after second one's call")


def main():
    import sys
    url = sys.argv[1]

    hive = Hive()
    web_reader = hive.create_actor(WebReader)

    hive.send_message(
        to=web_reader,
        directive="read_webs",
        body={"url": url})

    hive.run()


if __name__ == "__main__":
    main()
