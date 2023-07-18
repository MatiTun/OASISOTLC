from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('configuration.DevelopmentConfig')

db = SQLAlchemy(app, session_options={"autoflush": False})

cors = CORS(app, resources={r'/*':{'origin':['*']}})

from app.otlc.controllers.contract import otlc

app.register_blueprint(otlc)