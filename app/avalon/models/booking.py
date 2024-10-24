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
    
class BookingsAvalon(db.Model):
    __bind_key__            = 'AVALON'
    __tablename__           = 'RECReservas'
    Reserva                 = db.Column(db.String(20), nullable=False, primary_key=True, index=True)
    Linea                   = db.Column(db.Numeric(12), nullable=False, primary_key=True, index=True)
    EntidadNegocio          = db.Column(db.String(20), nullable=False, index=True)
    Entidad                 = db.Column(db.String(20), nullable=False, index=True)
    HotelFactura            = db.Column(db.String(20), nullable=False, index=True)
    THFactura               = db.Column(db.String(20), nullable=False)
    RegimenFactura          = db.Column(db.String(20), nullable=False)
    Tarifa                  = db.Column(db.String(20), nullable=False)
    Oferta                  = db.Column(db.String(20), nullable=False)
    Estancia                = db.Column(db.Numeric(10), nullable=False)
    Grupo                   = db.Column(db.String(30), nullable=False)
    NombreContacto          = db.Column(db.String(50), nullable=False)
    TipoCliente             = db.Column(db.String(20), nullable=False)
    TipoCredito             = db.Column(db.Numeric(2), nullable=False)
    LimiteCredito           = db.Column(db.Numeric(18,3), nullable=False)
    Referencia              = db.Column(db.String(50), nullable=False)
    Localizador             = db.Column(db.String(50), nullable=False)
    Bono                    = db.Column(db.String(50), nullable=False)
    AltaUsuario             = db.Column(db.String(20), nullable=False)
    AltaFecha               = db.Column(db.DateTime, nullable=False)
    ModificacionUsuario     = db.Column(db.String(20), nullable=False)
    ModificacionFecha       = db.Column(db.DateTime, nullable=False)
    Canal                   = db.Column(db.String(20), nullable=False)
    Segmento                = db.Column(db.String(20), nullable=False)
    LlegadaVueloAeropuerto  = db.Column(db.String(20), nullable=False)
    LlegadaDia              = db.Column(db.DateTime, nullable=False)
    SalidaVueloAeropuerto   = db.Column(db.String(20), nullable=False)
    SalidaDia               = db.Column(db.DateTime, nullable=False)
    TextoReserva            = db.Column(db.String(2000), nullable=False)
    Nacionalidad            = db.Column(db.String(20), nullable=False)
    VentaFecha              = db.Column(db.DateTime, nullable=False)
    CancelacionFecha        = db.Column(db.DateTime, nullable=False)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ValorationAvalon(db.Model):
    __bind_key__                = 'AVALON'
    __tablename__               = 'RECReservasValoracion'

    Autokey                     = db.Column(primary_key=True, nullable=False)
    Reserva                     = db.Column(db.String(20), nullable=True)
    LineaReserva                = db.Column(db.Numeric(10), nullable=True)
    Fecha                       = db.Column(db.DateTime, nullable=True)
    NumeroPersona               = db.Column(db.Numeric(10), nullable=True)
    Destino                     = db.Column(db.Numeric(10), nullable=True)
    TipoPersona                 = db.Column(db.Numeric(10), nullable=True)
    CentroProductivo            = db.Column(db.String(20), nullable=True)
    Importe                     = db.Column(db.Numeric(18, 4), nullable=True)
    ImporteProduccion           = db.Column(db.Numeric(18, 4), nullable=True)
    Garantia                    = db.Column(db.Numeric(10), nullable=True)
    Contrato                    = db.Column(db.String(20), nullable=True)
    Tarifa                      = db.Column(db.String(20), nullable=True)
    Oferta                      = db.Column(db.String(20), nullable=True)
    TipoServicio                = db.Column(db.Numeric(10), nullable=True)
    TipoPrecio                  = db.Column(db.Numeric(10), nullable=True)
    OrigenPrecio                = db.Column(db.Numeric(10), nullable=True)
    TipoLinea                   = db.Column(db.Numeric(10), nullable=True)
    PrecioFac                   = db.Column(db.Numeric(18, 4), nullable=True)
    DivisaFac                   = db.Column(db.String(20), nullable=True)
    PrecioDAFac                 = db.Column(db.Numeric(18, 4), nullable=True)
    Servicio                    = db.Column(db.String(20), nullable=True)
    GrupoImpuestoNegocio         = db.Column(db.String(20), nullable=True)
    GrupoImpuestoProducto       = db.Column(db.String(20), nullable=True)
    PorcentajeImpuesto          = db.Column(db.Numeric(18, 4), nullable=True)
    ImporteDA                   = db.Column(db.Numeric(18, 4), nullable=True)
    ImporteProduccionDA         = db.Column(db.Numeric(18, 4), nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ExchangeAvalon(db.Model):
    __bind_key__                = 'AVALON'
    __tablename__               = 'TiposCambioDivisa'
    
    Divisa                     = db.Column(db.String(20), primary_key=True, nullable=False)
    FechaCambio                = db.Column(db.DateTime, nullable=True)
    TipoCambio                 = db.Column(db.Numeric(18, 6), nullable=True)
    TipoCambioCompraBilletes    = db.Column(db.Numeric(18, 6), nullable=True)
    TipoCambioCompraCheques     = db.Column(db.Numeric(18, 6), nullable=True)
    TipoCambioVentaBilletes     = db.Column(db.Numeric(18, 6), nullable=True)
    TipoCambioVentaCheques      = db.Column(db.Numeric(18, 6), nullable=True)
    DivisaLocal                = db.Column(db.String(20), nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
class EntitiesAvalon(db.Model):
    __bind_key__                = 'AVALON'
    __tablename__               = 'HOTEntidades'

    Entidad                     = db.Column(db.String(20), primary_key=True, nullable=False)
    CIF                         = db.Column(db.String(20), nullable=True)
    Nombre                      = db.Column(db.String(50), nullable=True)
    Tipo                        = db.Column(db.String(20), nullable=True)
    DivisaFacturas              = db.Column(db.String(20), nullable=True)
    GrupoImpuestoNegocio        = db.Column(db.String(20), nullable=True)
    AgrupacionFacturas          = db.Column(db.Numeric(10), nullable=True)
    TarifasPermitidas           = db.Column(db.Numeric(10), nullable=True)
    DestinoEstancia             = db.Column(db.Numeric(10), nullable=True)
    EnvioFacturas               = db.Column(db.Numeric(10), nullable=True)
    ReservasEnFactura           = db.Column(db.Boolean, nullable=True)
    AgrupacionFacturasGarantia  = db.Column(db.Numeric(10), nullable=True)
    FusionFacturasGarantia      = db.Column(db.Numeric(10), nullable=True)
    Bloqueada                   = db.Column(db.Boolean, nullable=True)
    FormatoFacturas             = db.Column(db.Numeric(10), nullable=True)
    EFacturacion                = db.Column(db.Numeric(10), nullable=True)
    TextoEmailFacturas          = db.Column(db.String(500), nullable=True)
    AsuntoEmailFacturas         = db.Column(db.String(100), nullable=True)
    Prepago                     = db.Column(db.Boolean, nullable=True)
    NoFacturarImporteCero       = db.Column(db.Boolean, nullable=True)
    CobroFacturas               = db.Column(db.Numeric(10), nullable=True)
    TipoDocumento               = db.Column(db.String(20), nullable=True)
    FormaPago                   = db.Column(db.String(20), nullable=True)
    TerminoPago                 = db.Column(db.String(20), nullable=True)
    CodigoIATA                  = db.Column(db.String(50), nullable=True)
    Alias                       = db.Column(db.String(50), nullable=True)
    CargosEntidadConEstancia    = db.Column(db.Boolean, nullable=True)
    AvisarBloqueoVentas         = db.Column(db.Boolean, nullable=True)
    Proveedor                   = db.Column(db.String(20), nullable=True)
    PorcentajePrepago           = db.Column(db.Numeric(18, 4), nullable=True)
    CodigoFiscal                = db.Column(db.String(40), nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class CommentsAvalon(db.Model):
    __bind_key__                = 'AVALON'
    __tablename__               = 'RECReservasComentarios'

    Clave                       = db.Column(primary_key=True, nullable=False)
    Reserva                     = db.Column(db.String(20), nullable=False)
    Linea                       = db.Column(db.Numeric(10), nullable=False)
    Interno                     = db.Column(db.Boolean, nullable=True)
    CheckIn                     = db.Column(db.Boolean, nullable=True)
    CheckOut                    = db.Column(db.Boolean, nullable=True)
    Texto                       = db.Column(db.String(2000), nullable=True)
    Canales                     = db.Column(db.Boolean, nullable=True)
    Cancelacion                 = db.Column(db.Boolean, nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    


    
    
    