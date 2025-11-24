from flask import Blueprint, request, jsonify, send_file, Response, current_app
from app.helpers.api import pagination, JsonResponse
from ...avalon.models.booking import db, BookingsAvalon as av, BookingsDetailAvalon as ada, BookingsGuestAvalon as ca, ValorationAvalon as va,EntitiesAvalon as ea\
                                    ,CommentsAvalon as cma, ImExt, ImpEst, ExchangeAvalon as exa, bookingsOtlc as bo, customers as cu, roomTypes as rt
from app import app
from sqlalchemy import desc, asc, func, case, or_, String, cast, VARCHAR, and_
from datetime import datetime, timedelta
from io import BytesIO
import pandas
from sqlalchemy import text, bindparam, Integer
from flask_sqlalchemy import SQLAlchemy
import json
import os
from decimal import Decimal


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
                    ca.Nombre,
                    ca.Apellido1,
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
            cma.Texto.label('Comentario2'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea), isouter=True
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
                'Texto': item.Comentario2,
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



@arrivals.route('/arrivalsMigracion', methods=['POST'])
def arrivals_AvalonMigracion():
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

        # Subquery de clientes
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
                    ),
                    cast('|', VARCHAR(1))
                )
            )
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        # Subquery para obtener el número mínimo y así tomar el "titular"
        numero_min_subquery = (
            db.session.query(func.min(ca.Numero))
            .filter(ca.Reserva == av.Reserva, ca.Linea == av.Linea)
            .correlate(av)
            .as_scalar()
        )

        # Subquery para el nombre del titular
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

        # Importes
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

        # Monedas
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

        # Query base
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
            ada.THUso.label('Uso'),
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
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea), isouter=True
        )

        # Filtros
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

        # Evitar líneas "raras"
        query = query.filter(ada.Linea != -1).order_by(
            av.HotelFactura,
            ada.FechaEntrada,
            av.Reserva,
            av.Linea
        )

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
                    'THUSO': item.Uso,
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
                } for item in results]
                _code = 200
                info = {'total': len(data)}
            else:
                _code = 404
                error_message = {'info': 'No se encontraron resultados'}
        except Exception as e:
            error_message = {'error': f'Error en la consulta: {str(e)}'}
            _code = 500

        return jsonify({'code': _code, 'data': data, 'info': info, 'msg': error_message})

def _normalize_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out

def _ok(data):
    payload = {"code": 200, "data": data, "info": {}, "msg": {}}
    return Response(json.dumps(payload, default=str),
                    mimetype="application/json", status=200)

def _error(code, message):
    payload = {"code": code, "data": [], "info": {}, "msg": {"error": message}}
    return Response(json.dumps(payload, default=str),
                    mimetype="application/json", status=code)

def _normalize_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        else:
            out[k] = v
    return out

def _ok(data):
    payload = {"code": 200, "data": data, "info": {}, "msg": {}}
    return Response(json.dumps(payload, default=str),
                    mimetype="application/json", status=200)

def _error(code, message):
    payload = {"code": code, "data": [], "info": {}, "msg": {"error": message}}
    return Response(json.dumps(payload, default=str),
                    mimetype="application/json", status=code)

from datetime import datetime, timedelta
from flask import request, current_app
from sqlalchemy import text, bindparam

