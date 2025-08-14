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

class ImpEst(db.Model):
    __bind_key__ = 'AVALON'
    __tablename__ = 'PRODetalleEstancia'

    Factura = db.Column(db.String(20), primary_key=True, nullable=False)
    ClaveID = db.Column(db.Numeric, nullable=False)
    Reserva = db.Column(db.String(20), nullable=True)
    LineaReserva = db.Column(db.Numeric, nullable=True)
    Destino = db.Column(db.Numeric, nullable=True)
    TipoPersona = db.Column(db.Numeric, nullable=True)
    NumeroPersona = db.Column(db.Numeric, nullable=True)
    Fecha = db.Column(db.DateTime, nullable=True)
    CentroProductivo = db.Column(db.String(20), nullable=True)
    Divisa = db.Column(db.String(20), nullable=True)
    ImpuestosIncluidos = db.Column(db.Boolean, nullable=True)
    PorcentajeImpuesto = db.Column(db.Numeric(18, 2), nullable=True)
    DiferencialImpuesto = db.Column(db.Boolean, nullable=True)
    Cantidad = db.Column(db.Numeric, nullable=True)
    Precio = db.Column(db.Numeric(18, 4), nullable=True)
    ImporteProduccion = db.Column(db.Numeric(18, 4), nullable=True)
    Garantia = db.Column(db.Numeric, nullable=True)
    Concepto = db.Column(db.String(50), nullable=True)
    FacturaOriginal = db.Column(db.String(20), nullable=True)
    Contrato = db.Column(db.String(20), nullable=True)
    Tarifa = db.Column(db.String(20), nullable=True)
    Oferta = db.Column(db.String(20), nullable=True)
    TipoServicio = db.Column(db.Numeric, nullable=True)
    TipoPrecio = db.Column(db.Numeric, nullable=True)
    OrigenPrecio = db.Column(db.Numeric, nullable=True)
    RG = db.Column(db.String(36), nullable=True)  
    TipoLinea = db.Column(db.Numeric, nullable=True)
    ClaveComision = db.Column(db.String(36), nullable=True)  
    LineaFactura = db.Column(db.Numeric, nullable=True)
    ReferenciaPaqueteCT = db.Column(db.String(36), nullable=True)  
    CodigoPremio = db.Column(db.String(20), nullable=True)
    CodigoTTu = db.Column(db.String(20), nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ImExt(db.Model):
    __bind_key__ = 'AVALON'
    __tablename__ = 'RECReservasPreciosExterno'

    Reserva = db.Column(db.String(20), primary_key=True, nullable=False)
    Linea = db.Column(db.Numeric, nullable=False)
    Orden = db.Column(db.Numeric, nullable=False)
    Tarifa = db.Column(db.String(20), nullable=True)
    LineaTarifa = db.Column(db.String(20), nullable=True)
    Importe = db.Column(db.Numeric(18, 5), nullable=True)
    Divisa = db.Column(db.String(20), nullable=True)
    Concepto = db.Column(db.String(50), nullable=True)
    Fecha = db.Column(db.DateTime, nullable=True)
    NumeroPersona = db.Column(db.Numeric, nullable=True)
    TipoPersona = db.Column(db.String(20), nullable=True)
    TipoLinea = db.Column(db.String(20), nullable=True)
    TipoPrecio = db.Column(db.String(20), nullable=True)
    TipoSuplemento = db.Column(db.String(20), nullable=True)
    RG = db.Column(db.String(36), nullable=True)  
    TipoPrecioAvalon = db.Column(db.Numeric, nullable=True)
    CodigoSuplemento = db.Column(db.String(20), nullable=True)
    CargoPorCancelacion = db.Column(db.Boolean, nullable=True)
    ImporteOriginal = db.Column(db.Numeric(18, 5), nullable=True)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    
class bookingsOtlc (db.Model):
    __bind_key__            = 'OTLC'
    __tablename__           = 'RSRESERVAS'
    RS_RESERVA              = db.Column(db.String(20), nullable=False, primary_key=True)
    RS_STATUS               = db.Column(db.String(1), default='R')
    RS_HOTEL                = db.Column(db.String(5))
    RS_LLEGADA              = db.Column(db.Date)
    RS_LLEGADA_HORA         = db.Column(db.String(5))
    RS_SALIDA               = db.Column(db.Date)
    RS_SALIDA_HORA          = db.Column(db.String(5), default='12:00')
    RS_NOCHES               = db.Column(db.Numeric(1))
    RS_SALIDA_PREVIA        = db.Column(db.Date)
    RS_SALIDA_PREVIA_HORA   = db.Column(db.String(5))
    RS_MERCADO              = db.Column(db.String(12))
    RS_AGENCIA              = db.Column(db.String(50))
    RS_TRATO                = db.Column(db.String(12))
    RS_GRUPO                = db.Column(db.String(12))
    RS_EVENTO               = db.Column(db.String(12))
    RS_TIPO_CLIENTE         = db.Column(db.String(12))
    RS_LINEA_ROOM_LIST      = db.Column(db.Numeric)
    RS_ADULTOS              = db.Column(db.Numeric)
    RS_JUNIORS              = db.Column(db.Numeric)
    RS_MENORES              = db.Column(db.Numeric)
    RS_BEBES                = db.Column(db.Numeric)
    RS_NOTAS                = db.Column(db.String(100))
    RS_NOTAS_SISTEMAS       = db.Column(db.String(100))
    RS_CATEGORIA            = db.Column(db.String(50), nullable=False)
    RS_TIPO_HABITACION      = db.Column(db.String(10), nullable=False)
    RS_TARIFA               = db.Column(db.Numeric(14,2))
    RS_IMPORTE              = db.Column(db.Numeric(14,2))
    RS_MONEDA               = db.Column(db.String(12))
    RS_TIPO_CAMBIO          = db.Column(db.Numeric(14,2))
    RS_ISA                  = db.Column(db.Numeric(14,2))
    RS_FEE                  = db.Column(db.Numeric(14,2))
    RS_HABITACION           = db.Column(db.String(12))
    RS_HOTEL_ORIGEN         = db.Column(db.Numeric)
    RS_RESERVA_ORIGEN       = db.Column(db.String(8))
    RS_HOTEL_DESTINO        = db.Column(db.Numeric)
    RS_RESERVA_DESTINO      = db.Column(db.String(8))
    RS_VOUCHER              = db.Column(db.String(20))
    RS_CONFIRMACION         = db.Column(db.String(20))
    RS_MEMBRESIA            = db.Column(db.String(20))
    RS_NIVEL                = db.Column(db.String(12))
    RS_PREREGISTRO          = db.Column(db.Numeric)
    RS_PREPAGO_IMPORTE      = db.Column(db.Numeric)
    RS_PREPAGO_FECHA        = db.Column(db.Date)
    RS_VENTA_FECHA          = db.Column(db.Date)
    RS_VENTA_HORA           = db.Column(db.String(5))
    RS_VENTA_USUARIO        = db.Column(db.String(10))
    RS_CAPTURA_FECHA        = db.Column(db.Date)
    RS_CAPTURA_HORA         = db.Column(db.String(5))
    RS_CAPTURA_USUARIO      = db.Column(db.String(10))
    RS_CANCELACION_FECHA    = db.Column(db.Date)
    RS_CANCELACION_HORA     = db.Column(db.String(5))
    RS_CANCELACION_USUARIO  = db.Column(db.String(10))
    RS_CANCELACION_MOTIVO   = db.Column(db.String(200))
    RS_SUBTOTAL             = db.Column(db.Numeric(12,4))
    RS_DESCTOI              = db.Column(db.Numeric(12,4))
    RS_DESCTO2I             = db.Column(db.Numeric(12,4))
    RS_NOTA_PRINCIPAL       = db.Column(db.String(100))
    RS_EMAIL                = db.Column(db.String(100))
    RS_ORIGEN               = db.Column(db.String(30))
    RS_OFERTA_DESC          = db.Column(db.String(30))
    RS_TARIFA_DESC          = db.Column(db.String(30))
    RS_LINEA                = db.Column(db.Numeric(4),nullable=False, primary_key=True)
    RS_IMPORTE_MANUAL       = db.Column(db.Numeric(12,2))
    RS_NOMBRE_SOCIO         = db.Column(db.String(100))
    RS_METODO_PAGO          = db.Column(db.String(50))
    RS_CONFIRMACION_LINEA   = db.Column(db.Numeric(5))
    RS_EMAIL2               = db.Column(db.String(100))
    RS_IMPORTEPAX           = db.Column(db.Numeric)
    RS_RESERVA_F            = db.Column(db.Date)
    RS_RESERVA_H            = db.Column(db.String(8))
    RS_RESERVA_U            = db.Column(db.String(15)) 
    RS_TRANSPORTE           = db.Column(db.String(20))
    RS_CODIGO_CRS           = db.Column(db.String(5))
    RS_ID_INSIST            = db.Column(db.String(30))
    RS_PROMO                = db.Column(db.String(20))
    RS_STATUS_AVALON        = db.Column(db.String(20))
    RS_NOCHES_AVALON        = db.Column(db.Numeric)
    RS_SALIDA_AVALON        = db.Column(db.Date)
    RS_IMPORTE_AVALON       = db.Column(db.Numeric(14,2))
    RS_AD_AVALON            = db.Column(db.Numeric(1,0))
    RS_JR_AVALON            = db.Column(db.Numeric(1,0))
    RS_MEN_AVALON           = db.Column(db.Numeric(1,0))
    RS_BE_AVALON            = db.Column(db.Numeric(1,0))
    RS_MONEDA_AVALON        = db.Column(db.String(12))
    RS_CONFLIN              = db.Column(db.String(12))
    
    def __init__(self, reserva, status, hotel, llegada, llegada_hora, salida, salida_hora, noches,
                salida_previa, salida_previa_hora, mercado, agencia, trato, grupo, evento, tipo_cliente,
                linea_room_list, adultos, juniors, menores, bebes, notas, notas_sistemas, categoria,
                tipo_habitacion, tarifa, importe, moneda, tipo_cambio, isa, fee, habitacion, hotel_origen,
                reserva_origen, hotel_destino, reserva_destino, voucher, confirmacion, menbresia, nivel,
                preregistro, prepago_importe, prepago_fecha, venta_fecha, venta_hora, venta_usuario,captura_fecha,
                captura_hora, captura_usuario, cancelacion_fecha, cancelacion_hora, cancelacion_usuario, cancelacion_motivo,subtotal,desctoi,desctoi2,
                origen,oferta,tarifa_desc,linea,manual,nombresocio,metodopago,confirmacionLinea, promocion, notaprincipal, conflin
                ):
        self.RS_RESERVA              = reserva
        self.RS_STATUS               = status
        self.RS_HOTEL                = hotel
        self.RS_LLEGADA              = llegada
        self.RS_LLEGADA_HORA         = llegada_hora
        self.RS_SALIDA               = salida
        self.RS_SALIDA_HORA          = salida_hora
        self.RS_NOCHES               = noches
        self.RS_SALIDA_PREVIA        = salida_previa
        self.RS_SALIDA_PREVIA_HORA   = salida_previa_hora
        self.RS_MERCADO              = mercado
        self.RS_AGENCIA              = agencia
        self.RS_TRATO                = trato
        self.RS_GRUPO                = grupo
        self.RS_EVENTO               = evento
        self.RS_TIPO_CLIENTE         = tipo_cliente
        self.RS_LINEA_ROOM_LIST      = linea_room_list
        self.RS_ADULTOS              = adultos
        self.RS_JUNIORS              = juniors
        self.RS_MENORES              = menores
        self.RS_BEBES                = bebes
        self.RS_NOTAS                = notas
        self.RS_NOTAS_SISTEMAS       = notas_sistemas
        self.RS_CATEGORIA            = categoria
        self.RS_TIPO_HABITACION      = tipo_habitacion
        self.RS_TARIFA               = tarifa
        self.RS_IMPORTE              = importe
        self.RS_MONEDA               = moneda
        self.RS_TIPO_CAMBIO          = tipo_cambio
        self.RS_ISA                  = isa
        self.RS_FEE                  = fee
        self.RS_HABITACION           = habitacion
        self.RS_HOTEL_ORIGEN         = hotel_origen
        self.RS_RESERVA_ORIGEN       = reserva_origen
        self.RS_HOTEL_DESTINO        = hotel_destino
        self.RS_RESERVA_DESTINO      = reserva_destino
        self.RS_VOUCHER              = voucher
        self.RS_CONFIRMACION         = confirmacion
        self.RS_MEMBRESIA            = menbresia
        self.RS_NIVEL                = nivel
        self.RS_PREREGISTRO          = preregistro
        self.RS_PREPAGO_IMPORTE      = prepago_importe
        self.RS_PREPAGO_FECHA        = prepago_fecha
        self.RS_VENTA_FECHA          = venta_fecha
        self.RS_VENTA_HORA           = venta_hora
        self.RS_VENTA_USUARIO        = venta_usuario
        self.RS_CAPTURA_FECHA        = captura_fecha
        self.RS_CAPTURA_HORA         = captura_hora
        self.RS_CAPTURA_USUARIO      = captura_usuario
        self.RS_CANCELACION_FECHA    = cancelacion_fecha
        self.RS_CANCELACION_HORA     = cancelacion_hora
        self.RS_CANCELACION_USUARIO  = cancelacion_usuario
        self.RS_CANCELACION_MOTIVO   = cancelacion_motivo
        self.RS_SUBTOTAL             = subtotal
        self.RS_DESCTOI              = desctoi
        self.RS_DESCTO2I             = desctoi2
        self.RS_ORIGEN               = origen
        self.RS_OFERTA_DESC          = oferta
        self.RS_TARIFA_DESC          = tarifa_desc
        self.RS_LINEA                = linea
        self.RS_IMPORTE_MANUAL       = manual
        self.RS_NOMBRE_SOCIO         = nombresocio
        self.RS_METODO_PAGO          = metodopago
        self.RS_CONFIRMACION_LINEA   = confirmacionLinea
        self.RS_PROMO                = promocion
        self.RS_NOTA_PRINCIPAL       = notaprincipal
        self.RS_CONFLIN              = conflin

class customers(db.Model):
    __bind_key__    = 'OTLC'
    __tablename__   = 'RSCLIENTES'

    CL_ID           = db.Column(db.Numeric(), primary_key=True) 
    CL_RESERVA      = db.Column(db.String(20), nullable=False)
    CL_NOMBRES      = db.Column(db.String(100), nullable=False)
    CL_APELLIDOS    = db.Column(db.String(100), nullable=False)
    CL_TIPO         = db.Column(db.String(1), nullable=False)
    CL_EDAD         = db.Column(db.Numeric())
    CL_PRINCIPAL    = db.Column(db.String(20))
    CL_LINEA        = db.Column(db.Numeric(38))
    CL_SECUENCIA    = db.Column(db.Integer)
    CL_CONFLIN      = db.Column(db.String(30))
    CL_CAP_U        = db.Column(db.String(50), nullable=False) 

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class roomTypes(db.Model):
    __bind_key__    = 'OTLC'
    __tablename__   = 'RSTIPOHABITACION'
    TH_CODIGO       = db.Column(db.String(12), nullable=False, primary_key=True)
    TH_CATEGORIA    = db.Column(db.String(50), nullable=False, primary_key=True)
    TH_HOTEL        = db.Column(db.String(12), nullable=False, primary_key=True)
    TH_DESCRIPCION  = db.Column(db.String(50), nullable=False, primary_key=False)
    TH_CAPACIDAD    = db.Column(db.Numeric(), nullable=False, primary_key=False)
    TH_ACTIVO       = db.Column(db.String(1), nullable=False, primary_key=False)
    TH_MAX_ADU      = db.Column(db.Numeric(), primary_key=False)
    TH_MAX_MEN      = db.Column(db.Numeric(), primary_key=False)
    
    def __init__(self, codigo, categoria, hotel, desc, capacidad, activo):
        self.TH_CODIGO      = codigo
        self.TH_CATEGORIA   = categoria
        self.TH_HOTEL       = hotel
        self.TH_DESCRIPCION = desc
        self.TH_CAPACIDAD   = capacidad
        self.TH_ACTIVO      = activo
