from flask import jsonify
from flask import Blueprint, request
from ..models.empleados import EmpleadosView
from app.auth.controllers.auth import token_required
from app.helpers.api import JsonResponse

referidos  = Blueprint("referidos", __name__, url_prefix='/referidos')

@referidos.route('/employee/get/<int:folio>', methods=['GET'])
@token_required
def employee_get(folio):
    if request.method == 'GET':
        try:
            """
                Consultar empleados
                parametros: folio
                select em_emp,em_nombre,em_depto,em_depto_desc,em_hotel,em_activo from GRHEMPLEADOS_V2;
            """
            empleado = []
            # consulta empleados

            data_emp = EmpleadosView.query.filter(EmpleadosView.EM_EMP==folio,EmpleadosView.EM_ACTIVO=='S').all()
            # print('data_emp', data_emp)
            for item in data_emp:
                obj = item.as_dict()
                obj.pop('EM_DEPTO')
                obj.pop('EM_ACTIVO')
                empleado.append(obj)
        
        except Exception as e:
            print('Error al consultar contrato {}'.format(e))
            return JsonResponse(
                                    500, 
                                    msg={'error': str(e)}
                                )

        return JsonResponse(
                                200, 
                                data_json=empleado, 
                                info={}
                            )