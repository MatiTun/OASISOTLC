from flask import Blueprint, request, jsonify, send_file
from app.helpers.api import pagination, JsonResponse
from ...avalon.models.booking import db, BookingsAvalon as av, BookingsDetailAvalon as ada, BookingsGuestAvalon as ca, ValorationAvalon as va,EntitiesAvalon as ea\
                                    ,CommentsAvalon as cma, ImExt, ImpEst, ExchangeAvalon as exa, bookingsOtlc as bo, customers as cu, roomTypes as rt
from app import app
from sqlalchemy import desc, asc, func, case, or_, String, cast, VARCHAR, and_
from datetime import datetime, timedelta
from io import BytesIO
import pandas

arrivals = Blueprint('arrivals', __name__, url_prefix='/otlc/arrivals')

@arrivals.route('/arrivals/<int:page>', methods=['POST'])
@arrivals.route('/arrivals/<int:page>/<int:rows>', methods=['POST'])
def arrivals_Avalon(page=1, rows=10):
    _code = 500
    info = {}
    data = []
    error_message = None

    if request.method == 'POST':
        hotel = request.form.get('hotel', '').strip()
        fechafin = request.form.get('fechafin', '').strip() 
        fechaini = request.form.get('fechaini', '').strip() 
        confirmacion = request.form.get('confirmacion', '').strip()  
        segmento = request.form.get('segmento', '').strip()  
        estado = request.form.get('estado', '').strip()  
        capu = request.form.get('capu', '').strip()
        entidad = request.form.get('entidad', '').strip()
        
        entidades_list = entidad.split(',') if entidad else []
        estados_list = estado.split(',') if estado else []
        clientes_subquery = (
            db.session.query(
                func.string_agg(
                    cast(
                        func.concat(
                            cast(case(
                                (ca.TipoPersona == '0', 'AD'),
                                (ca.TipoPersona == '1', 'JR'),
                                (ca.TipoPersona == '2', 'NI'),
                                (ca.TipoPersona == '3', 'CU'),
                                else_='Other'
                            ), VARCHAR(10)),
                            ',',
                            cast(ca.Edad, VARCHAR(10)), '/ ',
                            cast(ca.Nombre, VARCHAR(100)), ' ',
                            cast(ca.Apellido1, VARCHAR(100)), ' ',
                            cast(ca.Apellido2, VARCHAR(100))
                        ),
                        VARCHAR("MAX")
                    ), cast('|', VARCHAR(1))
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        nombre_subquery = (
            db.session.query(
                func.concat(
                    ca.Nombre, ' ',
                    ca.Apellido1, ' ',
                    ca.Apellido2
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .as_scalar()
        )
        
        valoracion_mxn_subquery = db.session.query(
            func.sum(func.coalesce(va.PrecioFac, 0) 
        )
        ).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).label('Valoracion_mxn')

        externo_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImExt.Importe, 0)
        )
        ).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).label('Externo_mxn')

        estancia_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImpEst.Precio, 0) 
        )
        ).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).label('Estancia_mxn')
        
        moneda_subquery_externa = db.session.query(func.max(ImExt.Divisa)).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).correlate(av).scalar_subquery()
        moneda_subquery_estancia = db.session.query(func.max(ImpEst.Divisa)).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()
        
        moneda_subquery = db.session.query(func.max(va.DivisaFac)).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()



        query = db.session.query(
            av.HotelFactura.label('Hotel'),
            av.Reserva.label('Reserva'),
            av.Linea.label('Linea'),
            av.Bono.label('Bono'),
            av.Estancia.label('Estancia'),
            av.Oferta.label('Oferta'),
            func.format(av.VentaFecha, 'dd/MM/yy').label('venta'),
            func.format(av.SalidaDia, 'dd/MM/yy').label('SalidaEstimada'),
            av.Localizador.label('Localizador'),
            av.Segmento.label('Segmento'),
            av.Entidad.label('Agencia'),
            av.Grupo.label('Grupo'),
            av.Canal.label('Canal'),
            func.format(ada.FechaEntrada, 'dd/MM/yy').label('Entrada'),
            func.format(ada.FechaSalida, 'dd/MM/yy').label('Salida'),
            ada.Noches.label('Nts'),
            case(
                (ada.Estado == 0, 'Reserva'),
                (ada.Estado == 1, 'EnCasa'),
                (ada.Estado == 2, 'Salida'),
                (ada.Estado == 3, 'NoShow'),
                (ada.Estado == 4, 'Cancelada'),
                else_='Desconocido'
            ).label('Estado'),
            ada.AD,
            ada.JR,
            ada.NI,
            ada.CU,
            av.RegimenFactura.label('Regim'),
            ada.Habitacion.label('Habi'),
            av.THFactura.label('th'),
            ada.HotelUso,
            func.coalesce(
                externo_mxn_subquery,
                valoracion_mxn_subquery,
                estancia_mxn_subquery
            ).label('Importe'),
            # ea.DivisaFacturas.label('Moneda'),
            func.coalesce(moneda_subquery_externa, moneda_subquery, moneda_subquery_estancia).label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            av.TextoReserva.label('Comentario'),
            cma.Texto.label('Comentario2'),
            clientes_subquery.label('Clientes'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) , isouter=True
        )
        
        if confirmacion:
            query = query.filter(av.Reserva == confirmacion)
        else:
            if hotel:
                query = query.filter(av.HotelFactura == hotel)
            if fechaini and fechafin:
                query = query.filter(ada.FechaEntrada >= fechaini, ada.FechaEntrada <= fechafin)
            elif fechaini and not fechafin:
                error_message = {'error': 'Debe seleccionar una fecha de fin'}
                return jsonify({'code': 400, 'data': [], 'info': {}, 'msg': error_message})
            if segmento:
                query = query.filter(av.Segmento == segmento)
            if estados_list:
                query = query.filter(ada.Estado.in_(estados_list))
            if capu:
                query = query.filter(av.AltaUsuario == capu)
            if entidades_list: 
                query = query.filter(av.Entidad.in_(entidades_list))

        query = query.filter(ada.Linea != -1).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)

        if request.form.get('excel') == 'true':
            df = pandas.DataFrame([{
                    'Hotel Factura': item.Hotel,
                    'Hotel': item.HotelUso,
                    'Reserva': item.Reserva,
                    'Linea': item.Linea,
                    'Clientes': item.Clientes,
                    'Nombre': item.Nombre,
                    'Localizador': item.Localizador,
                    'Segmento': item.Segmento,
                    'Agencia': item.Agencia,
                    'Grupo': item.Grupo,
                    'Canal': item.Canal,
                    'Entrada': item.Entrada,
                    'Salida': item.Salida,
                    'Nts': item.Nts,
                    'Estado': item.Estado,
                    'Ad': item.AD,
                    'Jr': item.JR,
                    'Ni': item.NI,
                    'Cu': item.CU,
                    'Regim': item.Regim,
                    'Habi': item.Habi,
                    'TH': item.th,
                    'Importe': item.Importe,
                    'Moneda': item.Moneda,
                    'Tarifa': item.Tarifa,
                    'Oferta': item.Oferta,
                    'Bono': item.Bono,
                    'Estancia': item.Estancia,
                    'Salida Estimada': item.SalidaEstimada,
                    'Fecha venta': item.venta,
                    'CapU': item.CapU,
                    'Nac': item.Nac,
                    'Texto': item.Comentario2 if item.Comentario2 else item.Comentario
            } for item in query.all()])
            
            output = BytesIO()
            with pandas.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Llegadas_avalon', index=False)
            output.seek(0)
            return send_file(output, download_name='Llegadas_avalon.xlsx', as_attachment=True, mimetype='application/vnd.ms-excel')
        try:
            data_paginated = query.paginate(page=page, per_page=rows)
            if data_paginated.items:
                info['pagination'] = pagination(data_paginated)
                data = [{
                    'Hotel Factura': item.Hotel,
                    'Hotel': item.HotelUso,
                    'Reserva': item.Reserva,
                    'Linea': item.Linea,
                    'Clientes': item.Clientes,
                    'Nombre': item.Nombre,
                    'Localizador': item.Localizador,
                    'Segmento': item.Segmento,
                    'Agencia': item.Agencia,
                    'Grupo': item.Grupo,
                    'Canal': item.Canal,
                    'Entrada': item.Entrada,
                    'Salida': item.Salida,
                    'Nts': item.Nts,
                    'Estado': item.Estado,
                    'Ad': item.AD,
                    'Jr': item.JR,
                    'Ni': item.NI,
                    'Cu': item.CU,
                    'Regim': item.Regim,
                    'Habi': item.Habi,
                    'TH': item.th,
                    'Importe': item.Importe,
                    'Moneda': item.Moneda,
                    'Tarifa': item.Tarifa,
                    'Oferta': item.Oferta,
                    'Bono': item.Bono,
                    'Estancia': item.Estancia,
                    'Salida Estimada': item.SalidaEstimada,
                    'Fecha venta': item.venta,
                    'CapU': item.CapU,
                    'Nac': item.Nac,
                    'Texto': item.Comentario2 if item.Comentario2 else item.Comentario
                } for item in data_paginated.items]
                _code = 200
            else:
                _code = 404
                error_message = {'info': 'No se encontraron resultados'}
        except Exception as e:
            error_message = {'error': f'Error en la consulta: {str(e)}'}
            _code = 500

        return jsonify({'code': _code, 'data': data, 'info': info, 'msg': error_message})
    
    
