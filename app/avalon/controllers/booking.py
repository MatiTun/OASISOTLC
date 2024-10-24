from flask import Blueprint, request, jsonify, send_file
from app.herpers.api import pagination, JsonResponse
from ...avalon.models.booking import db, BookingsAvalon as av, BookingsDetailAvalon as ada, BookingsGuestAvalon as ca, ValorationAvalon as va,EntitiesAvalon as ea\
                                    ,CommentsAvalon as cma
from app import app
from sqlalchemy import desc, asc, func, case, String, cast, VARCHAR
from datetime import datetime
from io import BytesIO
import pandas

arrivals = Blueprint('arrivals', __name__, url_prefix='/otlc/arrivals')

@arrivals.route('/arrivals/<int:page>', methods=['POST'])
@arrivals.route('/arrivals/<int:page>/<int:rows>', methods=['POST'])
def arrivals_Avalon(page=1, rows=10):
    error_message = {'error': 'Error al consultar'}
    _code = 500
    info = {}
    data = []

    if request.method == 'POST':
        hotel = request.form.get('hotel', '').strip()
        fechafin = request.form.get('fechafin', '').strip() 
        fechaini = request.form.get('fechaini', '').strip() 
        confirmacion = request.form.get('confirmacion', '').strip()  
        segmento = request.form.get('segmento', '').strip()  
        estado = request.form.get('estado', '').strip()  
        
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
            db.session.query(
                func.sum(
                    func.coalesce(va.PrecioFac, 0)
                )
            ).filter(
                va.Reserva == av.Reserva,
                va.LineaReserva == av.Linea
            ).label('Valoracion'),
            ea.DivisaFacturas.label('Moneda'),
            av.Tarifa,
            av.AltaUsuario.label('CapU'),
            func.coalesce(av.Nacionalidad, func.substring(av.Segmento, 1, 3)).label('Nac'),
            cma.Texto.label('Comentario'),
            clientes_subquery.label('Clientes'),
            nombre_subquery.label('Nombre')
        ).join(
            ada, (ada.Reserva == av.Reserva) & (ada.Linea == av.Linea), isouter=True
        ).join(
            ea, ea.Entidad == av.Entidad, isouter=True
        ).join(
            cma, (cma.Reserva == av.Reserva) & (cma.Linea == av.Linea) & (cma.Texto.like('Voucher%')), isouter=True
        )
        
        if hotel:
            query = query.filter(av.HotelFactura == hotel)
        
        if fechaini and fechafin:
            query = query.filter(ada.FechaEntrada >= fechaini, ada.FechaEntrada <= fechafin)
        elif fechaini and not fechafin:
            error_message = {'error': 'Debe seleccionar una fecha de fin'}
            return jsonify({'code': 400, 'data': [], 'info': {}, 'msg': error_message})
        
        if confirmacion:
            query = query.filter(av.Reserva == confirmacion)
        if segmento:
            query = query.filter(av.Segmento == segmento)
        if estados_list:
            query = query.filter(ada.Estado.in_(estados_list))

        query = query.filter(ada.Linea != -1).order_by(av.HotelFactura, ada.FechaEntrada, av.Reserva, av.Linea)

        if 'excel' in request.form:
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
                    'Importe': item.Valoracion,
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
                    'Importe': item.Valoracion,
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
                } for item in data_paginated.items]
                _code = 200
            else:
                _code = 404
        except Exception as e:
            error_message = {'error': f'Error en la consulta: {str(e)}'}
            _code = 500

        return jsonify({'code': _code, 'data': data, 'info': info, 'msg': error_message})
