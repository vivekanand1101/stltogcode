#!/usr/bin/env python
# coding=utf-8

import flask
from flask import Flask

APP = Flask(__name__)

APP.config.from_object('webapp.default_config')

import webapp.lib

SESSION = webapp.lib.create_session(APP.config['DB_URL'])

webapp.lib.set_redis(
    host=APP.config['REDIS_HOST'],
    port=APP.config['REDIS_PORT'],
    dbname=APP.config['REDIS_DB']
)

import webapp.ui.app

@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()