@arrivals.route('/segment/search', methods=['GET'])
def segment():
    _code = 500
    ms_error = {'error': 'Error al consultar'}
    try:
        data_segmentos = db.session.query(av.Segmento.label('Segmento')).distinct().all()


        resp = [{'Segmento': item.Segmento} for item in data_segmentos]

        if resp:
            info = {'columns': [{'name': 'Segmento'}]}
            _code = 200
            msg = {'success': 'Consulta exitosa'}
        else:
            info = {}
            msg = {'info': 'No se encontraron segmentos disponibles'}
    except Exception as error:
        msg = {'error': str(error)}
        resp = []
        info = {}

    return jsonify({'code': _code, 'data': resp, 'info': info, 'msg': msg})

@arrivals.route('/user/search', methods=['GET'])
def user():
    _code = 500
    ms_error = {'error': 'Error al consultar usuarios'}
    try:
        data_capu = db.session.query(av.AltaUsuario.label('Capu')).distinct().all()


        resp = [{'Capu': item.Capu} for item in data_capu]

        if resp:
            info = {'columns': [{'name': 'Capu'}]}
            _code = 200
            msg = {'success': 'Consulta exitosa'}
        else:
            info = {}
            msg = {'info': 'No se encontraron usuarios'}
    except Exception as error:
        msg = {'error': str(error)}
        resp = []
        info = {}

    return jsonify({'code': _code, 'data': resp, 'info': info, 'msg': msg})

