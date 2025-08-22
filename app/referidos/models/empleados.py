from app import db
from app.helpers.utilis import BaseModel

class EmpleadosView(db.Model, BaseModel):
    __bind_key__            = 'GRH'
    __tablename__       = 'GRHEMPLEADOS_V2'
    EM_EMP          = db.Column(db.Numeric(6,0), nullable=False, primary_key=True, info={'name':'Numero'})
    EM_NOMBRE       = db.Column(db.String(35), nullable=False, info={'name':'Nombre'})
    EM_DEPTO        = db.Column(db.String(5), nullable=False)
    EM_DEPTO_DESC   = db.Column(db.String(30), nullable=False, info={'name':'Departamento'})
    EM_HOTEL        = db.Column(db.String(5), nullable=True, info={'name':'Hotel'})
    EM_ACTIVO       = db.Column(db.String(1), nullable=False)