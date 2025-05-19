import pandas as pd
import xml.etree.ElementTree as ET
import json
import requests
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import Nomenclature, LSI
from .forms import NomenclatureForm, LSIForm
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы
INTBUS_SYNC_URL = "http://intbus:8000/sync/api/sync/"

# Аутентификация и регистрация
def login_view(request):
    next_url = request.GET.get('next', 'home')
    
    # Создаем тестового пользователя, если его нет
    if not User.objects.filter(username='testuser').exists():
        try:
            user = User.objects.create_user('testuser', 'test@example.com', 'password123')
            user.save()
            print("Создан тестовый пользователь: testuser с паролем password123")
        except Exception as e:
            print(f"Ошибка создания тестового пользователя: {e}")
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_param = request.POST.get('next', 'home')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if next_param.startswith('/'):
                return redirect(next_param)
            else:
                try:
                    return redirect(next_param)
                except:
                    return redirect('home')  
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    context = {'next': next_url}
    return render(request, 'accounts/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

# Главная страница
@login_required
def home(request):
    nomenclature_count = Nomenclature.objects.count()
    lsi_count = LSI.objects.count()
    
    context = {
        'nomenclature_count': nomenclature_count,
        'lsi_count': lsi_count
    }
    
    return render(request, 'accounts/home.html', context)

# Работа с номенклатурой
@login_required
def nomenclature_list(request):
    nomenclatures = Nomenclature.objects.all()
    context = {'nomenclatures': nomenclatures}
    return render(request, 'accounts/nomenclature_list.html', context)

@login_required
def create_nomenclature(request):
    if request.method == 'POST':
        form = NomenclatureForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nomenclature_list')
    else:
        form = NomenclatureForm()
    
    return render(request, 'accounts/create_nomenclature.html', {'form': form})

@login_required
def edit_nomenclature(request, pk):
    nomenclature = get_object_or_404(Nomenclature, pk=pk)
    
    if request.method == 'POST':
        form = NomenclatureForm(request.POST, instance=nomenclature)
        if form.is_valid():
            form.save()
            return redirect('nomenclature_list')
    else:
        form = NomenclatureForm(instance=nomenclature)
    
    context = {'form': form, 'nomenclature': nomenclature}
    return render(request, 'accounts/edit_nomenclature.html', context)

@login_required
def delete_nomenclature(request, pk):
    nomenclature = get_object_or_404(Nomenclature, pk=pk)
    
    if request.method == 'POST':
        nomenclature.delete()
        return redirect('nomenclature_list')
    
    context = {'nomenclature': nomenclature}
    return render(request, 'accounts/delete_nomenclature.html', context)

# Отправка данных номенклатуры в IntBus
@login_required
def send_nomenclature_to_intbus(request, pk):
    nomenclature = get_object_or_404(Nomenclature, pk=pk)
    
    try:
        # Формируем XML данные по образцу
        xml_data = f"""
        <НоменклатураИзделие>
            <УУИД>{nomenclature.uuid or ''}</УУИД>
            <СПК_ВидНоменклатуры>{nomenclature.spk_nomenclature_type or ''}</СПК_ВидНоменклатуры>
            <Аббревиатура>{nomenclature.abbreviation or ''}</Аббревиатура>
            <ДатаВведенияВДействие>{nomenclature.effective_date.strftime('%Y-%m-%d') if nomenclature.effective_date else ''}</ДатаВведенияВДействие>
            <КодВнутренний>{nomenclature.internal_code or ''}</КодВнутренний>
            <КодЕКПС>{nomenclature.ekps_code or ''}</КодЕКПС>
            <КодКВТ>{nomenclature.kvt_code or ''}</КодКВТ>
            <КонтрольнаяСуммаЗаписи>{nomenclature.checksum or ''}</КонтрольнаяСуммаЗаписи>
            <НаименованиеКраткое>{nomenclature.short_name or ''}</НаименованиеКраткое>
            <НаименованиеПолное>{nomenclature.full_name or ''}</НаименованиеПолное>
            <ПометкаУдаления>{'true' if nomenclature.deletion_mark else 'false'}</ПометкаУдаления>
            <ПризнакАрхивнойЗаписи>{'true' if nomenclature.archived else 'false'}</ПризнакАрхивнойЗаписи>
            <УникальныйКодКлассификатора>{nomenclature.classifier_unique_code or ''}</УникальныйКодКлассификатора>
            <ЧертежныйНомер>{nomenclature.drawing_number or ''}</ЧертежныйНомер>
            <Шифр>{nomenclature.cipher or ''}</Шифр>
        </НоменклатураИзделие>
        """
        
        # Создаем данные для отправки в новом формате
        data = {
            'apikey': 'ATOM-INTBUS-SECRET-KEY',  # Секретный ключ для авторизации
            'sender': 'ATOM',                   # Идентификатор отправителя
            'data': xml_data                    # XML данные в формате строки
        }
        
        # Установка заголовков
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Логируем отправляемые данные
        logger.info(f"Отправка данных в IntBus: {INTBUS_SYNC_URL}")
        logger.info(f"Заголовки: {headers}")
        
        # Отправляем данные в IntBus с правильными заголовками
        response = requests.post(INTBUS_SYNC_URL, json=data, headers=headers)
        
        # Логируем ответ
        logger.info(f"Ответ от IntBus: {response.status_code}, {response.text[:200]}")
        
        if response.status_code == 200:
            messages.success(request, 'Данные номенклатуры успешно отправлены в IntBus')
        else:
            messages.error(request, f'Ошибка при отправке данных: {response.status_code} {response.text}')
        
    except Exception as e:
        logger.error(f"Ошибка при отправке данных: {str(e)}", exc_info=True)
        messages.error(request, f'Ошибка при отправке данных: {str(e)}')
    
    return redirect('nomenclature_list')

# Работа с LSI
@login_required
def lsi_list(request):
    lsi_items = LSI.objects.all()
    context = {'lsi_items': lsi_items}
    return render(request, 'accounts/lsi_list.html', context)

@login_required
def create_lsi(request):
    if request.method == 'POST':
        form = LSIForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lsi_list')
    else:
        form = LSIForm()
    
    return render(request, 'accounts/create_lsi.html', {'form': form})

@login_required
def edit_lsi(request, pk):
    lsi = get_object_or_404(LSI, pk=pk)
    
    if request.method == 'POST':
        form = LSIForm(request.POST, instance=lsi)
        if form.is_valid():
            form.save()
            return redirect('lsi_list')
    else:
        form = LSIForm(instance=lsi)
    
    context = {'form': form, 'lsi': lsi}
    return render(request, 'accounts/edit_lsi.html', context)

@login_required
def delete_lsi(request, pk):
    lsi = get_object_or_404(LSI, pk=pk)
    
    if request.method == 'POST':
        lsi.delete()
        return redirect('lsi_list')
    
    context = {'lsi': lsi}
    return render(request, 'accounts/delete_lsi.html', context)

# Отправка данных LSI в IntBus
@login_required
def send_lsi_to_intbus(request, pk):
    lsi = get_object_or_404(LSI, pk=pk)
    
    try:
        # Формируем XML данные по образцу
        xml_data = f"""
        <КунПереченьКодовФункциональныхСистем>
            <Шифр>{lsi.cipher or ''}</Шифр>
            <УУИД>{lsi.uuid or ''}</УУИД>
            <Специальность>{lsi.specialty or ''}</Специальность>
            <ПризнакГруппы>{'true' if lsi.group_indicator else 'false'}</ПризнакГруппы>
            <ПометкаУдаления>{'true' if lsi.deletion_mark else 'false'}</ПометкаУдаления>
            <ПозицияВШтатнойСтруктуреТипа>{lsi.position_in_staff_structure_type or ''}</ПозицияВШтатнойСтруктуреТипа>
            <НомерЧертежа>{lsi.drawing_number or ''}</НомерЧертежа>
            <НаименованиеПозиции>{lsi.position_name or ''}</НаименованиеПозиции>
            <Лкн>{lsi.lkn or ''}</Лкн>
            <Количество>{lsi.quantity}</Количество>
            <КодТипаОбъекта>{lsi.object_type_code or ''}</КодТипаОбъекта>
            <КодПозиции>{lsi.position_code or ''}</КодПозиции>
            <КодМодификации>{lsi.modification_code or ''}</КодМодификации>
            <Код5>{lsi.code_5 or ''}</Код5>
            <Код4>{lsi.code_4 or ''}</Код4>
            <Код3>{lsi.code_3 or ''}</Код3>
            <Код2>{lsi.code_2 or ''}</Код2>
            <Код1>{lsi.code_1 or ''}</Код1>
            <ИдентификаторРодительскойЗаписи>{lsi.parent_record_id or ''}</ИдентификаторРодительскойЗаписи>
            <Dns>{lsi.dns or ''}</Dns>
        </КунПереченьКодовФункциональныхСистем>
        """
        
        # Создаем данные для отправки в новом формате
        data = {
            'apikey': 'ATOM-INTBUS-SECRET-KEY',  # Секретный ключ для авторизации
            'sender': 'ATOM',                   # Идентификатор отправителя
            'data': xml_data                    # XML данные в формате строки
        }
        
        # Установка заголовков
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Логируем отправляемые данные
        logger.info(f"Отправка данных ЛСИ в IntBus: {INTBUS_SYNC_URL}")
        logger.info(f"Заголовки: {headers}")
        
        # Отправляем данные в IntBus с правильными заголовками
        response = requests.post(INTBUS_SYNC_URL, json=data, headers=headers)
        
        # Логируем ответ
        logger.info(f"Ответ от IntBus: {response.status_code}, {response.text[:200]}")
        
        if response.status_code == 200:
            messages.success(request, 'Данные ЛСИ успешно отправлены в IntBus')
        else:
            messages.error(request, f'Ошибка при отправке данных: {response.status_code} {response.text}')
        
    except Exception as e:
        logger.error(f"Ошибка при отправке данных: {str(e)}", exc_info=True)
        messages.error(request, f'Ошибка при отправке данных: {str(e)}')
    
    return redirect('lsi_list')

# Экспорт и импорт
@login_required
def export_to_excel(request):
    # Экспорт Nomenclature
    nomenclature_data = Nomenclature.objects.all().values()
    nomenclature_df = pd.DataFrame(list(nomenclature_data))
    
    # Экспорт LSI
    lsi_data = LSI.objects.all().values()
    lsi_df = pd.DataFrame(list(lsi_data))
    
    # Создаем файл Excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="atom_data.xlsx"'
    
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        nomenclature_df.to_excel(writer, sheet_name='Nomenclature', index=False)
        lsi_df.to_excel(writer, sheet_name='LSI', index=False)
        
    return response

@login_required
def import_from_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        try:
            # Читаем файл Excel
            xl = pd.ExcelFile(excel_file)
            
            # Импорт номенклатуры
            if 'Nomenclature' in xl.sheet_names:
                nomenclature_df = pd.read_excel(xl, 'Nomenclature')
                
                # Удаляем существующие записи, если есть флаг очистки
                if request.POST.get('clear_existing') == 'on':
                    Nomenclature.objects.all().delete()
                
                # Добавляем новые записи
                for _, row in nomenclature_df.iterrows():
                    # Пропускаем id, если он есть
                    if 'id' in row:
                        row = row.drop('id')
                    
                    # Создаем новую запись
                    Nomenclature.objects.create(**row.to_dict())
            
            # Импорт LSI
            if 'LSI' in xl.sheet_names:
                lsi_df = pd.read_excel(xl, 'LSI')
                
                # Удаляем существующие записи, если есть флаг очистки
                if request.POST.get('clear_existing') == 'on':
                    LSI.objects.all().delete()
                
                # Добавляем новые записи
                for _, row in lsi_df.iterrows():
                    # Пропускаем id, если он есть
                    if 'id' in row:
                        row = row.drop('id')
                    
                    # Создаем новую запись
                    LSI.objects.create(**row.to_dict())
            
            messages.success(request, 'Данные успешно импортированы')
            
        except Exception as e:
            messages.error(request, f'Ошибка импорта: {str(e)}')
        
        return redirect('home')
    
    return render(request, 'accounts/import_excel.html')

# API для приема данных из IntBus
@csrf_exempt
def receive_data_from_intbus(request):
    """
    Обработчик для приема данных от IntBus
    """
    logger.info(f"Получен запрос в receive_data_from_intbus: метод {request.method}, путь {request.path}")
    logger.info(f"Заголовки запроса: {dict(request.headers)}")
    
    if request.method != 'POST':
        logger.warning(f"Метод не поддерживается: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Метод не поддерживается'}, status=405)
    
    try:
        # Получаем данные из запроса
        try:
            request_body = request.body.decode('utf-8')
            logger.info(f"Тело запроса: {request_body[:500]}...")
            data = json.loads(request_body)
            logger.info(f"Получены данные от IntBus: {data.keys() if isinstance(data, dict) else 'не словарь'}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}")
            return JsonResponse({'status': 'error', 'message': f'Неверный формат JSON: {str(e)}'}, status=400)
        
        # Проверка формата данных
        if not isinstance(data, dict):
            logger.error(f"Неверный формат данных, получен тип: {type(data)}")
            return JsonResponse({'status': 'error', 'message': 'Неверный формат данных'}, status=400)
        
        # Проверяем наличие необходимых полей
        if 'data' not in data or 'dataType' not in data:
            missing_fields = [field for field in ['data', 'dataType'] if field not in data]
            logger.error(f"Отсутствуют обязательные поля: {missing_fields}")
            return JsonResponse({
                'status': 'error', 
                'message': f'Неверный формат данных. Отсутствуют обязательные поля: {missing_fields}'
            }, status=400)
        
        item_data = data['data']
        data_type = data['dataType']
        logger.info(f"Тип данных: {data_type}")
        
        # Обработка номенклатуры
        if data_type == 'nomenclature':
            # Ищем внутренний код в разных возможных полях
            internal_code = None
            
            # Проверяем в разных местах
            if 'internalCode' in item_data:
                internal_code = item_data['internalCode']
            elif 'internal_code' in item_data:
                internal_code = item_data['internal_code']
            elif 'code' in item_data:
                internal_code = item_data['code']
            elif 'КодВнутренний' in item_data:
                internal_code = item_data['КодВнутренний']
            elif 'code' in data:  # Проверяем на верхнем уровне
                internal_code = data['code']
            
            if not internal_code:
                logger.error("Не найден внутренний код номенклатуры ни в одном из полей")
                logger.error(f"Доступные поля в item_data: {list(item_data.keys())}")
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Отсутствует внутренний код номенклатуры'
                }, status=400)
            
            logger.info(f"Обработка номенклатуры из IntBus с внутренним кодом: {internal_code}")
            
            # Проверяем существует ли номенклатура
            try:
                nomenclature = Nomenclature.objects.get(internal_code=internal_code)
                logger.info(f"Найдена существующая номенклатура с ID: {nomenclature.id}")
                
                # Обновляем существующую запись
                nomenclature.abbreviation = item_data.get('abbreviation', nomenclature.abbreviation)
                nomenclature.short_name = item_data.get('shortName', item_data.get('short_name', nomenclature.short_name))
                nomenclature.full_name = item_data.get('fullName', item_data.get('full_name', item_data.get('name', nomenclature.full_name)))
                nomenclature.cipher = item_data.get('cipher', nomenclature.cipher)
                nomenclature.ekps_code = item_data.get('ekpsCode', item_data.get('ekps_code', nomenclature.ekps_code))
                nomenclature.kvt_code = item_data.get('kvtCode', item_data.get('kvt_code', nomenclature.kvt_code))
                nomenclature.drawing_number = item_data.get('drawingNumber', item_data.get('drawing_number', nomenclature.drawing_number))
                nomenclature.spk_nomenclature_type = item_data.get('typeOfNomenclature', item_data.get('type_of_nomenclature', item_data.get('spk_nomenclature_type', nomenclature.spk_nomenclature_type)))
                
                nomenclature.save()
                logger.info(f"Номенклатура с ID {nomenclature.id} успешно обновлена")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Номенклатура успешно обновлена',
                    'id': nomenclature.id
                })
                
            except Nomenclature.DoesNotExist:
                # Создаем новую номенклатуру
                logger.info(f"Создание новой номенклатуры с внутренним кодом: {internal_code}")
                
                full_name = item_data.get('fullName', item_data.get('full_name', item_data.get('name', '')))
                short_name = item_data.get('shortName', item_data.get('short_name', full_name[:100] if full_name else ''))
                
                # Подготовим словарь с правильными именами полей для модели Nomenclature
                nom_data = {
                    'internal_code': internal_code,
                    'abbreviation': item_data.get('abbreviation', ''),
                    'short_name': short_name,
                    'full_name': full_name,
                    'cipher': item_data.get('cipher', ''),
                    'ekps_code': item_data.get('ekpsCode', item_data.get('ekps_code', '')),
                    'kvt_code': item_data.get('kvtCode', item_data.get('kvt_code', '')),
                    'drawing_number': item_data.get('drawingNumber', item_data.get('drawing_number', '')),
                    'spk_nomenclature_type': item_data.get('typeOfNomenclature', item_data.get('type_of_nomenclature', item_data.get('spk_nomenclature_type', '')))
                }
                
                # Создаем и сохраняем новую номенклатуру
                nomenclature = Nomenclature(**nom_data)
                nomenclature.save()
                
                logger.info(f"Создана новая номенклатура с ID: {nomenclature.id}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Создана новая номенклатура',
                    'id': nomenclature.id
                })
        
        # Обработка LSI
        elif data_type == 'lsi':
            # Используем position_name, которое есть в модели IntBus
            position_name = None
            
            # 1. Проверяем position_name в данных
            if 'position_name' in item_data:
                position_name = item_data['position_name']
            
            # 2. Проверяем в заголовках запроса
            elif 'HTTP_X_POSITION_NAME' in request.META:
                position_name = request.META['HTTP_X_POSITION_NAME']
            
            if not position_name:
                logger.error("Отсутствует название LSI (поле position_name)")
                logger.error(f"Доступные поля в item_data: {list(item_data.keys())}")
                logger.error(f"Заголовки: {dict(request.headers)}")
                logger.error(f"META: {request.META}")
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Отсутствует название LSI'
                }, status=400)
            
            logger.info(f"Обработка LSI из IntBus с названием: {position_name}")
            
            # Проверяем существует ли LSI с таким position_name
            try:
                lsi = LSI.objects.get(name=position_name)  # в LSI модели ATOM поле называется 'name'
                logger.info(f"Найдена существующая LSI с ID: {lsi.id}")
                
                # Обновляем существующую запись
                lsi.description = item_data.get('dns', item_data.get('description', lsi.description))
                
                lsi.save()
                logger.info(f"LSI с ID {lsi.id} успешно обновлена")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'LSI успешно обновлена',
                    'id': lsi.id
                })
                
            except LSI.DoesNotExist:
                # Создаем новую LSI
                logger.info(f"Создание новой LSI с названием: {position_name}")
                
                lsi = LSI(
                    name=position_name,  # в LSI модели ATOM поле называется 'name'
                    description=item_data.get('dns', item_data.get('description', ''))
                )
                
                lsi.save()
                logger.info(f"Создана новая LSI с ID: {lsi.id}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Создана новая LSI',
                    'id': lsi.id
                })
        
        # Неизвестный тип данных
        else:
            logger.error(f"Неизвестный тип данных: {data_type}")
            return JsonResponse({
                'status': 'error', 
                'message': f'Неизвестный тип данных: {data_type}'
            }, status=400)
    
    except Exception as e:
        logger.error(f"Ошибка при обработке данных из IntBus: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error', 
            'message': f'Ошибка при обработке данных: {str(e)}'
        }, status=500) 