@arrivals.route('/arrivals2', methods=['POST'])
def llegadas_Avalon(page=1, rows=10):
    _code = 500
    info = {}
    data = []
    error_message = None
    today = datetime.now()
    dosSemanas = (datetime.now() + timedelta(days=15))
    # print(yesterday)
    if request.method == 'POST':
        segmento = 'OTLC' 
        capu = 'WEB'
        
        clientes_subquery = (
            db.session.query(
                func.string_agg(
                    cast(
                        func.concat(
                            cast(case(
                                (ca.TipoPersona == '0', 'AD'),
                                (ca.TipoPersona == '1', 'JR'),
                                (ca.TipoPersona == '2', 'NI'),
                                (ca.TipoPersona == '3', 'CU'),
                                else_='Other'
                            ), VARCHAR(10)),
                            ',',
                            cast(ca.Edad, VARCHAR(10)), '/ ',
                            cast(ca.Nombre, VARCHAR(100)), ' ',
                            cast(ca.Apellido1, VARCHAR(100)), ' ',
                            cast(ca.Apellido2, VARCHAR(100))
                        ),
                        VARCHAR("MAX")
                    ), cast('|', VARCHAR(1))
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        nombre_subquery = (
            db.session.query(
                func.concat(
                    ca.Nombre, ' ',
                    ca.Apellido1, ' ',
                    ca.Apellido2
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .as_scalar()
        )
        
        valoracion_mxn_subquery = db.session.query(
            func.sum(func.coalesce(va.PrecioFac, 0) 
        )
        ).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).label('Valoracion_mxn')

        externo_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImExt.Importe, 0)
        )
        ).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).label('Externo_mxn')

        estancia_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImpEst.Precio, 0),
        )
        ).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).label('Estancia_mxn')
        
        moneda_subquery_externa = db.session.query(func.max(ImExt.Divisa)).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).correlate(av).scalar_subquery()
        moneda_subquery_estancia = db.session.query(func.max(ImpEst.Divisa)).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()
        
        moneda_subquery = db.session.query(func.max(va.DivisaFac)).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery() 


        query = db.session.query(
            av.HotelFactura.label('Hotel'),
            av.Reserva.label('Reserva'),
            av.Linea.label('Linea'),
            av.Bono.label('Bono'),
            av.Estancia.label('Estancia'),
            av.Oferta.label('Oferta'),
            func.format(av.VentaFecha, 'dd/MM/yy').label('venta'),
            func.format(av.SalidaDia, 'dd/MM/yy').label('SalidaEstimada'),
            av.Localizador.label('Localizador'),
            av.Segmento.label('Segmento'),
            av.Entidad.label('Agencia'),
            av.Grupo.label('Grupo'),
            av.Canal.label('Canal'),
            func.format(ada.FechaEntrada, 'dd/MM/yy').label('Entrada'),
            func.format(ada.FechaSalida, 'dd/MM/yy').label('Salida'),
            ada.Noches.label('Nts'),
            case(
                (ada.Estado == 0, 'Reserva'),
                (ada.Estado == 1, 'EnCasa'),
                (ada.Estado == 2, 'Salida'),
                (ada.Estado == 3, 'NoShow'),
                (ada.Estado == 4, 'Cancelada'),
                else_='Desconocido'
            ).label('Estado'),
            ada.AD,
            ada.JR,
            ada.NI,
            ada.CU,
            av.RegimenFactura.label('Regim'),
            ada.Habitacion.label('Habi'),
            av.THFactura.label('th'),
            ada.HotelUso,
            func.coalesce(
                externo_mxn_subquery,
                valoracion_mxn_subquery,
                estancia_mxn_subquery
            ).label('Importe'),
            # ImpEst.Divisa.label('Moneda'),
            func.coalesce(moneda_subquery_externa, moneda_subquery, moneda_subquery_estancia).label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            av.TextoReserva.label('Comentario'),
            clientes_subquery.label('Clientes'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) & (cma.Texto.like('Voucher%')), isouter=True
        )
        # print(yesterday, ada.FechaEntrada)
        
        # query = query.filter(av.Reserva == 'GOPRS240202050')
    
        query = query.filter(
            or_(
                and_(ada.FechaEntrada >= today.date(), ada.FechaEntrada <= dosSemanas)
            ),
            av.Segmento == "OTLC",
            av.AltaUsuario == "WEB",
            ada.Linea != -1
        ).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)

        try:
            results = query.all()
            if results:
                data = [{
                    'Hotel Factura': item.Hotel,
                    'Hotel': item.HotelUso,
                    'Reserva': item.Reserva,
                    'Linea': item.Linea,
                    'Clientes': item.Clientes,
                    'Nombre': item.Nombre,
                    'Localizador': item.Localizador,
                    'Segmento': item.Segmento,
                    'Agencia': item.Agencia,
                    'Grupo': item.Grupo,
                    'Canal': item.Canal,
                    'Entrada': item.Entrada,
                    'Salida': item.Salida,
                    'Nts': item.Nts,
                    'Estado': item.Estado,
                    'Ad': item.AD,
                    'Jr': item.JR,
                    'Ni': item.NI,
                    'Cu': item.CU,
                    'Regim': item.Regim,
                    'Habi': item.Habi,
                    'TH': item.th,
                    'Importe': item.Importe,
                    'Moneda': item.Moneda,
                    'Tarifa': item.Tarifa,
                    'Oferta': item.Oferta,
                    'Bono': item.Bono,
                    'Estancia': item.Estancia,
                    'Salida Estimada': item.SalidaEstimada,
                    'Fecha venta': item.venta,
                    'CapU': item.CapU,
                    'Nac': item.Nac,
                    'Texto': item.Comentario
                } for item in results]
                _code = 200
            else:
                _code = 404
                error_message = {'info': 'No se encontraron resultados'}
        except Exception as e:
            error_message = {'error': f'Error en la consulta: {str(e)}'}
            _code = 500

        return jsonify({'code': _code, 'data': data, 'info': info, 'msg': error_message})
    

