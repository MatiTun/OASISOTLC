from datetime import datetime, date, timedelta
from decimal import Decimal
from app import db
import json
import base64
from dateutil.parser import parse

dateformat = None
def pagination(result):
    return {
        'page': result.page,
        'pages': result.pages,
        'total_count': result.total,
        'has_prev': result.has_prev,
        'prev': result.prev_num,
        'has_next': result.has_next,
        'next': result.next_num
    }

def get_class_by_tablename(tablename):
    for c in db.Model.__subclasses__():
        if c.__tablename__ == tablename:
            return c
    return None
   

def response(data):
    _response = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                _response.append(response(item))
            else:
                try:
                    _response.append(item.as_dict())
                except Exception as ex:
                    _response.append(item._asdict())
    elif data:
        try:
            _response.append(data.as_dict())
        except Exception as ex:
            _response.append(data._asdict())
    return _response

def JsonResponse(code, data=None, data_json=None, msg=None, info=None, date_format=None):
    global dateformat 
    dateformat= date_format
    if code != 200:
        return json.dumps(
            {
                'code': code,
                'msg' : msg
            }
        ), code
    else:
        rsp = json.dumps(
            {
                'code': code,
                'info': info,
                'data': response(data) if data else data_json
            }
        , cls=MyJsonEncoder), code
        return rsp

def o_hook(o):
    _spec_type = o.get('_spec_type')
    if not _spec_type:
        return o
    else:
        return parse(o.get('val'))

class MyJsonEncoder(json.JSONEncoder):

    def __init__(self, dates=True, **kwargs):
        super(MyJsonEncoder, self).__init__(**kwargs)
        self.dates = dates

    def default(self, o):
        if isinstance(o, bytes):
            return str(base64.b64encode(o))
        if isinstance(o, (date, datetime)):
            if self.dates:
                if dateformat:
                    return datetime.strftime(o, '%Y-%m-%dT%H:%M:%S')
                return datetime.strftime(o, '%d/%m/%Y')
            else:
                return {"val": o.isoformat(), "_spec_type": "datetime"}
        if isinstance(o, Decimal):
            return float(o) 
        return json.JSONEncoder.default(self, o)