@arrivals.route('/reservas/consulta', methods=['POST'])
def reservas_consulta():
    """
    Body JSON:
    {
      "reservas": ["GOCRS250361721","GOCRS250341882"],
      "hotel": "HT01",                 // o ["HT01","HT02"]
      "segmento": ["WEB","TA"],        // lista
      "estado": [0,1,4],               // número o lista (0..4)
      "fechaEntradaIni": "2025-06-01",
      "fechaEntradaFin": "2025-06-30"
    }
    """
    body = request.get_json(silent=True) or {}

    reservas = body.get("reservas") or []
    hotel = body.get("hotel")
    segmento = body.get("segmento") or []
    estado = body.get("estado")
    fi_raw = body.get("fechaEntradaIni")
    ff_raw = body.get("fechaEntradaFin")

    # === Normalizaciones ===

    # hotel -> lista de hoteles
    if isinstance(hotel, str) and hotel.strip():
        hoteles = [hotel.strip()]
    elif isinstance(hotel, list):
        hoteles = [str(h).strip() for h in hotel if str(h).strip()]
    else:
        hoteles = []

    # segmento -> lista limpia
    if not isinstance(segmento, list):
        segmento = [segmento] if segmento else []
    segmento = [str(s).strip() for s in segmento if str(s).strip()]

    # estado puede venir como int o lista
    if estado is None:
        estados = []
    elif isinstance(estado, list):
        estados = []
        for e in estado:
            try:
                estados.append(int(e))
            except Exception:
                pass
    else:
        try:
            estados = [int(estado)]
        except Exception:
            estados = []

    # Fechas (fin inclusivo): usamos >= ini y < fin+1día
    fi = None
    ff_plus = None
    try:
        if fi_raw:
            fi = datetime.strptime(fi_raw, "%Y-%m-%d")
        if ff_raw:
            ff_plus = datetime.strptime(ff_raw, "%Y-%m-%d") + timedelta(days=1)
    except Exception:
        return _error(400, "Las fechas deben tener formato 'YYYY-MM-DD'.")

    # --- BASE SELECT + CTEs para precios por noche ---
    base_select = r"""
        WITH Filtrado AS (
            SELECT r.Reserva, r.Linea, r.HotelFactura, r.Segmento, rd.Estado,
                rd.FechaEntrada, rd.FechaSalida, r.Oferta
            FROM dbo.RECReservas AS r
            JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
            WHERE 1=1
        ),
        OAS_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_oas
            FROM [AntforHotel-OAS].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        PAN_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_pan_val
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        PAN_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_pan_fac
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        MEX_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_mex_val
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        MEX_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_mex_fac
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        EXT_PRE AS (
            SELECT pe.Reserva, pe.linea AS Linea,
                CONVERT(date, pe.Fecha) AS Fecha,
                SUM(pe.importe) AS monto_ext
            FROM dbo.RECReservasPreciosExterno pe
            JOIN Filtrado f ON f.Reserva = pe.Reserva AND f.Linea = pe.linea
            GROUP BY pe.Reserva, pe.linea, CONVERT(date, pe.Fecha)
        ),
        FECHAS_UNION AS (
            SELECT Reserva, Linea, Fecha FROM OAS_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM EXT_PRE
        )

        SELECT
            r.Reserva, rd.Linea, r.Localizador, r.Entidad, r.EntidadNegocio, r.Grupo,
            r.HotelFactura, r.THFactura, rd.HotelUso, rd.THUso, r.RegimenFactura,
            r.Tarifa, r.Oferta, r.bono,
            CASE 
                WHEN rd.Estado = 0 THEN '0:Activa' 
                WHEN rd.Estado = 1 THEN '1:Check In' 
                WHEN rd.Estado = 2 THEN '2:Check Out' 
                WHEN rd.Estado = 3 THEN '3:No Show' 
                WHEN rd.Estado = 4 THEN '4:Cancel' 
                ELSE NULL 
            END AS Estado,
            r.Segmento, rd.AD, rd.JR, rd.ni, rd.cu,
            (
                SELECT STRING_AGG(
                    rc2.nombre + ' ' + rc2.apellido1 + ISNULL(' ' + rc2.apellido2, ''), ' | '
                )
                FROM [AntforHotel-OAS].dbo.RECReservasClientes rc2
                WHERE rc2.reserva = r.Reserva AND rc2.linea = r.Linea
            ) AS ocupantes,
            (
            SELECT STRING_AGG(
                CAST(rc2.Edad AS VARCHAR(3)), ','
            )
            FROM [AntforHotel-OAS].dbo.RECReservasClientes rc2
            WHERE rc2.reserva = r.Reserva 
            AND rc2.linea = r.Linea
            AND rc2.Edad IS NOT NULL
            ) AS edades,
            ISNULL(NULLIF(rc.Texto, ''), r.TextoReserva) AS Texto,
            rd.FechaEntrada, rd.FechaSalida, r.AltaFecha, r.VentaFecha,
            r.ModificacionFecha, rd.noches, r.Canal, r.AltaUsuario, r.CancelacionUsuario,
            (
                SELECT DISTINCT TOP 1 DivisaFac
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            ) AS divisa,

            -- Totales globales (igual que antes)
            ISNULL((
                SELECT SUM(precioFAC)
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
                GROUP BY Reserva, LineaReserva
            ), (
                SELECT SUM(Precio)
                FROM [AntforHotel-OAS].dbo.PRODetalleEstancia de
                WHERE de.Reserva = r.Reserva AND de.LineaReserva = rd.Linea
                GROUP BY de.Reserva
            )) AS precio_hotel,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_panama,

            (SELECT SUM(importe)
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_panama,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_mexico,

            (SELECT SUM(importe)
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_mexico,

            (SELECT SUM(importe)
            FROM dbo.RECReservasPreciosExterno pe
            WHERE pe.Reserva = r.Reserva AND pe.linea = r.linea
            GROUP BY pe.Reserva, pe.linea) AS precio_externo,

            -- JSON por noche
            (
            SELECT
                fu.Fecha,
                ROUND(
                ISNULL(oas.monto_oas,0) +
                ISNULL(pv.monto_pan_val,0) +
                ISNULL(pf.monto_pan_fac,0) +
                ISNULL(mv.monto_mex_val,0) +
                ISNULL(mf.monto_mex_fac,0) +
                ISNULL(ex.monto_ext,0), 4
                ) AS monto_total,
                ISNULL(oas.monto_oas,0)      AS monto_oas,
                ISNULL(pv.monto_pan_val,0)   AS monto_panama_val,
                ISNULL(pf.monto_pan_fac,0)   AS monto_panama_fac,
                ISNULL(mv.monto_mex_val,0)   AS monto_mexico_val,
                ISNULL(mf.monto_mex_fac,0)   AS monto_mexico_fac,
                ISNULL(ex.monto_ext,0)       AS monto_externo
            FROM FECHAS_UNION fu
            LEFT JOIN OAS_VAL oas ON oas.Reserva = fu.Reserva AND oas.Linea = fu.Linea AND oas.Fecha = fu.Fecha
            LEFT JOIN PAN_VAL pv  ON pv.Reserva  = fu.Reserva AND pv.Linea  = fu.Linea AND pv.Fecha  = fu.Fecha
            LEFT JOIN PAN_FAC pf  ON pf.Reserva  = fu.Reserva AND pf.Linea  = fu.Linea AND pf.Fecha  = fu.Fecha
            LEFT JOIN MEX_VAL mv  ON mv.Reserva  = fu.Reserva AND mv.Linea  = fu.Linea AND mv.Fecha  = fu.Fecha
            LEFT JOIN MEX_FAC mf  ON mf.Reserva  = fu.Reserva AND mf.Linea  = fu.Linea AND mf.Fecha  = fu.Fecha
            LEFT JOIN EXT_PRE ex  ON ex.Reserva  = fu.Reserva AND ex.Linea  = fu.Linea AND ex.Fecha  = fu.Fecha
            WHERE fu.Reserva = r.Reserva AND fu.Linea = rd.Linea
            ORDER BY fu.Fecha
            FOR JSON PATH
            ) AS precio_por_noche_json

        FROM dbo.RECReservas AS r
        JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
        LEFT JOIN dbo.RECReservasComentarios rc
            ON rc.Reserva = r.Reserva AND rc.Linea = r.Linea
    """

    # === WHERE dinámico ===
    where_clauses = ["1=1"]
    params = {}
    bind_list = []

    # Excluir localizadores de grupo/bonos/etc.
    where_clauses.append(
        "(r.Localizador NOT LIKE 'G-%' "
        "AND r.Localizador NOT LIKE 'B-%' "
        "AND r.Localizador NOT LIKE 'FT-%')"
    )
    where_clauses.append("rd.Estado <> 4")

    if isinstance(reservas, list) and reservas:
        where_clauses.append("r.Reserva IN :reservas")
        params["reservas"] = reservas
        bind_list.append(bindparam("reservas", expanding=True))

    if hoteles:
        where_clauses.append("r.HotelFactura IN :hoteles")
        params["hoteles"] = hoteles
        bind_list.append(bindparam("hoteles", expanding=True))

    if segmento:
        where_clauses.append("r.Segmento IN :segmento")
        params["segmento"] = segmento
        bind_list.append(bindparam("segmento", expanding=True))

    if estados:
        where_clauses.append("rd.Estado IN :estados")
        params["estados"] = estados
        bind_list.append(bindparam("estados", expanding=True))

    if fi is not None:
        where_clauses.append("rd.FechaEntrada >= :fi")
        params["fi"] = fi

    if ff_plus is not None:
        # fin inclusivo: < fecha_fin + 1 día
        where_clauses.append("rd.FechaEntrada < :ff_plus")
        params["ff_plus"] = ff_plus

    # Igual que en tu COUNT(*)
    where_clauses.append("r.Linea > 0")

    sql_text = base_select + "\nWHERE " + " AND ".join(where_clauses) + """
        ORDER BY rd.FechaEntrada, r.Reserva, rd.Linea;
    """

    sql = text(sql_text)
    if bind_list:
        sql = sql.bindparams(*bind_list)

    try:
        engine = db.get_engine(current_app, bind="AVALON")
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()

        def _parse_json_field(v):
            if v is None:
                return []
            if isinstance(v, (bytes, bytearray)):
                v = v.decode("utf-8", errors="ignore")
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return v

        data = []
        for r in rows:
            d = dict(r)
            # Parsear el JSON por noche
            d["precio_por_noche"] = _parse_json_field(d.pop("precio_por_noche_json", None))
            data.append(_normalize_row(d))

        return _ok(data)
    except Exception as e:
        return _error(500, f"Error en la consulta: {e}")


