from flask import Flask

app = Flask(__name__)

app.config.update(
SECRET_KEY = "development key",
HOST="localhost",
USERNAME = "appuser",
PASSWORD = "rextrebat",
DB = "hotel_genome",
)

import views
