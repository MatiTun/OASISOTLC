from sqlalchemy.orm import class_mapper
import json

def object_to_dict(obj):
    mapper = class_mapper(obj.__class__)
    out = {c.info.get('name') if c.info else c.name: getattr(obj, c.name) for c in obj.__table__.columns if '_ACT_' not in c.name and 'HASH' not in c.name}
    for name, relation in mapper.relationships.items():
        related_obj = getattr(obj, name)
        if related_obj is not None:
            if relation.uselist:
                out[name] = [object_to_dict(child) for child in related_obj]
            else:
                out[name] = object_to_dict(related_obj)
    return out

class BaseModel():
    
    def as_dict(self):
        return object_to_dict(self)