@arrivals.route('/grupos/consulta', methods=['POST'])
def grupos_consulta():
    """
    Body JSON:
    {
      "reservas": ["GOCRS250361721","GOCRS250341882"],
      "hotel": "HT01",                 // o ["HT01","HT02"]
      "segmento": ["WEB","TA"],        // lista
      "estado": [0,1,4],               // número o lista (0..4)
      "fechaEntradaIni": "2025-06-01",
      "fechaEntradaFin": "2025-06-30"
    }
    """
    body = request.get_json(silent=True) or {}

    reservas = body.get("reservas") or []
    hotel = body.get("hotel")
    segmento = body.get("segmento") or []
    estado = body.get("estado")
    fi_raw = body.get("fechaEntradaIni")
    ff_raw = body.get("fechaEntradaFin")

    # Normalizaciones
    if isinstance(hotel, str) and hotel.strip():
        hoteles = [hotel.strip()]
    elif isinstance(hotel, list):
        hoteles = [str(h).strip() for h in hotel if str(h).strip()]
    else:
        hoteles = []

    if not isinstance(segmento, list):
        segmento = [segmento] if segmento else []
    segmento = [str(s).strip() for s in segmento if str(s).strip()]

    # estado puede venir como int o lista
    if estado is None:
        estados = []
    elif isinstance(estado, list):
        estados = []
        for e in estado:
            try:
                estados.append(int(e))
            except Exception:
                pass
    else:
        try:
            estados = [int(estado)]
        except Exception:
            estados = []

    # Fechas (inclusive): usamos >= ini y < fin+1día
    fi = None
    ff_plus = None
    try:
        if fi_raw:
            fi = datetime.strptime(fi_raw, "%Y-%m-%d")
        if ff_raw:
            ff_plus = datetime.strptime(ff_raw, "%Y-%m-%d") + timedelta(days=1)
    except Exception:
        return _error(400, "Las fechas deben tener formato 'YYYY-MM-DD'.")

    # --- BASE SELECT + CTEs para precios por noche ---
    
    base_select = r"""
        WITH Filtrado AS (
            SELECT r.Reserva, r.Linea, r.HotelFactura, r.Segmento, rd.Estado,
                rd.FechaEntrada, rd.FechaSalida, r.Oferta
            FROM dbo.RECReservas AS r
            JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
            WHERE 1=1 
        ),
        OAS_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_oas
            FROM [AntforHotel-OAS].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        PAN_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_pan_val
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        PAN_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_pan_fac
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        MEX_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_mex_val
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        MEX_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_mex_fac
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        EXT_PRE AS (
            SELECT pe.Reserva, pe.linea AS Linea,
                CONVERT(date, pe.Fecha) AS Fecha,
                SUM(pe.importe) AS monto_ext
            FROM dbo.RECReservasPreciosExterno pe
            JOIN Filtrado f ON f.Reserva = pe.Reserva AND f.Linea = pe.linea
            GROUP BY pe.Reserva, pe.linea, CONVERT(date, pe.Fecha)
        ),
        FECHAS_UNION AS (
            SELECT Reserva, Linea, Fecha FROM OAS_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM EXT_PRE
        )

        SELECT
            r.Reserva, rd.Linea, r.Localizador, r.Entidad, r.EntidadNegocio, r.Grupo,
            r.HotelFactura, r.THFactura, rd.HotelUso, rd.THUso, r.RegimenFactura,
            r.Tarifa, r.Oferta, r.bono,r.NombreContacto,
            CASE 
                WHEN rd.Estado = 0 THEN '0:Activa' 
                WHEN rd.Estado = 1 THEN '1:Check In' 
                WHEN rd.Estado = 2 THEN '2:Check Out' 
                WHEN rd.Estado = 3 THEN '3:No Show' 
                WHEN rd.Estado = 4 THEN '4:Cancel' 
                ELSE NULL 
            END AS Estado,
            r.Segmento, rd.AD, rd.JR, rd.ni, rd.cu,
            (
                SELECT STRING_AGG(
                    rc.nombre + ' ' + rc.apellido1 + ISNULL(' ' + rc.apellido2, ''), ' | '
                )
                FROM [AntforHotel-OAS].dbo.RECReservasClientes rc
                WHERE rc.reserva = r.Reserva AND rc.linea = r.Linea
            ) AS ocupantes,
            (
                SELECT STRING_AGG(
                    CAST(rc2.Edad AS VARCHAR(3)), ','
                )
                FROM [AntforHotel-OAS].dbo.RECReservasClientes rc2
                WHERE rc2.reserva = r.Reserva 
                AND rc2.linea = r.Linea
                AND rc2.Edad IS NOT NULL
            ) AS edades,
            ISNULL(NULLIF(rc.Texto, ''), r.TextoReserva) AS Texto,
            rd.FechaEntrada, rd.FechaSalida, r.AltaFecha, r.VentaFecha,
            r.ModificacionFecha, rd.noches, r.Canal, r.AltaUsuario, r.CancelacionUsuario,
            (
                SELECT DISTINCT TOP 1 DivisaFac
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            ) AS divisa,

            -- Totales globales (igual que antes)
            ISNULL((
                SELECT SUM(precioFAC)
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
                GROUP BY Reserva, LineaReserva
            ), (
                SELECT SUM(Precio)
                FROM [AntforHotel-OAS].dbo.PRODetalleEstancia de
                WHERE de.Reserva = r.Reserva AND de.LineaReserva = rd.Linea
                GROUP BY de.Reserva
            )) AS precio_hotel,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_panama,

            (SELECT SUM(importe)
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_panama,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_mexico,

            (SELECT SUM(importe)
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_mexico,

            (SELECT SUM(importe)
            FROM dbo.RECReservasPreciosExterno pe
            WHERE pe.Reserva = r.Reserva AND pe.linea = r.linea
            GROUP BY pe.Reserva, pe.linea) AS precio_externo,

            -- JSON por noche
            (
            SELECT
                fu.Fecha,
                ROUND(
                ISNULL(oas.monto_oas,0) +
                ISNULL(pv.monto_pan_val,0) +
                ISNULL(pf.monto_pan_fac,0) +
                ISNULL(mv.monto_mex_val,0) +
                ISNULL(mf.monto_mex_fac,0) +
                ISNULL(ex.monto_ext,0), 4
                ) AS monto_total,
                ISNULL(oas.monto_oas,0)      AS monto_oas,
                ISNULL(pv.monto_pan_val,0)   AS monto_panama_val,
                ISNULL(pf.monto_pan_fac,0)   AS monto_panama_fac,
                ISNULL(mv.monto_mex_val,0)   AS monto_mexico_val,
                ISNULL(mf.monto_mex_fac,0)   AS monto_mexico_fac,
                ISNULL(ex.monto_ext,0)       AS monto_externo
            FROM FECHAS_UNION fu
            LEFT JOIN OAS_VAL oas ON oas.Reserva = fu.Reserva AND oas.Linea = fu.Linea AND oas.Fecha = fu.Fecha
            LEFT JOIN PAN_VAL pv  ON pv.Reserva  = fu.Reserva AND pv.Linea  = fu.Linea AND pv.Fecha  = fu.Fecha
            LEFT JOIN PAN_FAC pf  ON pf.Reserva  = fu.Reserva AND pf.Linea  = fu.Linea AND pf.Fecha  = fu.Fecha
            LEFT JOIN MEX_VAL mv  ON mv.Reserva  = fu.Reserva AND mv.Linea  = fu.Linea AND mv.Fecha  = fu.Fecha
            LEFT JOIN MEX_FAC mf  ON mf.Reserva  = fu.Reserva AND mf.Linea  = fu.Linea AND mf.Fecha  = fu.Fecha
            LEFT JOIN EXT_PRE ex  ON ex.Reserva  = fu.Reserva AND ex.Linea  = fu.Linea AND ex.Fecha  = fu.Fecha
            WHERE fu.Reserva = r.Reserva AND fu.Linea = rd.Linea
            ORDER BY fu.Fecha
            FOR JSON PATH
            ) AS precio_por_noche_json

        FROM dbo.RECReservas AS r
        JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
        LEFT JOIN dbo.RECReservasComentarios rc
            ON rc.Reserva = r.Reserva AND rc.Linea = r.Linea
    """

    # WHERE dinámico
    where_clauses = ["1=1"]
    params = {}
    bind_list = []
    where_clauses.append("(r.Localizador LIKE 'G-%' OR r.Localizador LIKE 'B-%' OR r.Localizador LIKE 'FT-%')")


    if isinstance(reservas, list) and reservas:
        where_clauses.append("r.Reserva IN :reservas")
        params["reservas"] = reservas
        bind_list.append(bindparam("reservas", expanding=True))

    if hoteles:
        where_clauses.append("rd.HotelUso IN :hoteles")
        params["hoteles"] = hoteles
        bind_list.append(bindparam("hoteles", expanding=True))

    if segmento:
        where_clauses.append("r.Segmento IN :segmento")
        params["segmento"] = segmento
        bind_list.append(bindparam("segmento", expanding=True))

    if estados:
        where_clauses.append("rd.Estado IN :estados")
        params["estados"] = estados
        bind_list.append(bindparam("estados", expanding=True))

    if fi is not None:
        where_clauses.append("rd.FechaEntrada >= :fi")
        params["fi"] = fi

    if ff_plus is not None:
        where_clauses.append("rd.FechaEntrada < :ff_plus")
        params["ff_plus"] = ff_plus

    sql_text = base_select + "\nWHERE " + " AND ".join(where_clauses) + """
        ORDER BY rd.FechaEntrada, r.Reserva, rd.Linea;
    """

    sql = text(sql_text)
    if bind_list:
        sql = sql.bindparams(*bind_list)

    try:
        engine = db.get_engine(current_app, bind="AVALON")
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()

        def _parse_json_field(v):
            if v is None:
                return []
            if isinstance(v, (bytes, bytearray)):
                v = v.decode("utf-8", errors="ignore")
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return v

        data = []
        for r in rows:
            d = dict(r)
            # Parsear el JSON por noche
            d["precio_por_noche"] = _parse_json_field(d.pop("precio_por_noche_json", None))
            data.append(_normalize_row(d))

        return _ok(data)

    except Exception as e:
        return _error(500, f"Error en la consulta: {e}")
    
    
