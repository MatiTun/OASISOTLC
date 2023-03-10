from app import app
from flask import request, jsonify
from flask import Blueprint
from ..models.contract import Contract, Movement, AccountStatusHeader, AccountStatusBody, db
from sqlalchemy.sql.expression import func
from app.herpers.api import JsonResponse
from datetime import datetime, timedelta

otlc  = Blueprint("otlc", __name__, url_prefix='/otlc')

@otlc.route('/contract/information/<contrato>/get', methods=['GET'])
def contratct_information__otlc(contrato):
    response_data = {}
    try:
        reporte = request.args.get('Reporte',False)
        resp = []
        objt_g = {}
        objt_f = {}
        fecha_hoy = datetime.today()
        today_f = datetime.now()
        format_sesion = today_f.strftime("%d%m%y%H%M")

        if reporte:
            # estado de cuenta
            resp_detalle = []
            data_totales = []
            try:
                engine = db.get_engine(bind_key='OTLC')
                connection = engine.raw_connection()
                cursor = connection.cursor()
                #genera_edocta ('1454',Trunc(sysdate),'OTLC','15','B','OSG-2028');
                estado_cuenta = cursor.callproc("GENERA_EDOCTA",[format_sesion,fecha_hoy,'OTLC','15','B',contrato])
                print('estado_cuenta', estado_cuenta)
            except Exception as error:
                print('Error al generar información genera_edocta {}'.format(error))

            detalle = AccountStatusBody.query.filter(AccountStatusBody.ED_CONTRATO==contrato,AccountStatusBody.ED_SESION==format_sesion).order_by(AccountStatusBody.ED_SECUENCIA).all()            
            capital, interes, total, totalp, saldo = 0, 0, 0, 0, 0
            for item in detalle:
                objt_detalle = {}
                item = item.as_dict()
                if item['Saldo Mes'] is None:
                        item['Saldo Mes'] = 0
                for x in item.keys():
                    if x not in ['ED_SESION','ED_FECHA_GEN','ED_USUARIO','ED_CONTRATO','ED_SECUENCIA','ED_FORMATO']:
                        if item[x] is None:
                            objt_detalle[x] = ""
                        else:
                            objt_detalle[x] = item[x]
                if 'Capital' in item:
                    capital += item['Capital']
                if 'Interes' in item:
                    interes += item['Interes']
                if 'Total' in item:
                    total += item['Total']
                if 'Total Pagado' in item:
                    totalp += item['Total Pagado']
                if 'Saldo Mes' in item:
                    saldo += item['Saldo Mes']
                resp_detalle.append(objt_detalle)
            data_totales.append({
                'Capital': capital,
                'Interes': interes,
                'Total': total,
                'Total Pagado': totalp,
                'Saldo Mes': saldo
            })
            encabezado = AccountStatusHeader.query.filter(AccountStatusHeader.EE_CONTRATO==contrato,AccountStatusHeader.EE_SESION==format_sesion).all()
            for item in encabezado:
                objt = {}
                item = item.as_dict()
                print('item', item)
                for x in item.keys():
                    if x not in ['Fecha','Usuario','EE_TIPO','EE_SESION']:
                        if x not in ['Contrato','Socio1','Socio2','Moneda','EE_TASA_INTERES','EE_PM_INICIAL','EE_PM_PAGADO','EE_PM_SALDO']:
                            objt[x] = round(item[x],2) #'{:,.2f}'.format(item[x])
                        else:
                            objt[x] = item[x]
                fecha = item['Fecha']
                fecha = fecha.strftime("%d.%b.%Y")
                objt['Fecha'] = fecha
                objt['OTCL_DETALLE'] = resp_detalle
                objt['OTCL_TOTALES'] = data_totales
                resp.append(objt)
        else:
            # datos generales
            tc_contrato = 0
            data_contratos_g = Contract.query.with_entities(Contract.CN_CONTRATO,Contract.CN_TIPO_CONTRATO,Contract.CN_TC,Contract.CN_STATUS_CONTRATO, Contract.CN_NOMBRE,Contract.CN_APELLIDO,Contract.CN_TELEFONO,Contract.CN_EMAIL).filter(Contract.CN_CONTRATO==contrato).all()
            for item in data_contratos_g:
                tc_contrato = item.CN_TC
                objt_g = item._asdict()
            # datos generales
            aux_pagos_realizados = Movement.query\
                .with_entities(func.sum(func.nvl(func.decode(Movement.MO_MONEDA,'USD',Movement.MO_TOTAL,'MXN',Movement.MO_TOTAL/tc_contrato),0)))\
                .filter(Movement.MO_CONTRATO==contrato,Movement.MO_TIPOMOV.notin_(['COSTO CONTRATO','ENGANCHE']))\
                .label('CN_PAGOS_REALIZADOS')
            data_contratos_f = Contract.query.with_entities(Contract.CN_CONTRATO,Contract.CN_TIPO_CONTRATO,Contract.CN_PRECIO_VENTA, 
            Contract.CN_COSTO_CONTRATO,Contract.CN_PRIMER_PAGO,Contract.CN_MENSUALIDAD,aux_pagos_realizados,(Contract.CN_PRECIO_VENTA-Contract.CN_ENGANCHE_IMP).label('CN_SALDO_FINANCIADO'))\
            .filter(Contract.CN_CONTRATO==contrato).all()
            for item2 in data_contratos_f:
                objt_f = item2._asdict()
                objt_f['CN_PAGOS_REALIZADOS'] if objt_f['CN_PAGOS_REALIZADOS'] is not None else 0
                objt_f['CN_SALDO_ACTUAL'] =  abs(objt_f['CN_SALDO_FINANCIADO'] - objt_f['CN_PAGOS_REALIZADOS'])
            resp.append({
                "data_general": objt_g,
                "data_financial": objt_f
            })

    except Exception as e:
        print('Error al consultar contrato {}'.format(e))
        return JsonResponse(500, msg={'error': str(e)})

    return JsonResponse(200, data_json=resp, info={})