@arrivals.route('/reservations/paraty', methods=['POST'])
def reservas_paraty():
    _code = 500
    info = {}
    data = []
    error_message = None
    try:
        data = request.get_json()
        unique_id = data.get('unique_id')
        if not unique_id:
            return jsonify({'error': 'unique_id no proporcionado'}), 400
        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .scalar_subquery()
        )

        nombre_subquery = (
            db.session.query(
                func.concat(
                    ca.Nombre, ' ',
                    ca.Apellido1, ' ',
                    ca.Apellido2
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .scalar_subquery()
        )

        valoracion_mxn_subquery = db.session.query(
            func.sum(func.coalesce(va.PrecioFac, 0))
        ).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).scalar_subquery()

        externo_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImExt.Importe, 0))
        ).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).scalar_subquery()

        estancia_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImpEst.Precio, 0))
        ).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).scalar_subquery()

        moneda_subquery_externa = db.session.query(func.max(ImExt.Divisa)).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery_estancia = db.session.query(func.max(ImpEst.Divisa)).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery = db.session.query(func.max(va.DivisaFac)).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        # Aquí quitamos th_categoria del query principal

        query = db.session.query(
            av.HotelFactura.label('Hotel'),
            av.Reserva.label('Reserva'),
            av.Linea.label('Linea'),
            av.Bono.label('Bono'),
            av.Estancia.label('Estancia'),
            av.Oferta.label('Oferta'),
            av.AltaFecha.label('alta'),
            av.Localizador.label('Localizador'),
            av.Segmento.label('Segmento'),
            av.Entidad.label('Agencia'),
            av.Grupo.label('Grupo'),
            av.Canal.label('Canal'),
            ada.FechaEntrada.label('Entrada'),
            ada.FechaSalida.label('Salida'),
            ada.Noches.label('Nts'),
            case(
                (ada.Estado == 0, 'Reserva'),
                (ada.Estado == 1, 'EnCasa'),
                (ada.Estado == 2, 'Salida'),
                (ada.Estado == 3, 'NoShow'),
                (ada.Estado == 4, 'Cancelada'),
                else_='Desconocido'
            ).label('Estado'),
            ada.AD,
            ada.JR,
            ada.NI,
            ada.CU,
            av.RegimenFactura.label('Regim'),
            ada.Habitacion.label('Habi'),
            av.THFactura.label('th'),
            ada.HotelUso,
            av.Entidad,
            func.coalesce(
                externo_mxn_subquery,
                valoracion_mxn_subquery,
                estancia_mxn_subquery
            ).label('Importe'),
            func.coalesce(moneda_subquery_externa, moneda_subquery, moneda_subquery_estancia).label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            av.TextoReserva.label('Comentario'),
            # cma.Texto.label('Comentario2'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) & (cma.Texto.like('Voucher%')), isouter=True
        ).filter(
            av.Localizador == unique_id,
            ada.Linea != -1
        ).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)
        
        resultados = query.all()
        salida = []
        for item in resultados:
            salida.append({
                'reserva': item.Reserva,
                'linea': item.Linea,
                'localizador': item.Localizador,
                'estado': item.Estado,
                'hotel': item.HotelUso,
                'entrada': str(item.Entrada),
                'salida': str(item.Salida),
                'noches': item.Nts,
                'adultos': item.AD,
                'juniors': item.JR,
                'menores': item.NI,
                'bebes': item.CU,
                'tipo_habitacion': item.th,
                'importe': float(item.Importe) if item.Importe else 0,
                'moneda': item.Moneda,
                'tarifa_desc': item.Tarifa,
                'Texto': item.Comentario,
                # 'Texto': item.Comentario2 if item.Comentario2 else item.Comentario,
                'capu': item.CapU,
                'segmento': item.Segmento,
                'entidad': item.Entidad,
                'nombre': item.Nombre,
                'alta': item.alta
            })
        clientes = db.session.query(
            ca.Reserva, 
            ca.Linea, 
            ca.Numero, 
            ca.Nombre,
            ca.Apellido1,
            ca.Apellido2,
            ca.TipoPersona,
            ca.Edad
        ).join(
            av, (av.Reserva == ca.Reserva) & (av.Linea == ca.Linea)
        ).filter(
            av.Reserva == unique_id,
            av.Linea != -1
        ).order_by(
            ca.Reserva, ca.Linea, ca.Numero
        ).all()

        lista_clientes = []
        for r, l, n, nombre, ap1, ap2, tipo, edad in clientes:
            lista_clientes.append({
                'reserva': r,
                'linea': l,
                'numero': n,
                'nombre': nombre,
                'apellido1': ap1,
                'apellido2': ap2,
                'tipo_persona': tipo,
                'edad': int(edad) if edad else 0
            })

        return jsonify({
            'code': 200,
            'reservas': salida,
            'clientes': lista_clientes
        })

    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Error al consultar: {str(e)}'})