@arrivals.route('/casa/consulta', methods=['POST'])
def casa_consulta():
    """
    Body JSON:
    {
      "reservas": ["GOCRS250361721","GOCRS250341882"],
      "hotel": "HT01",                 // o ["HT01","HT02"]
      "segmento": ["WEB","TA"],        // lista
      "estado": [0,1,4],               // número o lista (0..4)
      "fechaEntradaIni": "2025-06-01",
      "fechaEntradaFin": "2025-06-30"
    }
    """
    body = request.get_json(silent=True) or {}

    reservas = body.get("reservas") or []
    hotel = body.get("hotel")
    segmento = body.get("segmento") or []
    estado = body.get("estado")
    fi_raw = body.get("fechaEntradaIni")
    ff_raw = body.get("fechaEntradaFin")

    # Normalizaciones
    if isinstance(hotel, str) and hotel.strip():
        hoteles = [hotel.strip()]
    elif isinstance(hotel, list):
        hoteles = [str(h).strip() for h in hotel if str(h).strip()]
    else:
        hoteles = []

    if not isinstance(segmento, list):
        segmento = [segmento] if segmento else []
    segmento = [str(s).strip() for s in segmento if str(s).strip()]

    # estado puede venir como int o lista
    if estado is None:
        estados = []
    elif isinstance(estado, list):
        estados = []
        for e in estado:
            try:
                estados.append(int(e))
            except Exception:
                pass
    else:
        try:
            estados = [int(estado)]
        except Exception:
            estados = []

    # Fechas (inclusive): usamos >= ini y < fin+1día
    fi = None
    ff_plus = None
    try:
        if fi_raw:
            fi = datetime.strptime(fi_raw, "%Y-%m-%d")
        if ff_raw:
            ff_plus = datetime.strptime(ff_raw, "%Y-%m-%d") + timedelta(days=1)
    except Exception:
        return _error(400, "Las fechas deben tener formato 'YYYY-MM-DD'.")

    # --- BASE SELECT + CTEs para precios por noche ---
    
    base_select = r"""
        WITH Filtrado AS (
            SELECT r.Reserva, r.Linea, r.HotelFactura, r.Segmento, rd.Estado,
                rd.FechaEntrada, rd.FechaSalida, r.Oferta
            FROM dbo.RECReservas AS r
            JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
            WHERE 1=1 
        ),
        OAS_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_oas
            FROM [AntforHotel-OAS].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        PAN_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_pan_val
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        PAN_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_pan_fac
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        MEX_VAL AS (
            SELECT rv.Reserva, rv.LineaReserva AS Linea,
                CONVERT(date, rv.Fecha) AS Fecha,
                SUM(rv.precioFAC) AS monto_mex_val
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion rv
            JOIN Filtrado f ON f.Reserva = rv.Reserva AND f.Linea = rv.LineaReserva
            GROUP BY rv.Reserva, rv.LineaReserva, CONVERT(date, rv.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        MEX_FAC AS (
            SELECT fd.Reserva, fd.LineaReserva AS Linea,
                CONVERT(date, fd.Fecha) AS Fecha,
                SUM(fd.importe) AS monto_mex_fac
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle fd
            JOIN Filtrado f ON f.Reserva = fd.Reserva AND f.Linea = fd.LineaReserva
            GROUP BY fd.Reserva, fd.LineaReserva, CONVERT(date, fd.Fecha)
        ),
        -- SIN cantidad: usar solo importe
        EXT_PRE AS (
            SELECT pe.Reserva, pe.linea AS Linea,
                CONVERT(date, pe.Fecha) AS Fecha,
                SUM(pe.importe) AS monto_ext
            FROM dbo.RECReservasPreciosExterno pe
            JOIN Filtrado f ON f.Reserva = pe.Reserva AND f.Linea = pe.linea
            GROUP BY pe.Reserva, pe.linea, CONVERT(date, pe.Fecha)
        ),
        FECHAS_UNION AS (
            SELECT Reserva, Linea, Fecha FROM OAS_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM PAN_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_VAL
            UNION
            SELECT Reserva, Linea, Fecha FROM MEX_FAC
            UNION
            SELECT Reserva, Linea, Fecha FROM EXT_PRE
        )

        SELECT
            r.Reserva, rd.Linea, r.Localizador, r.Entidad, r.EntidadNegocio, r.Grupo,
            r.HotelFactura, r.THFactura, rd.HotelUso, rd.THUso, r.RegimenFactura,
            r.Tarifa, r.Oferta, r.bono,r.NombreContacto,
            CASE 
                WHEN rd.Estado = 0 THEN '0:Activa' 
                WHEN rd.Estado = 1 THEN '1:Check In' 
                WHEN rd.Estado = 2 THEN '2:Check Out' 
                WHEN rd.Estado = 3 THEN '3:No Show' 
                WHEN rd.Estado = 4 THEN '4:Cancel' 
                ELSE NULL 
            END AS Estado,
            r.Segmento, rd.AD, rd.JR, rd.ni, rd.cu,
            (
                SELECT STRING_AGG(
                    rc.nombre + ' ' + rc.apellido1 + ISNULL(' ' + rc.apellido2, ''), ' | '
                )
                FROM [AntforHotel-OAS].dbo.RECReservasClientes rc
                WHERE rc.reserva = r.Reserva AND rc.linea = r.Linea
            ) AS ocupantes,
            (
                SELECT STRING_AGG(
                    CAST(rc2.Edad AS VARCHAR(3)), ','
                )
                FROM [AntforHotel-OAS].dbo.RECReservasClientes rc2
                WHERE rc2.reserva = r.Reserva 
                AND rc2.linea = r.Linea
                AND rc2.Edad IS NOT NULL
            ) AS edades,
            ISNULL(NULLIF(rc.Texto, ''), r.TextoReserva) AS Texto,
            rd.FechaEntrada, rd.FechaSalida, r.AltaFecha, r.VentaFecha,
            r.ModificacionFecha, rd.noches, r.Canal, r.AltaUsuario, r.CancelacionUsuario,
            (
                SELECT DISTINCT TOP 1 DivisaFac
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            ) AS divisa,

            -- Totales globales (igual que antes)
            ISNULL((
                SELECT SUM(precioFAC)
                FROM [AntforHotel-OAS].dbo.RECReservasValoracion
                WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
                GROUP BY Reserva, LineaReserva
            ), (
                SELECT SUM(Precio)
                FROM [AntforHotel-OAS].dbo.PRODetalleEstancia de
                WHERE de.Reserva = r.Reserva AND de.LineaReserva = rd.Linea
                GROUP BY de.Reserva
            )) AS precio_hotel,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-PANAMA].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_panama,

            (SELECT SUM(importe)
            FROM [AntforHotel-PANAMA].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_panama,

            (SELECT SUM(precioFAC)
            FROM [AntforHotel-MEXICO].dbo.RECReservasValoracion
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea
            GROUP BY Reserva, LineaReserva) AS precio_mexico,

            (SELECT SUM(importe)
            FROM [AntforHotel-MEXICO].dbo.FACFacturasDetalle
            WHERE Reserva = r.Reserva AND LineaReserva = rd.Linea) AS precio_fac_mexico,

            (SELECT SUM(importe)
            FROM dbo.RECReservasPreciosExterno pe
            WHERE pe.Reserva = r.Reserva AND pe.linea = r.linea
            GROUP BY pe.Reserva, pe.linea) AS precio_externo,

            -- JSON por noche
            (
            SELECT
                fu.Fecha,
                ROUND(
                ISNULL(oas.monto_oas,0) +
                ISNULL(pv.monto_pan_val,0) +
                ISNULL(pf.monto_pan_fac,0) +
                ISNULL(mv.monto_mex_val,0) +
                ISNULL(mf.monto_mex_fac,0) +
                ISNULL(ex.monto_ext,0), 4
                ) AS monto_total,
                ISNULL(oas.monto_oas,0)      AS monto_oas,
                ISNULL(pv.monto_pan_val,0)   AS monto_panama_val,
                ISNULL(pf.monto_pan_fac,0)   AS monto_panama_fac,
                ISNULL(mv.monto_mex_val,0)   AS monto_mexico_val,
                ISNULL(mf.monto_mex_fac,0)   AS monto_mexico_fac,
                ISNULL(ex.monto_ext,0)       AS monto_externo
            FROM FECHAS_UNION fu
            LEFT JOIN OAS_VAL oas ON oas.Reserva = fu.Reserva AND oas.Linea = fu.Linea AND oas.Fecha = fu.Fecha
            LEFT JOIN PAN_VAL pv  ON pv.Reserva  = fu.Reserva AND pv.Linea  = fu.Linea AND pv.Fecha  = fu.Fecha
            LEFT JOIN PAN_FAC pf  ON pf.Reserva  = fu.Reserva AND pf.Linea  = fu.Linea AND pf.Fecha  = fu.Fecha
            LEFT JOIN MEX_VAL mv  ON mv.Reserva  = fu.Reserva AND mv.Linea  = fu.Linea AND mv.Fecha  = fu.Fecha
            LEFT JOIN MEX_FAC mf  ON mf.Reserva  = fu.Reserva AND mf.Linea  = fu.Linea AND mf.Fecha  = fu.Fecha
            LEFT JOIN EXT_PRE ex  ON ex.Reserva  = fu.Reserva AND ex.Linea  = fu.Linea AND ex.Fecha  = fu.Fecha
            WHERE fu.Reserva = r.Reserva AND fu.Linea = rd.Linea AND fu.Fecha >= '2025-11-24'
            ORDER BY fu.Fecha
            FOR JSON PATH
            ) AS precio_por_noche_json

        FROM dbo.RECReservas AS r
        JOIN dbo.RECReservasDetalle AS rd
            ON r.Reserva = rd.Reserva AND rd.Linea = r.Linea
        LEFT JOIN dbo.RECReservasComentarios rc
            ON rc.Reserva = r.Reserva AND rc.Linea = r.Linea
    """

    # WHERE dinámico
    where_clauses = ["1=1"]
    params = {}
    bind_list = []
    where_clauses.append("(rd.FechaSalida > '2025-11-24')")

    if isinstance(reservas, list) and reservas:
        where_clauses.append("r.Reserva IN :reservas")
        params["reservas"] = reservas
        bind_list.append(bindparam("reservas", expanding=True))

    if hoteles:
        where_clauses.append("r.HotelFactura IN :hoteles")
        params["hoteles"] = hoteles
        bind_list.append(bindparam("hoteles", expanding=True))

    if segmento:
        where_clauses.append("r.Segmento IN :segmento")
        params["segmento"] = segmento
        bind_list.append(bindparam("segmento", expanding=True))

    if estados:
        where_clauses.append("rd.Estado IN :estados")
        params["estados"] = estados
        bind_list.append(bindparam("estados", expanding=True))

    if fi is not None:
        where_clauses.append("rd.FechaEntrada >= :fi")
        params["fi"] = fi

    if ff_plus is not None:
        where_clauses.append("rd.FechaEntrada < :ff_plus")
        params["ff_plus"] = ff_plus

    sql_text = base_select + "\nWHERE " + " AND ".join(where_clauses) + """
        ORDER BY rd.FechaEntrada, r.Reserva, rd.Linea;
    """

    sql = text(sql_text)
    if bind_list:
        sql = sql.bindparams(*bind_list)

    try:
        engine = db.get_engine(current_app, bind="AVALON")
        with engine.connect() as conn:
            rows = conn.execute(sql, params).mappings().all()

        def _parse_json_field(v):
            if v is None:
                return []
            if isinstance(v, (bytes, bytearray)):
                v = v.decode("utf-8", errors="ignore")
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return v

        data = []
        for r in rows:
            d = dict(r)
            # Parsear el JSON por noche
            d["precio_por_noche"] = _parse_json_field(d.pop("precio_por_noche_json", None))
            data.append(_normalize_row(d))

        return _ok(data)

    except Exception as e:
        return _error(500, f"Error en la consulta: {e}")
