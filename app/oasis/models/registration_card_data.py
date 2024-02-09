from datetime import datetime
from app import dbaws as db
from app.herpers.utilis import BaseModel

class RegistrationCardData(db.Model, BaseModel):
    __bind_key__            = 'AWS'
    __tablename__               = 'AVHOJAREGISTROFIRMAPAX'
    HR_ID                       = db.Column(db.Numeric(9), nullable=False)
    HR_HOTEL                    = db.Column(db.String(10), nullable=True, index=True,primary_key=True)
    HR_RESERVA                  = db.Column(db.String(20), nullable=True, index=True,primary_key=True)
    HR_LINEA                    = db.Column(db.Numeric(5), nullable=True, index=True,primary_key=True)
    HR_SECUENCIA                = db.Column(db.Numeric(3), nullable=True, index=True,primary_key=True)
    HR_NOMBRE                   = db.Column(db.String(150), nullable=True)
    HR_ARCHIVO                  = db.Column(db.String(20), nullable=True)
    HR_TIPO                     = db.Column(db.String(15), nullable=True)
    HR_EDAD                     = db.Column(db.Numeric(2), nullable=True)
    HR_BRAZALETE                = db.Column(db.String(30), nullable=True)
    HR_PASAPORTE                = db.Column(db.String(30), nullable=True)
    HR_EMAIL                    = db.Column(db.String(30), nullable=True)
    HR_IMG64                    = db.Column(db.LargeBinary, nullable=True)
    HR_PASS64                   = db.Column(db.LargeBinary, nullable=True)
    HR_REVERSO64                = db.Column(db.LargeBinary, nullable=True)
    HR_CAP_F                    = db.Column(db.DateTime,nullable=True)
    HR_CAP_H                    = db.Column(db.String(8),nullable=True)
    HR_CAP_U                    = db.Column(db.String(8), nullable=True)
    HR_NUM_TDR                  = db.Column(db.Numeric(3), nullable=True)
    HR_FECHA_NAC                = db.Column(db.DateTime, nullable=True)
    HR_NOMBRE_IDENT_FRENTE      = db.Column(db.String(100), nullable=True)
    HR_NOMBRE_IDENT_REVERSO     = db.Column(db.String(100), nullable=True)
    HR_TIPO_IDENT               = db.Column(db.String(100), nullable=True)
    HR_CAP_T                    = db.Column(db.String(20), nullable=True)
    HR_NACIONALIDAD             = db.Column(db.String(50), nullable=True)
    HR_VIGENCIAID               = db.Column(db.DateTime,nullable=True)