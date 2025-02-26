from datetime import datetime
from datetime import date
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Cobro, Pago, EliminacionPagos, TipoPago, TipoGasto, Gasto
from usuarios.models import ConteoAnualEstudiantes, Curso, LlevaCurso, Nacionalidad
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from .forms import PaymentRegisterForm, CobroExtraForm, CobroExtraCursoForm, TipoGastoForm, GastoForm, TipoPagoForm
from django.core.serializers import serialize
from decorators.decorators import staff_user
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
import json

# Create your views here.
@login_required(login_url='/usuarios/login/')
def control_view(request):
    return render(request, 'pagos/control.html')

@login_required(login_url='/usuarios/login/')
def caja_chica_view(request):
    return render(request, 'pagos/caja_chica.html')

@login_required(login_url='/usuarios/login/')
@staff_user
def pivote_view(request):
    return render(request, 'pagos/pivote.html')

@login_required(login_url='/usuarios/login/')
@staff_user
def pivote(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        if action == 'pivote':
            pagos = Pago.objects.filter(status=1)
            lista = []
            for pago in pagos:
                item = {
                    'id': pago.id, 
                    'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y'), 
                    'user': pago.user.username,
                    'names': pago.user.first_name+' ' + pago.user.last_name,
                    'codigo_curso': pago.codigo_curso.nombre,
                    'forma_pago': pago.forma_pago.nombre,
                    'tipo_pago': pago.cobro.tipo_pago.nombre,
                    'moneda': pago.moneda.nombre,
                    'cantidad': pago.cantidad,
                    'tipo': 'Pago',
                    }
                lista.append(item)
            gastos = Gasto.objects.filter(status=1)
            for gasto in gastos:
                item = {
                    'id': gasto.id, 
                    'fecha_pago': gasto.fecha_gasto.strftime('%d/%m/%Y'), 
                    'names': gasto.user.first_name+' ' + gasto.user.last_name,
                    'user': gasto.user.username,
                    'codigo_curso': '',
                    'forma_pago': 'Efectivo',
                    'tipo_pago': gasto.tipo_gasto.nombre,
                    'moneda': 'Quetzal',
                    'cantidad': gasto.cantidad,
                    'tipo': 'Gasto',
                    }
                lista.append(item)
            return JsonResponse({"data": lista}, safe=False)
    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def saldo_view(request):
    return render(request, 'pagos/saldo_consulta.html')

