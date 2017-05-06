import os

SECRET_KEY = 'thisissupposedtobeasecret'
DB_URL = 'postgresql://postgres:@localhost/conversion'
APP_URL = 'http://127.0.0.1:5000'

# SSE
EVENTSOURCE_SOURCE = 'http://127.0.0.1:8080/'
REDIS_HOST = '0.0.0.0'
REDIS_PORT = 6379
REDIS_DB = 0
EVENTSOURCE_PORT = 8080

# conversion server
CONVERSION_SERVER_PORT = 8081

# Max file size - 4 MB
MAX_CONTENT_LENGTH = 4 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..',
    'uploads',
)

OUTPUT_FOLDER = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..',
    'output',
)

CURAENGINE_FOLDER = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '../..',
    'CuraEngine',
)


ALLOWED_EXTENSIONS = {
    'stl': 'gcode',
}
