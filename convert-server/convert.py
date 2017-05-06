#!/usr/bin/env python

import time
import json
import logging
import os
import sys
import subprocess
import urllib.parse as urlparse

import requests
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


def _get_file_from_obj(file_obj):
    ''' Given the file object, return the actual file path '''
    directory = webapp.APP.config['UPLOAD_FOLDER']
    return directory + '/' + file_obj.uid + '-' + file_obj.secure_filename


def convert_file(uid):
    ''' Convert the file from stl to gcode '''
    file_obj = webapp.lib.get_file(webapp.SESSION, uid=uid)
    filepath = _get_file_from_obj(file_obj)
    if not os.path.exists(filepath):
        raise webapp.exceptions.WebappException(
            'File not found while converting')

    original_file = webapp.APP.config['UPLOAD_FOLDER'] \
        + '/' + uid + '-' + file_obj.secure_filename
    original_extension = original_file.split('.')[-1]
    new_extension = webapp.APP.config['ALLOWED_EXTENSIONS'][original_extension]
    new_filename = webapp.lib.rreplace(
        file_obj.secure_filename, original_extension, new_extension, 1)
    converted_file = webapp.APP.config['OUTPUT_FOLDER'] \
        + '/' + uid + '-' + new_filename

    cura_engine_dir = webapp.APP.config['CURAENGINE_FOLDER']
    cmd = "./build/CuraEngine slice -v -j fdmprinter.def.json -o %s -e0 -l %s"
    cmd = cmd % (converted_file, original_file)
    subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cura_engine_dir,
    )
    return webapp.APP.config['APP_URL'] + '/converted/' + uid


@trollius.coroutine
def handle_messages():
    ''' Take the files from the queue and start converting '''

    connection = yield trollius.From(trollius_redis.Connection.create(
        host=webapp.APP.config['REDIS_HOST'],
        port=webapp.APP.config['REDIS_PORT'],
        db=webapp.APP.config['REDIS_DB'])
    )

    try:

        # Create subscriber.
        subscriber = yield trollius.From(connection.start_subscribe())

        # Subscribe to channel.
        yield trollius.From(subscriber.subscribe(['webapp.convert']))

        while True:
            reply = yield trollius.From(subscriber.next_published())
            log.info(reply)
            # do the conversion here
            # the conversion is shockingly fast :/
            # allow the client to be connect with sse server
            # before the conversion has already taken place
            time.sleep(3)
            uid = json.loads(reply.value)['uid']
            reply = convert_file(uid)
            out = {"uid": uid, "down_link": reply}
            # send back the result
            webapp.lib.trigger_ev_server(uid, json.dumps(out))

    except trollius.ConnectionResetError:
        log.exception("ERROR: ConnectionResetError converting")
    except Exception as err:
        log.exception("ERROR: Some problem occured while converting")
    finally:
        connection.close()


def main():
    try:
        loop = trollius.get_event_loop()
        tasks = [
            trollius.async(handle_messages()),
        ]
        loop.run_until_complete(trollius.wait(tasks))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except trollius.ConnectionResetError as err:
        log.exception("ERROR: ConnectionResetError in main")
    except Exception:
        log.exception("ERROR: Exception in main")
    finally:
        log.info("End Connection")
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