@login_required(login_url='/usuarios/login/')
def pagos(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        # params = request.POST.get('params')
        if action == 'listaPagos':
            pagos = Pago.objects.filter(status=1)
            return JsonResponse({"data":[x.toDict() for x in pagos]}, safe=False)
        elif action == 'cajaChica':
            pagos = Pago.objects.filter(status=1, forma_pago__nombre='Efectivo')
            lista = []
            for pago in pagos:
                item = {
                    'id': pago.id, 
                    'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y'), 
                    'user': pago.user.username,
                    'codigo_curso': pago.codigo_curso.nombre,
                    'forma_pago': 'Efectivo',
                    'tipo_pago': pago.cobro.tipo_pago.nombre,
                    'moneda': pago.moneda.nombre,
                    'cantidad': pago.cantidad,
                    'tipo': 'Ingresos',
                    }
                lista.append(item)
            gastos = Gasto.objects.filter(status=1)
            for gasto in gastos:
                item = {
                    'id': gasto.id, 
                    'fecha_pago': gasto.fecha_gasto.strftime('%d/%m/%Y'), 
                    'user': gasto.user.username,
                    'codigo_curso': '',
                    'forma_pago': 'Efectivo',
                    'tipo_pago': gasto.tipo_gasto.nombre,
                    'moneda': 'Quetzal',
                    'cantidad': gasto.cantidad,
                    'tipo': 'Gastos',
                    }
                lista.append(item)
            return JsonResponse({"data": lista})
        #     if params:
        #         parametros = params.split(',')
        #         # print(parametros)
        #         f_ini = parametros[0]
        #         f_fin = parametros[1]
        #         cod_usuario = parametros[2]
        #         if f_ini != '' and f_fin == '':
        #             pagos = pagos.filter(fecha_pago__gte=f_ini)
        #         if f_fin != '' and f_ini == '':
        #             pagos = pagos.filter(fecha_pago__lte=f_fin)
        #         if f_fin != '' and f_ini != '':
        #             pagos = pagos.filter(fecha_pago__range=[f_ini,f_fin])
        #         if cod_usuario != '':
        #             pagos = pagos.filter(user__username__contains=cod_usuario)

    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def solicitarEliminacionPago(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        id_pago = json.loads(request.POST.get('pagos_data')).get('pago_id')
        if action == 'pagoEliminacion':
            pago = Pago.objects.filter(id=id_pago)
            pago = pago.first()
            pago.status = 2
            pago.save()
            pagosExistentes = EliminacionPagos.objects.filter(pago=id_pago)
            if not pagosExistentes:
                EliminacionPagos.objects.create(pago=pago, solicitadoPor=request.user, respuesta=None)
            else:
                pagosExistentes.delete()
                EliminacionPagos.objects.create(pago=pago, solicitadoPor=request.user, respuesta=None)
            response_data = {}
            response_data['result'] = 'CONFIRMADO'
            return JsonResponse(response_data)

@login_required(login_url='/usuarios/login/')
@staff_user
def pagos_solicitados_eliminar_view(request):
    return render(request, 'pagos/pagos_solicitados_eliminar.html')

@login_required(login_url='/usuarios/login/')
@staff_user
def solicitud_eliminacion_pago(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        id_pago = json.loads(request.POST.get('pagos_data')).get('pago_id')
        if action == 'aceptarSolicitudEliminacionPago':
            # pago = Pago.objects.filter(id=id_pago)
            # pago.update(status=0)
            pago = Pago.objects.filter(id=id_pago)
            pago = pago.first()
            pago.status = 0
            pago.save()
            eliminacionPago = EliminacionPagos.objects.filter(pago=id_pago)

            eliminacionPago = eliminacionPago.first()
            eliminacionPago.procesadoPor = request.user
            eliminacionPago.respuesta = 0
            eliminacionPago.fechaRespuesta = datetime.now()
            eliminacionPago.save()
            response_data = {}
            response_data['result'] = 'CONFIRMADA SOLICITUD DE ELIMINACION DEL PAGO'
            return JsonResponse(response_data)
        elif action == 'rechazarSolicitudEliminacionPago':
            pago = Pago.objects.filter(id=id_pago)
            pago = pago.first()
            pago.status = 1
            pago.save()
            eliminacionPago = EliminacionPagos.objects.filter(pago=id_pago)
            eliminacionPago = eliminacionPago.first()
            eliminacionPago.procesadoPor = request.user
            eliminacionPago.respuesta = 1
            eliminacionPago.fechaRespuesta = datetime.now()
            eliminacionPago.save()
            response_data = {}
            response_data['result'] = 'RECHAZADA SOLICITUD DE ELIMINACION DEL PAGO'
            return JsonResponse(response_data)
    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')  

@login_required(login_url='/usuarios/login/')
@staff_user
def pagos_eliminados(request):
    return render(request, 'pagos/pagos_eliminados.html')

@login_required(login_url='/usuarios/login/')
@staff_user
def pagos_eliminados_list(request):
    if request.is_ajax() and request.method == 'POST':

        action = request.POST.get('action')
        params = request.POST.get('params')
        if action == 'listaPagos':
            # pagos = Pago.objects.filter(status=0)
            pagos = EliminacionPagos.objects.filter(respuesta=0)
            return JsonResponse({"data":[x.toDict() for x in pagos]}, safe=False)
    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def pagos_pendientes(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        params = request.POST.get('params')
        if action == 'listaPagos':
            pagos = Pago.objects.filter(status=2)
            if params:
                parametros = params.split(',')
                f_ini = parametros[0]
                f_fin = parametros[1]
                cod_usuario = parametros[2]
                if f_ini != '' and f_fin == '':
                    pagos = pagos.filter(fecha_pago__gte=f_ini)
                if f_fin != '' and f_ini == '':
                    pagos = pagos.filter(fecha_pago__lte=f_fin)
                if f_fin != '' and f_ini != '':
                    pagos = pagos.filter(fecha_pago__range=[f_ini,f_fin])
                if cod_usuario != '':
                    pagos = pagos.filter(user__username__contains=cod_usuario)
            return JsonResponse({"data":[x.toDict() for x in pagos]}, safe=False)
        else:
            response_data = {}
            response_data['result'] = 'ERROR'
            response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
            return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def cobros_estudiante(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            user = User.objects.get(username=request.POST.get('user'))
            cobros = Cobro.objects.filter(user=user)
            lista = []
            if user:
                pagos_estudiante = Pago.objects.filter(user = user).filter(status=1)
                for cobro in cobros:
                    pago_cobro = (pagos_estudiante.filter(cobro = cobro).aggregate(Sum('cantidad'))['cantidad__sum'] or 0)
                    diferencia = cobro.monto - pago_cobro
                    if diferencia != 0:
                        lista.append({
                            'id': cobro.id,
                            'user': cobro.user.username,
                            'fecha_cobro':cobro.fecha_cobro.strftime('%d/%m/%Y'),
                            'monto': diferencia,
                            'tipo_pago': cobro.tipo_pago.nombre,
                            'tipo_moneda': cobro.tipo_moneda.nombre
                        })
                return JsonResponse({"data":lista}, safe=False)
    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def moneda_estudiante(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            moneda = User.objects.get(username=request.POST.get('user')).userextra.nacionalidad.moneda
            return JsonResponse({"data":[{'id': moneda.id, 'nombre': moneda.nombre}]}, safe=False)
    else:
        response_data = {}
        response_data['result'] = 'ERROR'
        response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
        return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def saldos(request):
    if request.is_ajax() and request.method == 'POST':
        action = request.POST.get('action')
        params = request.POST.get('params')
        if action == 'listaSaldos':
            cursosLlevados = LlevaCurso.objects.all()
            hoy = date.today()
            lista = []
            for cursoLlevado in cursosLlevados:
                pagos = Pago.objects.all()
                cobros = Cobro.objects.all()
                moneda_usuario = cursoLlevado.user.userextra.nacionalidad.moneda.nombre
                pagos_usuario = pagos.filter(user__username=cursoLlevado.user.username)
                pagos_usuario = pagos_usuario.filter(codigo_curso__codigo=cursoLlevado.curso.codigo).filter(status=1)
                pagos_usuario = pagos_usuario.filter(moneda__nombre=moneda_usuario)
                cobros = cobros.filter(user__username=cursoLlevado.user.username)
                cobros = cobros.filter(tipo_moneda__nombre=moneda_usuario)
                cobros = cobros.filter(codigo_curso__codigo=cursoLlevado.curso.codigo)
                for cobro in cobros:
                    pagos_cobro = pagos_usuario.filter(cobro=cobro)
                    diferencia = cobro.monto - (pagos_cobro.aggregate(Sum('cantidad'))['cantidad__sum'] or 0)
                    if diferencia == 0:
                        for pago in pagos_cobro:
                            lista.append({
                                'desc_est': 'Nombre: '
                                                +cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name+
                                            ' - Código Estudiante: '
                                                +cursoLlevado.user.username+
                                            ' - Moneda: '
                                                +moneda_usuario,
                                'nombre_est': cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name,
                                'codigo_curso': cursoLlevado.curso.codigo,
                                'desc_pag': cobro.tipo_pago.nombre,
                                'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y'),
                                'tipo_pago': 'Pagado',
                                'cantidad': pago.cantidad,
                                'codigo': pago.user.username,
                                'curso': pago.codigo_curso.codigo})
                    else:
                        for pago in pagos_cobro:
                            lista.append({
                                'desc_est': 'Nombre: '
                                                +cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name+
                                            ' - Código Estudiante: '
                                                +cursoLlevado.user.username+
                                            ' - Moneda: '
                                                +moneda_usuario,
                                'nombre_est': cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name,
                                'codigo_curso': cursoLlevado.curso.codigo,
                                'desc_pag': cobro.tipo_pago.nombre,
                                'fecha_pago': pago.fecha_pago.strftime('%d/%m/%Y'),
                                'tipo_pago': 'Pagado',
                                'cantidad': pago.cantidad,
                                'codigo': pago.user.username,
                                'curso': pago.codigo_curso.codigo})
                        estado = 'Vencido (Pagar lo antes posible)' if hoy > cobro.fecha_cobro else 'Por Vencer'
                        lista.append({
                                'desc_est': 'Nombre: '
                                                +cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name+
                                            ' - Código Estudiante: '
                                                +cursoLlevado.user.username+
                                            ' - Moneda: '
                                                +moneda_usuario,
                                'desc_pag': cobro.tipo_pago.nombre,
                                'fecha_pago': cobro.fecha_cobro.strftime('%d/%m/%Y'),
                                'tipo_pago': estado,
                                'cantidad': diferencia,
                                'codigo': cobro.user.username,
                                'curso': cursoLlevado.curso.codigo})
                        if estado == 'Vencido (Pagar lo antes posible)' and cobro.tipo_pago.nombre != 'Mora':
                            if not cobros.filter(relacionado=cobro.id):
                                Cobro.objects.create(user=cobro.user, fecha_cobro=cobro.fecha_cobro, monto=50, tipo_pago=TipoPago.objects.get(nombre='Mora'), tipo_moneda=cursoLlevado.user.userextra.nacionalidad.moneda, relacionado=cobro, codigo_curso=cursoLlevado.curso)
                                lista.append({
                                'desc_est': 'Nombre: '
                                                +cursoLlevado.user.first_name+' '+cursoLlevado.user.last_name+
                                            ' - Código Estudiante: '
                                                +cursoLlevado.user.username+
                                            ' - Moneda: '
                                                +moneda_usuario,
                                'desc_pag': 'Mora',
                                'fecha_pago': cobro.fecha_cobro.strftime('%d/%m/%Y'),
                                'tipo_pago': estado,
                                'cantidad': 50,
                                'codigo': cobro.user.username,
                                'curso': cursoLlevado.curso.codigo})
            return JsonResponse({"data":lista}, safe=False)
        else:
            response_data = {}
            response_data['result'] = 'ERROR'
            response_data['message'] = 'AUTH OR REQUEST METHOD ERROR'
            return HttpResponse(serialize('json', response_data), content_type='application/json')

@login_required(login_url='/usuarios/login/')
def control_pagos(request):
    pagos = Pago.objects.all()
    context = {
        'pagos': pagos
    }
    return render(request, 'pagos/control_excel.html', context)

@login_required(login_url='/usuarios/login/')
def ingreso_view(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = PaymentRegisterForm(request.POST)
            cobro = Cobro.objects.get(id = request.POST.get('cobro'))
            pagos_estudiante = Pago.objects.filter(user = request.POST.get('user')).filter(status=1)
            pagos_cobro = (pagos_estudiante.filter(cobro = cobro).aggregate(Sum('cantidad'))['cantidad__sum'] or 0) + float(request.POST.get('cantidad'))
            if cobro.monto < pagos_cobro:
                context = {'form': form, "message":"Esta realizando un pago que excede el monto del cobro"}
                return render(request, 'pagos/ingresar.html', context)
            else:
                if form.is_valid():
                    Pago.objects.create(**form.cleaned_data)
                    form = PaymentRegisterForm()
                    context = {'form': form, "message":"Pago Completado"}
                    return render(request, 'pagos/ingresar.html', context)
        else:
            form = PaymentRegisterForm()
        context = {'form': form}
        return render(request, 'pagos/ingresar.html', context)
    else:
        return render(request, 'pagos/ingresar.html')

@login_required(login_url='/usuarios/login/')
def cobros_extra_view(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form_cobros_extra = CobroExtraForm(request.POST)
            if form_cobros_extra.is_valid():
                Cobro.objects.create(**form_cobros_extra.cleaned_data)
                form_cobros_extra = CobroExtraForm()
                context = {'form_cobros_extra': form_cobros_extra, "message": "Ingreso de cobros extra a usuario exitoso"}
                return render(request, 'pagos/cobros_extra.html', context)
        else:
            form_cobros_extra = CobroExtraForm()
        context = {'form_cobros_extra': form_cobros_extra}
        return render(request, 'pagos/cobros_extra.html', context)
    else:
        return HttpResponseRedirect('../pagos/login/')

@login_required(login_url='/usuarios/login/')
def cobros_extra_a_curso(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form_cobros_extra = CobroExtraCursoForm(request.POST)
            if form_cobros_extra.is_valid():

                for asig in LlevaCurso.objects.all():
                    
                    if asig.curso == form_cobros_extra.cleaned_data['Curso']:
                        data = {}
                        data['user'] = asig.user
                        data['fecha_cobro'] = form_cobros_extra.cleaned_data['fecha_cobro']
                        data['monto'] = form_cobros_extra.cleaned_data['monto']
                        data['tipo_moneda'] = form_cobros_extra.cleaned_data['tipo_moneda']
                        data['tipo_pago'] = form_cobros_extra.cleaned_data['tipo_pago']
                        data['relacionado'] = None
                        data['codigo_curso'] = form_cobros_extra.cleaned_data['Curso']
                        Cobro.objects.create(**data)
                        
                form_cobros_extra = CobroExtraCursoForm()
                context = {'form_cobros_extra': form_cobros_extra, "message":"Ingreso de cobros extra a un curso exitoso"}
                return render(request, 'pagos/cobros_extra.html', context)
        else:
            form_cobros_extra = CobroExtraCursoForm()
        context = {'form_cobros_extra': form_cobros_extra}
        return render(request, 'pagos/cobros_extra.html', context)
    else:
        return HttpResponseRedirect('../pagos/login/')

@login_required(login_url='/usuarios/login/')
def ingreso_tipo_gasto(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = TipoGastoForm(request.POST)
            if form.is_valid():
                TipoGasto.objects.create(**form.cleaned_data)
                form = TipoGastoForm()
                context = {'form': form, "message":"Ingreso de tipo de gasto exitoso"}
                return render(request, 'pagos/ingreso_tipo_gasto.html', context)
            else:
                form = TipoGastoForm()
        else:
            form = TipoGastoForm()
        context = {'form': form}
        return render(request, 'pagos/ingreso_tipo_gasto.html', context)
    else:
        return HttpResponseRedirect('../pagos/login/')

@login_required(login_url='/usuarios/login/')
def ingreso_gasto(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = GastoForm(request.POST)
            if form.is_valid():
                user = request.user
                Gasto.objects.create(**form.cleaned_data, user_id=user.id)
                form = GastoForm()
                context = {'form': form, "message": "Ingreso de gasto exitoso"}
                return render(request, 'pagos/ingreso_gasto.html', context)
            else:
                form = GastoForm()
        else:
            form = GastoForm()
        context = {'form': form}
        return render(request, 'pagos/ingreso_gasto.html', context)
    else:
        return HttpResponseRedirect('../pagos/login/')


@login_required(login_url='/usuarios/login/')
def definicion_tipo_pago(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            form = TipoPagoForm(request.POST)
            if form.is_valid():
                TipoPago.objects.create(**form.cleaned_data)
                form = TipoPagoForm()
                context = {'form': form, "message":"Ingreso de tipo de pago exitoso"}
                return render(request, 'pagos/definicion_tipo_pago.html', context)
            else:
                form = TipoPagoForm()
        else:
            form = TipoPagoForm()
        context = {'form': form}
        return render(request, 'pagos/definicion_tipo_pago.html', context)
    else:
        return HttpResponseRedirect('../pagos/login/')

@login_required(login_url='/usuarios/login/')
def correos_saldos(request):
    if request.method == "POST":
        usuarios = User.objects.all()
        cursosLlevados = LlevaCurso.objects.all()
        cobros = Cobro.objects.all()
        for user in usuarios:
            cursosUsuario = cursosLlevados.filter(user__username=user.username)
            for curso in cursosUsuario:
                cobrosUsuario = cobros.filter(user__username=curso.user.username)
                cobrosUsuario = cobrosUsuario.filter(codigo_curso__codigo=curso.curso.codigo)
                cobrosUsuario = cobrosUsuario.order_by('-fecha_cobro')
                total_deuda = cobrosUsuario.aggregate(Sum('monto'))['monto__sum']
                context = {"cobros": cobrosUsuario, "total_deuda": total_deuda, "mensaje": 'A continuación se le ha enviado su estado de cuenta ' + user.first_name + ' ' + user.last_name + ', en el curso: ' + curso.curso.codigo + curso.curso.nombre}
                template = get_template('correo.html')
                content = template.render(context)
                email = EmailMultiAlternatives(
                    'Estado de cuenta PlusAcademy, curso: ' + curso.curso.codigo + curso.curso.nombre,
                    'A continuación se le ha enviado su estado de cuenta ' + user.first_name + ' ' + user.last_name + ', en el curso: ' + curso.curso.codigo + curso.curso.nombre,
                    settings.EMAIL_HOST_USER,
                    [user.email]
                )
                email.attach_alternative(content, 'text/html')
                email.send()
        context = {"message":"Envio de estados de cuenta a correos de estudiantes exitoso"}
        return render(request, 'pagos/correos_saldos.html', context)
    return render(request, 'pagos/correos_saldos.html')

@login_required(login_url='/usuarios/login/')
def correos_morosos(request):
    if request.method == "POST":
        usuarios = User.objects.all()
        cursosLlevados = LlevaCurso.objects.all()
        cobros = Cobro.objects.all()
        datos = []
        for user in usuarios:
            cursosUsuario = cursosLlevados.filter(user__username=user.username)
            for curso in cursosUsuario:
                cobrosUsuario = cobros.filter(user__username=curso.user.username)
                cobrosUsuario = cobrosUsuario.filter(codigo_curso__codigo=curso.curso.codigo)
                cobrosUsuario = cobrosUsuario.filter(tipo_pago__nombre='Mora')
                cobrosUsuario = cobrosUsuario.order_by('-fecha_cobro')
                total_deuda = cobrosUsuario.aggregate(Sum('monto'))['monto__sum']
                datos.append({"username":user.username, "nombre":user.first_name + ' ' + user.last_name, "curso":curso.curso.codigo, "total": total_deuda, "moneda":user.userextra.nacionalidad.moneda})
        usuariosStaff = usuarios.filter(is_staff=True)
        for user in usuariosStaff:
            context = {"datos": datos, "mensaje":user.first_name + ' ' + user.last_name + ', a continuación se le ha enviado los estudiantes con su mora total por curso' }
            template = get_template('correo_morosos.html')
            content = template.render(context)
            email = EmailMultiAlternatives(
                'Morosos PlusAcademy '+user.username,
                'A continuación se le ha enviado Los estudiantes con mora con su total ' + user.first_name + ' ' + user.last_name,
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            email.attach_alternative(content, 'text/html')
            email.send()
        context = {"message":"Envio de estados de cuenta a correos de estudiantes morosos exitoso"}
        return render(request, 'pagos/correos_morosos.html', context)
    return render(request, 'pagos/correos_morosos.html')