@arrivals.route('/reservations/avalon', methods=['GET'])
def reservas_avalon():
    _code = 500
    info = {}
    data = []
    error_message = None
    
    captura_fecha = datetime.today()
    
    try:
        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .scalar_subquery()
        )

        nombre_subquery = (
            db.session.query(
                func.concat(
                    ca.Nombre, ' ',
                    ca.Apellido1, ' ',
                    ca.Apellido2
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .scalar_subquery()
        )

        valoracion_mxn_subquery = db.session.query(
            func.sum(func.coalesce(va.PrecioFac, 0))
        ).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).scalar_subquery()

        externo_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImExt.Importe, 0))
        ).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).scalar_subquery()

        estancia_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImpEst.Precio, 0))
        ).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).scalar_subquery()

        moneda_subquery_externa = db.session.query(func.max(ImExt.Divisa)).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery_estancia = db.session.query(func.max(ImpEst.Divisa)).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery = db.session.query(func.max(va.DivisaFac)).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        prefijos = ['BPA', 'GPA', 'GOC', 'GOP', 'SPA', 'GBA', 'ZPA', 'GOT']
        query = db.session.query(
            av.HotelFactura.label('Hotel'),
            av.Reserva.label('Reserva'),
            av.Linea.label('Linea'),
            av.Bono.label('Bono'),
            av.Estancia.label('Estancia'),
            av.Oferta.label('Oferta'),
            av.AltaFecha.label('alta'),
            av.Localizador.label('Localizador'),
            av.Segmento.label('Segmento'),
            av.Entidad.label('Agencia'),
            av.Grupo.label('Grupo'),
            av.Canal.label('Canal'),
            ada.FechaEntrada.label('Entrada'),
            ada.FechaSalida.label('Salida'),
            ada.Noches.label('Nts'),
            case(
                (ada.Estado == 0, 'Reserva'),
                (ada.Estado == 1, 'EnCasa'),
                (ada.Estado == 2, 'Salida'),
                (ada.Estado == 3, 'NoShow'),
                (ada.Estado == 4, 'Cancelada'),
                else_='Desconocido'
            ).label('Estado'),
            ada.AD,
            ada.JR,
            ada.NI,
            ada.CU,
            av.RegimenFactura.label('Regim'),
            ada.Habitacion.label('Habi'),
            av.THFactura.label('th'),
            ada.HotelUso,
            av.Entidad,
            func.coalesce(
                externo_mxn_subquery,
                valoracion_mxn_subquery,
                estancia_mxn_subquery
            ).label('Importe'),
            func.coalesce(moneda_subquery_externa, moneda_subquery, moneda_subquery_estancia).label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            av.TextoReserva.label('Comentario'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) & (cma.Texto.like('Voucher%')), isouter=True
        ).filter(
            or_(*[av.Localizador.like(f'{prefix}%') for prefix in prefijos]),
            av.AltaUsuario != 'WEB',
            av.Segmento == 'OTLC',
            av.Linea != -1,
            av.AltaFecha == captura_fecha      
        ).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)
        
        resultados = query.all()
        salida = []
        for item in resultados:
            salida.append({
                'reserva': item.Reserva,
                'linea': item.Linea,
                'localizador': item.Localizador,
                'estado': item.Estado,
                'hotel': item.HotelUso,
                'entrada': str(item.Entrada),
                'salida': str(item.Salida),
                'noches': item.Nts,
                'adultos': item.AD,
                'juniors': item.JR,
                'menores': item.NI,
                'bebes': item.CU,
                'tipo_habitacion': item.th,
                'importe': float(item.Importe) if item.Importe else 0,
                'moneda': item.Moneda,
                'tarifa_desc': item.Tarifa,
                'comentario': item.Comentario,
                'capu': item.CapU,
                'segmento': item.Segmento,
                'entidad': item.Entidad,
                'nombre': item.Nombre,
                'alta': item.alta
            })
        #     clientes = db.session.query(
        #     ca.Reserva, 
        #     ca.Linea, 
        #     ca.Numero, 
        #     ca.Nombre,
        #     ca.Apellido1,
        #     ca.Apellido2,
        #     ca.TipoPersona,
        #     ca.Edad
        # ).join(
        #     av, (av.Reserva == ca.Reserva) & (av.Linea == ca.Linea)
        # ).filter(
        #     av.Reserva == item.Reserva,
        #     av.Linea != -1
        # ).order_by(
        #     ca.Reserva, ca.Linea, ca.Numero
        # ).all()

        # lista_clientes = []
        # for r, l, n, nombre, ap1, ap2, tipo, edad in clientes:
        #     lista_clientes.append({
        #         'reserva': r,
        #         'linea': l,
        #         'numero': n,
        #         'nombre': nombre,
        #         'apellido1': ap1,
        #         'apellido2': ap2,
        #         'tipo_persona': tipo,
        #         'edad': int(edad) if edad else 0
        #     })
       
        return jsonify({
            'code': 200,
            'reservas': salida
        })

    except Exception as e:
        return jsonify({'code': 500, 'msg': f'Error al consultar: {str(e)}'})
    
