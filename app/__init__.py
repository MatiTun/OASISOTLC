from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('configuration.DevelopmentConfig')

db = SQLAlchemy(app, session_options={"autoflush": False})

cors = CORS(app, resources={r'/*':{'origin':['http://localhost','http://192.168.2.57','https://staging.oasis-tlc.com']}},
methods=['GET','POST'],
allow_headers= ['Accept','Content-Type','Authorization','Access-Control-Allow-Credentials'],
supports_credentials=True)

from app.otlc.controllers.contract import otlc

app.register_blueprint(otlc)