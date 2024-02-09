from app import dbavalon as db

class BookingsDetailAvalon(db.Model):
    __bind_key__                = 'AVALON'
    __tablename__               = 'RECReservasDetalle'
    Reserva                     = db.Column(db.String(20), nullable=False, primary_key=True, index=True)
    Linea                       = db.Column(db.Numeric(12), nullable=False, primary_key=True, index=True)
    HotelUso                    = db.Column(db.String(20), nullable=False)
    Cantidad                    = db.Column(db.Numeric(10), nullable=False)
    Habitacion                  = db.Column(db.String(20), nullable=False)
    FechaEntrada                = db.Column(db.DateTime, nullable=False)
    FechaSalida                 = db.Column(db.DateTime, nullable=False)
    Noches                      = db.Column(db.Numeric(10), nullable=False)
    THUso                       = db.Column(db.String(20), nullable=False)
    RegimenUso                  = db.Column(db.String(20), nullable=False)
    AD                          = db.Column(db.Numeric(10), nullable=False)
    JR                          = db.Column(db.Numeric(10), nullable=False)
    NI                          = db.Column(db.Numeric(10), nullable=False)
    CU                          = db.Column(db.Numeric(10), nullable=False)
    Estado                      = db.Column(db.Numeric(10), nullable=False, index=True)
    Situacion                   = db.Column(db.Numeric(10), nullable=False)
    Facturacion                 = db.Column(db.Numeric(10), nullable=False)
    FacturacionComercializadora = db.Column(db.Numeric(10), nullable=False)


class BookingsGuestAvalon(db.Model):
    __bind_key__            = 'AVALON'
    __tablename__           = 'RECReservasClientes'
    Reserva                 = db.Column(db.String(20), nullable=False, primary_key=True)
    Linea                   = db.Column(db.Numeric(12), nullable=False, primary_key=True)
    Numero                  = db.Column(db.Numeric(10), nullable=False, primary_key=True)
    TipoPersona             = db.Column(db.String(5), nullable=False)
    FechaEntrada            = db.Column(db.DateTime, nullable=False)
    FechaSalida             = db.Column(db.DateTime, nullable=False)
    Estado                  = db.Column(db.Numeric(10), nullable=False)
    Nombre                  = db.Column(db.String(50), nullable=False)
    Apellido1               = db.Column(db.String(50), nullable=False)
    Apellido2               = db.Column(db.String(50), nullable=False)
    Edad                    = db.Column(db.Numeric(10), nullable=False)
    ParteViajeros           = db.Column(db.Numeric(10), nullable=False)
    PreCheckIn              = db.Column(db.Numeric(1), nullable=False)
    Parentesco              = db.Column(db.Numeric(10), nullable=False)
    ClaveCardex             = db.Column(db.String(100), nullable=True)