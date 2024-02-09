from app import app
from flask import Blueprint
from ...oasis.models.registration_card_data import RegistrationCardData as RC
from ...avalon.models.booking import BookingsDetailAvalon as D, BookingsGuestAvalon as G
from app.herpers.api import JsonResponse

vcm  = Blueprint("vcm", __name__, url_prefix='/vcm')

@vcm.route('/booking/bracelet/<folio>', methods=['GET'])
def get_by_bracelet(folio):
    booking = RC.query.filter(RC.HR_BRAZALETE==folio).first()
    if booking:
        guest = RC.query.filter(RC.HR_RESERVA==booking.HR_RESERVA, RC.HR_LINEA==booking.HR_LINEA, RC.HR_SECUENCIA==1).first()
        avalon_data = D.query.filter(D.Reserva==booking.HR_RESERVA, D.Linea==booking.HR_LINEA).first()
        if guest and avalon_data:
            e = avalon_data.Estado
            data = {
                'hotel': booking.HR_HOTEL,
                'reserva': booking.HR_RESERVA,
                'linea': int(booking.HR_LINEA),
                'estado': 'Reserva' if e == 0 else 'EnCasa' if e == 1 else 'Salida' if e == 2 else 'NoShow' if e == 3 else 'Cancelada',
                'habitacion': avalon_data.Habitacion,
                'cliente': guest.HR_NOMBRE,
                'nacionalidad': guest.HR_NACIONALIDAD,
                'email': guest.HR_EMAIL
            }
            return JsonResponse(200, data_json=data)
        return JsonResponse(404, msg={'error':'no se ha encontrado la reserva'})
    else:
        return JsonResponse(404, msg={'error':'no se ha encontrado la reserva'})