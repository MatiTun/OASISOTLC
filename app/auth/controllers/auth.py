from app import app, dbaws as db
from functools import wraps
from flask import Blueprint, request, jsonify
from ..models.auth import User, APIKey
from uuid import uuid4

auth = Blueprint('auth', __name__, url_prefix='/auth')


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        if 'x-api-key' in request.headers:
            api_key = APIKey.query.filter(APIKey.AK_TOKEN==request.headers['x-api-key']).first()
            if api_key:
                print('ip_peticion', request.remote_addr)
                if api_key.AK_IP == '0.0.0.0' or (api_key.AK_IP != '0.0.0.0' and api_key.AK_IP == request.remote_addr):
                    return f(*args, **kwargs)
                else:
                    return jsonify({
                            'mensaje': 'Host inválido',
                            'autentificado': False
                        }), 401
            else:
                return jsonify({
                        'mensaje': 'ApiKey inválido',
                        'autentificado': False
                    }), 401
        else:
            return jsonify({
                'mensaje': 'ApiKey requerido',
                'autentificado': False
            }), 401
    return _verify


@auth.route('/generate/api-key/<client>', methods=['GET'])
def create_api_key(client):
    user = User.query.filter(User.USERNAME==client, User.ACTIVE==1).first()
    if user:
        key = "".join(str(uuid4()).split('-'))
        key = key + "".join(str(uuid4()).split('-'))
        new_key = APIKey(client, key)
        db.session.merge(new_key)
        db.session.commit()
        return new_key.AK_TOKEN
    else:
        return 'usuario inexistente o en baja'