@arrivals.route('/entidad/search', methods=['GET'])
def entidades():
    _code = 500
    try:
        data_entidad = (
            db.session.query(av.Entidad.label('Entidad'))
            .filter(av.Entidad != None, av.Entidad != '')
            .distinct()
            .order_by(av.Entidad)
            .all()
        )

        resp = [{'Entidad': item.Entidad} for item in data_entidad]

        if resp:
            info = {'columns': [{'name': 'Entidad'}]}
            _code = 200
            msg = {'success': 'Consulta exitosa'}
        else:
            info = {}
            msg = {'info': 'No se encontraron entidades'}

    except Exception as error:
        resp = []
        info = {}
        msg = {'error': str(error)}

    return jsonify({'code': _code, 'data': resp, 'info': info, 'msg': msg})

@arrivals.route('/arrivalsP', methods=['POST'])
def arrivals_AvalonP():
    _code = 500
    info = {}
    data = []
    error_message = None

    if request.method == 'POST':

        fechafin = request.form.get('fechafin', '').strip()
        fechaini = request.form.get('fechaini', '').strip()
        fechafinS = request.form.get('fechafinS', '').strip()
        fechainiS = request.form.get('fechainiS', '').strip()
        confirmacion = request.form.get('confirmacion', '').strip()
        segmento = 'OTLC'
        estado = request.form.get('estado', '').strip()
        capu = request.form.get('capu', '').strip()
        entidad = request.form.get('entidad', '').strip()

        entidades_list = entidad.split(',') if entidad else []
        estados_list = estado.split(',') if estado else []

        clientes_subquery = (
            db.session.query(
                func.string_agg(
                    cast(
                        func.concat(
                            cast(case(
                                (ca.TipoPersona == '0', 'AD'),
                                (ca.TipoPersona == '1', 'JR'),
                                (ca.TipoPersona == '2', 'NI'),
                                (ca.TipoPersona == '3', 'CU'),
                                else_='Other'
                            ), VARCHAR(10)),
                            ',',
                            cast(ca.Edad, VARCHAR(10)), '/ ',
                            cast(ca.Nombre, VARCHAR(100)), ' ',
                            cast(ca.Apellido1, VARCHAR(100)), ' ',
                            cast(ca.Apellido2, VARCHAR(100))
                        ),
                        VARCHAR("MAX")
                    ), cast('|', VARCHAR(1))
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        nombre_subquery = (
            db.session.query(ca.Nombre)
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .as_scalar()
        )

        apellido1_subquery = (
            db.session.query(ca.Apellido1)
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea, ca.Numero == numero_min_subquery)
            .correlate(av)
            .as_scalar()
        )

        valoracion_mxn_subquery = db.session.query(
            func.sum(func.coalesce(va.PrecioFac, 0))
        ).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).label('Valoracion_mxn')

        externo_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImExt.Importe, 0))
        ).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).label('Externo_mxn')

        estancia_mxn_subquery = db.session.query(
            func.sum(func.coalesce(ImpEst.Precio, 0))
        ).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).label('Estancia_mxn')

        moneda_subquery_externa = db.session.query(func.max(ImExt.Divisa)).filter(
            ImExt.Reserva == av.Reserva,
            ImExt.Linea == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery_estancia = db.session.query(func.max(ImpEst.Divisa)).filter(
            ImpEst.Reserva == av.Reserva,
            ImpEst.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        moneda_subquery = db.session.query(func.max(va.DivisaFac)).filter(
            va.Reserva == av.Reserva,
            va.LineaReserva == av.Linea
        ).correlate(av).scalar_subquery()

        # ---- Query principal ----
        query = db.session.query(
            av.HotelFactura.label('Hotel'),
            av.Reserva.label('Reserva'),
            av.Linea.label('Linea'),
            av.Bono.label('Bono'),
            av.Estancia.label('Estancia'),
            av.Oferta.label('Oferta'),
            func.format(av.VentaFecha, 'dd/MM/yy').label('venta'),
            func.format(av.SalidaDia, 'dd/MM/yy').label('SalidaEstimada'),
            av.Localizador.label('Localizador'),
            av.Segmento.label('Segmento'),
            av.Entidad.label('Agencia'),
            av.Grupo.label('Grupo'),
            av.Canal.label('Canal'),
            func.format(ada.FechaEntrada, 'dd/MM/yy').label('Entrada'),
            func.format(ada.FechaSalida, 'dd/MM/yy').label('Salida'),
            ada.Noches.label('Nts'),
            case(
                (ada.Estado == 0, 'Reserva'),
                (ada.Estado == 1, 'EnCasa'),
                (ada.Estado == 2, 'Salida'),
                (ada.Estado == 3, 'NoShow'),
                (ada.Estado == 4, 'Cancelada'),
                else_='Desconocido'
            ).label('Estado'),
            ada.AD,
            ada.JR,
            ada.NI,
            ada.CU,
            av.RegimenFactura.label('Regim'),
            ada.Habitacion.label('Habi'),
            av.THFactura.label('th'),
            ada.HotelUso,
            func.coalesce(
                externo_mxn_subquery,
                valoracion_mxn_subquery,
                estancia_mxn_subquery
            ).label('Importe'),
            func.coalesce(moneda_subquery_externa, moneda_subquery, moneda_subquery_estancia).label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            av.TextoReserva.label('Comentario'),
            cma.Texto.label('Comentario2'),
            clientes_subquery.label('Clientes'),
            nombre_subquery.label('Nombre'),
            apellido1_subquery.label('Apellido')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
             cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) , isouter=True
        )

        # ---- Filtros ----
        if confirmacion:
            query = query.filter(av.Reserva == confirmacion)
        else:
            if fechaini and fechafin:
                query = query.filter(ada.FechaEntrada >= fechaini, ada.FechaEntrada <= fechafin)
            elif fechaini and not fechafin:
                error_message = {'error': 'Debe seleccionar una fecha de fin'}
                return jsonify({'code': 400, 'data': [], 'info': {}, 'msg': error_message})
            if fechainiS and fechafinS:
                query = query.filter(ada.FechaSalida >= fechainiS, ada.FechaSalida <= fechafinS)
            elif fechainiS and not fechafinS:
                error_message = {'error': 'Debe seleccionar una fecha de fin'}
                return jsonify({'code': 400, 'data': [], 'info': {}, 'msg': error_message})
            if segmento:
                query = query.filter(av.Segmento == segmento)
            if estados_list:
                query = query.filter(ada.Estado.in_(estados_list))
            if capu:
                query = query.filter(av.AltaUsuario == capu)
            if entidades_list:
                query = query.filter(av.Entidad.in_(entidades_list))

        query = query.filter(ada.Linea != -1).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)

        try:
            items = query.all()
            if items:
                data = [{
                    'Hotel Factura': item.Hotel,
                    'Hotel': item.HotelUso,
                    'Reserva': item.Reserva,
                    'Linea': item.Linea,
                    'Clientes': item.Clientes,
                    'Nombre': item.Nombre,
                    'Apellido': item.Apellido, 
                    'Localizador': item.Localizador,
                    'Segmento': item.Segmento,
                    'Agencia': item.Agencia,
                    'Grupo': item.Grupo,
                    'Canal': item.Canal,
                    'Entrada': item.Entrada,
                    'Salida': item.Salida,
                    'Nts': item.Nts,
                    'Estado': item.Estado,
                    'Ad': item.AD,
                    'Jr': item.JR,
                    'Ni': item.NI,
                    'Cu': item.CU,
                    'Regim': item.Regim,
                    'Habi': item.Habi,
                    'TH': item.th,
                    'Importe': item.Importe,
                    'Moneda': item.Moneda,
                    'Tarifa': item.Tarifa,
                    'Oferta': item.Oferta,
                    'Bono': item.Bono,
                    'Estancia': item.Estancia,
                    'Salida Estimada': item.SalidaEstimada,
                    'Fecha venta': item.venta,
                    'CapU': item.CapU,
                    'Nac': item.Nac,
                    'Texto': item.Comentario2 if item.Comentario2 else item.Comentario
                } for item in items]
                info['count'] = len(data)
                _code = 200
            else:
                _code = 404
                error_message = {'info': 'No se encontraron resultados'}
        except Exception as e:
            error_message = {'error': f'Error en la consulta: {str(e)}'}
            _code = 500

        return jsonify({'code': _code, 'data': data, 'info': info, 'msg': error_message})
