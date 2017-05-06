from webapp import APP
from webapp.lib import model

model.create_tables(
    APP.config['DB_URL'],
    debug=True
)
