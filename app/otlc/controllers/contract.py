from app import app
from flask import request, jsonify
from flask import Blueprint
from ..models.contract import Contract, Movement, AccountStatusHeader, AccountStatusBody, Amortization,TipoMov, db
from sqlalchemy.sql.expression import func
from sqlalchemy import text, or_, and_
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
            tc_contrato, aux_pagos_realizados, aux_interes_i, aux_eng_p = 0, 0, 0, 0
            data_contratos_g = Contract.query.with_entities(Contract.CN_CONTRATO,Contract.CN_TIPO_CONTRATO,Contract.CN_TC,Contract.CN_STATUS_CONTRATO, Contract.CN_NOMBRE,Contract.CN_APELLIDO,Contract.CN_TELEFONO,Contract.CN_EMAIL).filter(Contract.CN_CONTRATO==contrato).all()
            for item in data_contratos_g:
                tc_contrato = item.CN_TC
                objt_g = item._asdict()
            # datos generales
            aux_pagos_realizados = Movement.query\
                .with_entities(func.sum(func.nvl(func.decode(Movement.MO_MONEDA,'USD',Movement.MO_TOTAL,'MXN',Movement.MO_TOTAL/tc_contrato),0)))\
                .filter(Movement.MO_CONTRATO==contrato,Movement.MO_TIPOMOV.notin_(['COSTO CONTRATO','ENGANCHE']))\
                .label('CN_PAGOS_REALIZADOS')
            interes_inicial = Amortization.query.with_entities(func.sum(func.decode(func.nvl(Amortization.TA_REFINA_EFECTO,'@'),'PLAZO',0,Amortization.TA_AMORT_INT)).label('CN_INTERES_INICIAL'))\
            .filter(Amortization.TA_EMP==15,Amortization.TA_PLAN=='B',Amortization.TA_CONTRATO==contrato).first()
            aux_enganche_pagado = Movement.query.with_entities(func.sum(func.decode(Movement.MO_MONEDA,'USD',Movement.MO_TOTAL,'MXN',Movement.MO_TOTAL/tc_contrato)).label('ENGANCHE'))\
            .filter(Movement.MO_CONTRATO==contrato,Movement.MO_TIPOMOV=='ENGANCHE').all()
            if len(aux_enganche_pagado) > 0:
                aux_eng_p = aux_enganche_pagado[0].ENGANCHE if aux_enganche_pagado[0].ENGANCHE else 0
            if len(interes_inicial) > 0:
                aux_interes_i = interes_inicial.CN_INTERES_INICIAL if interes_inicial.CN_INTERES_INICIAL else 0
            data_contratos_f = Contract.query.with_entities(Contract.CN_CONTRATO,Contract.CN_TIPO_CONTRATO,Contract.CN_MONEDA,Contract.CN_PRECIO_VENTA, 
            Contract.CN_COSTO_CONTRATO,Contract.CN_PRIMER_PAGO,Contract.CN_MENSUALIDAD,aux_pagos_realizados,((Contract.CN_PRECIO_VENTA + aux_interes_i)-Contract.CN_ENGANCHE_IMP).label('CN_SALDO_FINANCIADO'))\
            .filter(Contract.CN_CONTRATO==contrato).all()
            for item2 in data_contratos_f:
                objt_f = item2._asdict()
                objt_f['CN_ENG_PAGADO'] = aux_eng_p
                objt_f['CN_INTERES_INICIAL'] = aux_interes_i
                objt_f['CN_PAGOS_REALIZADOS'] = round(objt_f['CN_PAGOS_REALIZADOS'], 4) if objt_f['CN_PAGOS_REALIZADOS'] else 0
                objt_f['CN_SALDO_ACTUAL'] =  round((objt_f['CN_PRECIO_VENTA'] + aux_interes_i) - (objt_f['CN_PAGOS_REALIZADOS'] + objt_f['CN_ENG_PAGADO']), 4)
            resp.append({
                "data_general": objt_g,
                "data_financial": objt_f
            })

    except Exception as e:
        print('Error al consultar contrato {}'.format(e))
        return JsonResponse(500, msg={'error': str(e)})

    return JsonResponse(200, data_json=resp, info={})

@otlc.route('/contract/account-status/<contrato>/get', methods=['GET'])
def contratct_account_status_otlc(contrato):
    try:
        resp = {}
        resp_detalle = []
        fecha_hoy = datetime.today()
        today_f = datetime.now()
        format_sesion = today_f.strftime("%d%m%y%H%M")
        try:
            engine = db.get_engine(bind_key='OTLC')
            connection = engine.raw_connection()
            cursor = connection.cursor()
            estado_cuenta = cursor.callproc("GENERA_EDOCTA",[format_sesion,fecha_hoy,'OTLC','15','B',contrato])
            print('estado_cuenta', estado_cuenta)
        except Exception as error:
            print('Error al generar información genera_edocta {}'.format(error))

        detalle = AccountStatusBody.query.filter(AccountStatusBody.ED_CONTRATO==contrato,AccountStatusBody.ED_SESION==format_sesion).order_by(AccountStatusBody.ED_SECUENCIA).all()
        for item in detalle:
            objt_detalle = {}
            item = item.as_dict()
            # if item['Pago'] is None:
            #         item['Pago'] = ""
            # if item['Vencimiento'] is None:
            #         item['Vencimiento'] = ""
            if item['Saldo_Mes'] is None:
                    item['Saldo_Mes'] = 0
            if item['Total_Pagado'] is None:
                    item['Total_Pagado'] = 0
            for x in item.keys():
                if x not in ['ED_SESION','ED_FECHA_GEN','ED_USUARIO','ED_CONTRATO','ED_SECUENCIA','ED_FORMATO']:
                    objt_detalle[x] = item[x]
            resp_detalle.append(objt_detalle)
        encabezado = AccountStatusHeader.query.filter(AccountStatusHeader.EE_CONTRATO==contrato,AccountStatusHeader.EE_SESION==format_sesion).first()
        resp = encabezado.as_dict()
        resp.pop('EE_SESION')

    except Exception as e:
        print('Error al consultar contrato {}'.format(e))
        return JsonResponse(500, msg={'error': str(e)})

    return JsonResponse(200, data_json={"Encabezado":resp,"Detalle":resp_detalle}, info={})