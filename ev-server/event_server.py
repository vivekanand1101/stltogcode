#!/usr/bin/env python

import json
import logging
import os
import sys
import urllib.parse as urlparse

import trollius
import trollius_redis

log = logging.getLogger(__name__)

webapp_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..',
)

sys.path.insert(1, webapp_path)

import webapp
import webapp.lib
from webapp.exceptions import WebappEvException

SERVER = None


def get_obj_from_path(path):
    """ Return the Ticket or Request object based on the path provided.
    """
    uid = path.decode()[1:]
    file_obj = webapp.lib.get_file(webapp.SESSION, uid=uid)
    return file_obj


@trollius.coroutine
def handle_client(client_reader, client_writer):
    data = None
    while True:
        # give client a chance to respond, timeout after 10 seconds
        line = yield trollius.From(trollius.wait_for(
            client_reader.readline(),
            timeout=10.0))
        if not line.strip():
            break
        line = line.rstrip()
        if data is None:
            data = line

    if data is None:
        log.warning("Expected uid, received None")
        return

    data = data.rstrip().split()
    log.info("Received %s", data)
    if not data:
        log.warning("No URL provided: %s" % data)
        return

    url = urlparse.urlsplit(data[1])

    try:
        obj = get_obj_from_path(url.path)
    except WebappEvException as err:
        log.warning(err.message)
        return

    origin = webapp.APP.config.get('APP_URL', 'http://127.0.0.1:5000')
    if origin.endswith('/'):
        origin = origin[:-1]

    client_writer.write((
        "HTTP/1.0 200 OK\n"
        "Content-Type: text/event-stream\n"
        "Cache: nocache\n"
        "Connection: keep-alive\n"
        "Access-Control-Allow-Origin: %s\n\n" % origin
    ).encode())

    connection = yield trollius.From(trollius_redis.Connection.create(
        host=webapp.APP.config['REDIS_HOST'],
        port=webapp.APP.config['REDIS_PORT'],
        db=webapp.APP.config['REDIS_DB']))

    try:

        # Create subscriber.
        subscriber = yield trollius.From(connection.start_subscribe())

        # Subscribe to channel.
        yield trollius.From(subscriber.subscribe(['webapp.%s' % obj.uid]))

        # Inside a while loop, wait for incoming events.
        while True:
            reply = yield trollius.From(subscriber.next_published())
            log.info("Sending %s", reply.value)
            client_writer.write(("data: %s\n\n" % reply.value).encode())
            yield trollius.From(client_writer.drain())

    except trollius.ConnectionResetError as err:
        log.exception("ERROR: ConnectionResetError in handle_client")
    except Exception as err:
        log.exception("ERROR: Exception in handle_client")
    finally:
        # Wathever happens, close the connection.
        connection.close()
        client_writer.close()


def main():
    global SERVER

    try:
        loop = trollius.get_event_loop()
        coro = trollius.start_server(
            handle_client,
            host=None,
            port=webapp.APP.config['EVENTSOURCE_PORT'],
            loop=loop)
        SERVER = loop.run_until_complete(coro)
        log.info(
            'Serving server at {}'.format(SERVER.sockets[0].getsockname()))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except trollius.ConnectionResetError as err:
        log.exception("ERROR: ConnectionResetError in main")
    except Exception:
        log.exception("ERROR: Exception in main")
    finally:
        # Close the server
        SERVER.close()
        log.info("End Connection")
        loop.run_until_complete(SERVER.wait_closed())
        loop.close()
        log.info("End")


if __name__ == '__main__':
    log = logging.getLogger("")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(module)s:%(lineno)d] %(message)s")

    # setup console logging
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    aslog = logging.getLogger("asyncio")
    aslog.setLevel(logging.DEBUG)

    ch.setFormatter(formatter)
    log.addHandler(ch)
    main()
