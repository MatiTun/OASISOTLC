import os
from os.path import join, dirname, realpath

class BaseConfig(object):
    'Base configuracion'
    SQLALCHEMY_TRACK_MODIFICATIONS  = False
    SQLALCHEMY_DATABASE_URI         = 'oracle://COMER:SERVICE@192.168.1.25:1521/ZEUS'
    SQLALCHEMY_BINDS = {
        'OTLC'  : 'oracle://OTLC:SERVICE@192.168.1.25:1521/ZEUS',
    }
    BASE_DIR                        = os.path.abspath(os.path.dirname(__file__))
class ProductionConfig(BaseConfig):
    'Produccion configuracion'
    SECRET_KEY  = '0@s1sD3v3l0pm3nt'
    DEBUG       = False
    TESTING     = False
class DevelopmentConfig(BaseConfig):
    'Desarrollo configuracion'
    SECRET_KEY  = 'DesarrolloKey'
    DEBUG       = True
    TESTING     = True