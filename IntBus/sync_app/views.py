from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
import json
import logging
import traceback
import time
import requests
from nomenclature.models import Nomenclature, LSI, TeamCenterLSI
import re
from django.conf import settings
from django.contrib.auth.decorators import login_required

# Настройка логирования
logger = logging.getLogger(__name__)

# Получаем URL из настроек или используем значения по умолчанию
# Удаляем жестко закодированные URL значения, теперь они берутся из settings.py
# ATOM_SYNC_URL = "http://localhost:8080/api/sync-from-intbus"
# TEAMCENTER_SYNC_URL = "http://localhost:8082/api/sync-from-intbus"

# Создание CSRF-токена
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Вернуть CSRF-токен для клиента.
    Токен включен в ответ как cookie, а также в JSON-ответе.
    """
    csrf_token = get_token(request)
    logger.info(f"Запрошен CSRF-токен: {csrf_token[:8]}...")
    return JsonResponse({
        'status': 'success',
        'message': 'CSRF токен успешно создан',
        'token': csrf_token
    })

# Create your views here.
@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def sync_data(request):
    # Обработка OPTIONS запроса для CORS
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, Authorization'
        response['Access-Control-Max-Age'] = '86400'  # 24 часа
        return response
    
    # Обработка GET запроса для проверки доступности сервиса
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'message': 'API для синхронизации данных доступен',
            'version': '1.0'
        })
    
    # Обработка POST запроса для синхронизации данных
    if request.method == 'POST':
        try:
            # Логируем тип содержимого запроса
            content_type = request.headers.get('Content-Type', '')
            logger.info(f"Получен запрос с Content-Type: {content_type}")
            
            # Логируем заголовки для отладки
            headers_dict = dict(request.headers)
            # Обрезаем длинные значения для логирования
            for key, value in headers_dict.items():
                if isinstance(value, str) and len(value) > 50:
                    headers_dict[key] = value[:50] + '...'
            logger.info(f"Заголовки запроса: {headers_dict}")
            
            # Проверяем наличие тела запроса и логируем его размер
            content_length = request.headers.get('Content-Length', '0')
            transfer_encoding = request.headers.get('Transfer-Encoding', '')
            logger.info(f"Content-Length: {content_length}, Transfer-Encoding: {transfer_encoding}")
            
            # Получаем тело запроса в виде байтов
            if hasattr(request, 'body') and request.body:
                body_bytes = request.body
                logger.info(f"Размер тела запроса: {len(body_bytes)} байт")
                
                # Попытка декодировать bytes в текст
                try:
                    body_text = body_bytes.decode('utf-8', errors='replace')
                    logger.info(f"Тело запроса (первые 500 символов): {body_text[:500]}")
                except Exception as decode_error:
                    logger.error(f"Ошибка декодирования тела запроса: {str(decode_error)}")
                    body_text = str(body_bytes)
                    logger.info(f"Тело как строка байтов: {body_text[:500]}")
            else:
                logger.error("Получено пустое тело запроса")
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Тело запроса пустое'
                }, status=400)
            
            # Пытаемся распарсить JSON
            try:
                # Очищаем текст от возможного мусора в начале и конце
                body_text = body_text.strip()
                
                # Пробуем различные варианты преобразования
                try:
                    # Стандартный парсинг JSON
                    received_data = json.loads(body_text)
                    logger.info("JSON успешно распарсен стандартным способом")
                except json.JSONDecodeError as e1:
                    logger.warning(f"Стандартный парсинг не удался: {e1}, пробуем альтернативные методы")
                    
                    # Второй вариант: если JSON обернут в кавычки или содержит экранированные символы
                    try:
                        # Удаляем лишние символы в начале/конце строки, которые могут быть добавлены
                        clean_text = body_text.strip()
                        if clean_text.startswith('"') and clean_text.endswith('"'):
                            clean_text = clean_text[1:-1]
                        # Заменяем экранированные кавычки на обычные
                        clean_text = clean_text.replace('\\"', '"').replace('\\\\', '\\')
                        received_data = json.loads(clean_text)
                        logger.info("JSON успешно распарсен после очистки")
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Парсинг после очистки не удался: {e2}")
                        
                        # Если в теле запроса есть текст, напоминающий hex/base64-закодированные данные,
                        # возможно это бинарные данные, которые нужно обработать
                        if re.match(r'^[0-9a-fA-F]+$', body_text):
                            logger.info("Тело похоже на hex-строку, пробуем декодировать")
                            # Пробуем декодировать как hex
                            try:
                                hex_decoded = bytes.fromhex(body_text)
                                hex_text = hex_decoded.decode('utf-8', errors='replace')
                                received_data = json.loads(hex_text)
                                logger.info("JSON успешно распарсен после hex-декодирования")
                            except Exception as hex_error:
                                logger.error(f"Ошибка при hex-декодировании: {hex_error}")
                                # Если не удалось декодировать, создаем пустой объект
                                received_data = {"apikey": "default", "sender": "unknown", "data": {}}
                        else:
                            logger.error(f"Не удалось распарсить JSON: {e2}, тело: {body_text[:200]}")
                            return JsonResponse({
                                'status': 'error', 
                                'message': f'Неверный формат JSON данных: {str(e2)}'
                            }, status=400)
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке тела запроса: {str(e)}")
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Ошибка при обработке тела запроса: {str(e)}'
                }, status=400)
            
            # Добавим поддержку для запросов, когда клиент отправляет пустые данные
            if received_data is None:
                logger.warning("Распарсено пустое тело запроса (null), создаем базовый объект")
                received_data = {"apikey": "default", "sender": "unknown", "data": {}}
            
            # Проверяем формат данных
            if not isinstance(received_data, dict):
                logger.error(f"Неверный формат данных. Получен {type(received_data)}, ожидается dict")
                # Попытаемся преобразовать в dict, если это строка, возможно содержащая JSON
                if isinstance(received_data, str):
                    try:
                        received_data = json.loads(received_data)
                        logger.info("Строка успешно преобразована в словарь")
                    except:
                        logger.error("Не удалось преобразовать строку в словарь")
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Неверный формат данных. Ожидается словарь JSON, получена строка'
                    }, status=400)
                else:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Неверный формат данных. Ожидается словарь JSON, получен {type(received_data)}'
                    }, status=400)
            
            # Проверка обязательных полей для нового формата
            required_fields = ['apikey', 'sender', 'data']
            missing_fields = [field for field in required_fields if field not in received_data]
            
            if missing_fields:
                logger.error(f"Отсутствуют обязательные поля: {missing_fields}")
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Отсутствуют обязательные поля: {missing_fields}'
                }, status=400)
            
            # Получаем поля из запроса
            apikey = received_data['apikey']
            sender = received_data['sender']
            data = received_data['data']
            
            logger.info(f"Получены данные: apikey={apikey}, sender={sender}")
            
            # Создаем новую запись в соответствии с типом отправителя
            try:
                if sender.upper() == 'TEAMCENTER':
                    # Проверяем, если это данные ЛСИ (поиск признаков LSI в данных)
                    is_lsi_data = False
                    
                    # Проверяем по полям или структуре данных, что это ЛСИ
                    if isinstance(data, dict):
                        # Проверка по наличию маркера типа
                        if data.get('type') == 'LSI_DATA' or data.get('dataType') == 'lsi':
                            is_lsi_data = True
                        # Проверка по наличию списка элементов LSI
                        elif 'items' in data:
                            is_lsi_data = True
                        # Проверка на типичные поля ЛСИ
                        elif any(key in data for key in ['name', 'description', 'lsi_id', 'lsi_type']):
                            is_lsi_data = True
                    
                    if is_lsi_data:
                        # Создаем запись ЛСИ
                        lsi = LSI(
                            apikey=apikey,
                            sender=sender,
                            data=json.dumps(data) if isinstance(data, dict) else data
                        )
                        lsi.save()
                        logger.info(f"Сохранены данные ЛСИ из TeamCenter с ID: {lsi.id}")
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Данные ЛСИ успешно сохранены',
                            'id': lsi.id
                        })
                    else:
                        # Создаем запись номенклатуры
                        nomenclature = Nomenclature(
                            apikey=apikey,
                            sender=sender,
                            data=json.dumps(data) if isinstance(data, dict) else data
                        )
                        nomenclature.save()
                        logger.info(f"Сохранены данные номенклатуры из TeamCenter с ID: {nomenclature.id}")
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Данные номенклатуры успешно сохранены',
                            'id': nomenclature.id
                        })
                
                elif sender.upper() == 'ATOM':
                    # Определяем тип данных по XML
                    data_str = data if isinstance(data, str) else json.dumps(data)
                    
                    if '<НоменклатураИзделие>' in data_str:
                        # Данные номенклатуры
                        nomenclature = Nomenclature(
                            apikey=apikey,
                            sender=sender,
                            data=data_str
                        )
                        nomenclature.save()
                        logger.info(f"Сохранены данные номенклатуры из ATOM с ID: {nomenclature.id}")
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Данные номенклатуры успешно сохранены',
                            'id': nomenclature.id
                        })
                    
                    elif '<КунПереченьКодовФункциональныхСистем>' in data_str:
                        # Данные LSI
                        lsi = LSI(
                            apikey=apikey,
                            sender=sender,
                            data=data_str
                        )
                        lsi.save()
                        logger.info(f"Сохранены данные ЛСИ из ATOM с ID: {lsi.id}")
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Данные ЛСИ успешно сохранены',
                            'id': lsi.id
                        })
                    else:
                        # Если не удалось определить тип данных, сохраняем как номенклатуру
                        nomenclature = Nomenclature(
                            apikey=apikey,
                            sender=sender,
                            data=data_str
                        )
                        nomenclature.save()
                        logger.info(f"Сохранены неопределенные данные из ATOM как номенклатура с ID: {nomenclature.id}")
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Данные успешно сохранены как номенклатура',
                            'id': nomenclature.id
                        })
                else:
                    # Если отправитель не определен, сохраняем данные как номенклатуру
                    nomenclature = Nomenclature(
                        apikey=apikey,
                        sender=sender,
                        data=json.dumps(data) if isinstance(data, dict) else data
                    )
                    nomenclature.save()
                    logger.info(f"Сохранены данные от неизвестного отправителя '{sender}' с ID: {nomenclature.id}")
                    
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Данные успешно сохранены',
                        'id': nomenclature.id
                    })
            
            except Exception as e:
                logger.error(f"Ошибка при сохранении данных: {str(e)}")
                logger.error(traceback.format_exc())
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Ошибка при сохранении данных: {str(e)}'
                }, status=500)
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
            return JsonResponse({
                'status': 'error', 
                'message': f'Неверный формат JSON данных: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'status': 'error', 
                'message': f'Непредвиденная ошибка: {str(e)}'
            }, status=500)
    
    logger.warning(f"Получен неподдерживаемый метод: {request.method}")
    return JsonResponse({
        'status': 'error', 
        'message': 'Метод не поддерживается'
    }, status=405)

@login_required
def send_to_atom(request):
    """
    Получает данные и отправляет их в ATOM.
    Проверяет наличие обязательных полей, особенно 'name'.
    Обрабатывает данные перед отправкой.
    """
    logger.info(f"Получен запрос на отправку данных в ATOM")
    
    try:
        # Получаем данные из запроса
        try:
            if request.body:
                # Обрабатываем тело запроса, удаляя возможные проблемные символы
                body_text = request.body.decode('utf-8')
                # Удаляем null-байты если они есть
                if '\x00' in body_text:
                    body_text = body_text.replace('\x00', '')
                    logger.warning("Обнаружены нулевые байты в теле запроса, они были удалены")
                
                # Удаляем BOM если он есть
                if body_text.startswith('\ufeff'):
                    body_text = body_text[1:]
                    logger.warning("Обнаружен BOM-маркер в теле запроса, он был удален")
                
                data = json.loads(body_text)
                logger.info(f"Получены данные для отправки в ATOM: {type(data)}")
            else:
                logger.warning("Тело запроса пустое")
                return JsonResponse({'status': 'error', 'message': 'Тело запроса пустое'}, status=400)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Ошибка декодирования JSON: {str(e)}'}, status=400)
        
        # Проверяем что данные имеют корректный формат
        if not isinstance(data, dict):
            error_msg = f"Неверный формат данных: ожидается dict, получен {type(data)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        
        # Проверяем и подготавливаем структуру данных
        if 'data' not in data:
            logger.warning("Поле 'data' отсутствует в запросе, создаем его")
            data['data'] = {}
        
        # Проверяем что data является словарем
        if not isinstance(data['data'], dict):
            logger.warning(f"Поле 'data' имеет неправильный тип: {type(data['data'])}, преобразуем в словарь")
            try:
                if isinstance(data['data'], str):
                    data['data'] = json.loads(data['data'])
                else:
                    data['data'] = {}
            except json.JSONDecodeError:
                logger.error("Не удалось преобразовать поле 'data' в словарь")
                data['data'] = {}
        
        # Проверяем наличие поля name и обрабатываем его
        name_found = False
        
        # Проверяем наличие name в корне запроса
        if 'name' in data and data['name']:
            name_found = True
        
        # Проверяем наличие name в данных
        if not name_found and 'data' in data and isinstance(data['data'], dict):
            # Проверяем наличие name в данных
            if 'name' in data['data'] and data['data']['name']:
                data['name'] = data['data']['name']
                name_found = True
            # Если name отсутствует или пустое, пробуем получить из других полей
            else:
                possible_name_fields = [
                    'НаименованиеПолное', 'fullName', 'short_name', 
                    'НаименованиеКраткое', 'shortName', 'полное_наименование'
                ]
                
                for field in possible_name_fields:
                    if field in data['data'] and data['data'][field]:
                        data['data']['name'] = data['data'][field]
                        data['name'] = data['data'][field]
                        name_found = True
                        logger.info(f"Имя взято из поля {field}: {data['name']}")
                        break
        
        # Если не нашли подходящего поля, генерируем имя
        if not name_found:
            import time
            timestamp = int(time.time())
            default_name = f"Номенклатура_INTBUS_{timestamp}"
            data['data']['name'] = default_name
            data['name'] = default_name
            logger.info(f"Сгенерировано имя: {default_name}")
        
        # Проверяем наличие внутреннего кода (internal_code)
        code_found = False
        
        # Проверяем наличие code в корне запроса
        if 'code' in data and data['code']:
            code_found = True
            # Убеждаемся что код есть и в data
            if 'data' in data and isinstance(data['data'], dict):
                data['data']['internal_code'] = data['code']
        
        # Проверяем наличие кода в данных
        if not code_found and 'data' in data and isinstance(data['data'], dict):
            possible_code_fields = [
                'internal_code', 'code', 'КодВнутренний', 'internalCode', 'код'
            ]
            
            for field in possible_code_fields:
                if field in data['data'] and data['data'][field]:
                    # Устанавливаем internal_code
                    data['data']['internal_code'] = data['data'][field]
                    # Добавляем code в корень запроса
                    data['code'] = data['data'][field]
                    code_found = True
                    logger.info(f"Код взят из поля {field}: {data['code']}")
                    break
        
        # Если не нашли код, генерируем его
        if not code_found:
            import time
            timestamp = int(time.time())
            default_code = f"CODE_INTBUS_{timestamp}"
            data['data']['internal_code'] = default_code
            data['code'] = default_code
            logger.info(f"Сгенерирован код: {default_code}")
        
        # Добавляем тип данных если отсутствует
        if 'dataType' not in data:
            data['dataType'] = 'nomenclature'
            logger.info("Добавлен тип данных: nomenclature")
        
        # Добавляем отправителя если отсутствует
        if 'sender' not in data:
            data['sender'] = 'INTBUS'
            logger.info("Добавлен отправитель: INTBUS")
        
        # Добавляем API ключ если отсутствует
        if 'apikey' not in data:
            data['apikey'] = settings.ATOM_API_KEY
            logger.info(f"Добавлен API ключ из настроек")
        
        # Подготавливаем заголовки
        headers = {'Content-Type': 'application/json'}
        
        # Получаем URL для отправки
        url = settings.ATOM_SYNC_URL
        if not url:
            logger.error("URL для отправки в ATOM не настроен в settings")
            return JsonResponse({'status': 'error', 'message': 'URL для отправки в ATOM не настроен'}, status=500)
        
        logger.info(f"Отправка данных в ATOM на URL: {url}")
        logger.debug(f"Данные для отправки: {json.dumps(data)[:1000]}...")
        
        # Отправляем запрос в ATOM
        try:
            response = requests.post(url, json=data, headers=headers)
            
            # Обрабатываем ответ
            logger.info(f"Получен ответ от ATOM: статус={response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    logger.info(f"Успешный ответ от ATOM (JSON): {json.dumps(response_data)[:500]}")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Данные успешно отправлены в ATOM',
                        'response': response_data
                    })
                except json.JSONDecodeError:
                    logger.info(f"Успешный ответ от ATOM (не JSON): {response.text[:500]}")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Данные успешно отправлены в ATOM',
                        'response': {'text': response.text[:1000] if response.text else ''}
                    })
            else:
                error_msg = f"Ошибка при отправке в ATOM: {response.status_code} - {response.text[:1000]}"
                logger.error(error_msg)
                return JsonResponse({'status': 'error', 'message': error_msg}, status=500)
        except requests.RequestException as e:
            error_msg = f"Ошибка сетевого соединения при отправке в ATOM: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=500)
            
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при отправке данных в ATOM: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JsonResponse({'status': 'error', 'message': error_msg}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_to_teamcenter(request):
    """
    Отправка данных из IntBus в TeamCenter
    """
    try:
        # Получаем данные запроса
        data = json.loads(request.body)
        
        # Получаем исходные данные и целевую систему
        source_id = data.get('source_id')
        source_type = data.get('source_type', 'nomenclature')  # По умолчанию - номенклатура
        
        if not source_id:
            return JsonResponse({'status': 'error', 'message': 'Отсутствует идентификатор исходных данных'}, status=400)
        
        # Получаем исходный объект из базы
        source_data = None
        if source_type.lower() == 'nomenclature':
            try:
                source_data = Nomenclature.objects.get(id=source_id)
            except Nomenclature.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'Номенклатура с ID={source_id} не найдена'}, status=404)
        elif source_type.lower() == 'lsi':
            try:
                source_data = LSI.objects.get(id=source_id)
            except LSI.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'ЛСИ с ID={source_id} не найдена'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестный тип данных: {source_type}'}, status=400)
        
        # Определяем тип данных для TeamCenter (тип данных используется по-разному в разных системах)
        tc_data_type = 'LSI_DATA' if source_type.lower() == 'lsi' else 'NOMENCLATURE_DATA'
        
        # Если отправитель данных тот же (TeamCenter), то создаем JSON файл
        if source_data.sender.upper() == 'TEAMCENTER':
            # Разбираем данные источника с корректной обработкой JSON
            source_data_dict = None
            if isinstance(source_data.data, str):
                try:
                    # Очищаем строку от BOM и других возможных артефактов
                    clean_data = source_data.data.strip()
                    if clean_data.startswith('\ufeff'):  # Удаляем BOM маркер если есть
                        clean_data = clean_data[1:]
                    
                    # Пробуем парсить как JSON с дополнительными проверками
                    if clean_data:
                        source_data_dict = json.loads(clean_data)
                    else:
                        source_data_dict = {}
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка парсинга JSON при отправке в TeamCenter: {str(e)}")
                    logger.error(f"Начало проблемной строки: {clean_data[:50] if clean_data else 'пусто'}")
                    # Если данные не в формате JSON или имеют ошибки, создаем базовую структуру
                    source_data_dict = {
                        'rawData': source_data.data,
                        'parseError': str(e)
                    }
            else:
                source_data_dict = source_data.data
            
            # Создаем JSON с атрибутами для TeamCenter (включая тип)
            result_json = {
                'apikey': source_data.apikey,
                'sender': source_data.sender,  # Используем оригинального отправителя вместо 'INTBUS'
                'dataType': tc_data_type,  # Для TeamCenter используем поле 'dataType' вместо 'type'
                'data': source_data_dict
            }
            
            # Возвращаем готовый JSON файл
            return JsonResponse({
                'status': 'success',
                'message': 'Данные успешно подготовлены для TeamCenter',
                'json_data': result_json
            })
        else:
            # Если отправитель другой (не TeamCenter), создаем базовый JSON с сохранением исходного отправителя
            # Получаем исходные данные
            source_data_dict = None
            if isinstance(source_data.data, str):
                try:
                    clean_data = source_data.data.strip()
                    if clean_data.startswith('\ufeff'):
                        clean_data = clean_data[1:]
                    
                    if clean_data:
                        source_data_dict = json.loads(clean_data)
                    else:
                        source_data_dict = {}
                except json.JSONDecodeError:
                    source_data_dict = {'rawData': source_data.data}
            else:
                source_data_dict = source_data.data
                
            # Создаем базовый JSON для маппинга
            result_json = {
                'apikey': source_data.apikey,
                'sender': source_data.sender,  # Сохраняем оригинального отправителя
                'dataType': tc_data_type,
                'data': source_data_dict
            }
            
            return JsonResponse({
                'status': 'success',
                'message': 'Данные для маппинга подготовлены',
                'source_id': source_id,
                'source_type': source_type,
                'target': 'TEAMCENTER',
                'requires_mapping': True,
                'json_data': result_json
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Некорректный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при отправке в TeamCenter: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Ошибка: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_mapping_table(request):
    """
    Получение таблицы для маппинга атрибутов при отправке в другую систему
    """
    try:
        # Получаем данные запроса
        data = json.loads(request.body)
        
        # Получаем исходные данные и целевую систему
        source_id = data.get('source_id')
        source_type = data.get('source_type', 'nomenclature')
        target = data.get('target', '').upper()  # ATOM или TEAMCENTER
        
        if not source_id or not target:
            return JsonResponse({
                'status': 'error', 
                'message': 'Отсутствуют обязательные параметры: source_id или target'
            }, status=400)
        
        # Получаем исходный объект из базы
        source_data = None
        if source_type.lower() == 'nomenclature':
            try:
                source_data = Nomenclature.objects.get(id=source_id)
            except Nomenclature.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'Номенклатура с ID={source_id} не найдена'}, status=404)
        elif source_type.lower() == 'lsi':
            try:
                source_data = LSI.objects.get(id=source_id)
            except LSI.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'ЛСИ с ID={source_id} не найдена'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестный тип данных: {source_type}'}, status=400)
        
        # Получаем шаблонный объект целевой системы для анализа структуры
        target_template = None
        if target == 'ATOM':
            # Ищем последний объект от ATOM того же типа (номенклатура или ЛСИ)
            if source_type.lower() == 'nomenclature':
                target_templates = Nomenclature.objects.filter(sender='ATOM').order_by('-id')
                if target_templates.exists():
                    target_template = target_templates.first()
            else:  # LSI
                target_templates = LSI.objects.filter(sender='ATOM').order_by('-id')
                if target_templates.exists():
                    target_template = target_templates.first()
        elif target == 'TEAMCENTER':
            # Ищем последний объект от TeamCenter того же типа (номенклатура или ЛСИ)
            if source_type.lower() == 'nomenclature':
                target_templates = Nomenclature.objects.filter(sender='TEAMCENTER').order_by('-id')
                if target_templates.exists():
                    target_template = target_templates.first()
            else:  # LSI
                target_templates = LSI.objects.filter(sender='TEAMCENTER').order_by('-id')
                if target_templates.exists():
                    target_template = target_templates.first()
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестная целевая система: {target}'}, status=400)
        
        if not target_template:
            return JsonResponse({
                'status': 'error', 
                'message': f'Не найден шаблон данных для целевой системы {target}'
            }, status=404)
        
        # Извлекаем атрибуты (теги) из источника
        source_tags = []
        if isinstance(source_data.data, str):
            try:
                source_data_dict = json.loads(source_data.data)
                if isinstance(source_data_dict, dict):
                    source_tags = list(source_data_dict.keys())
                    # Если есть вложенные словари, добавляем их ключи с префиксом
                    for key, value in source_data_dict.items():
                        if isinstance(value, dict):
                            for nested_key in value.keys():
                                source_tags.append(f"{key}.{nested_key}")
            except json.JSONDecodeError:
                # Если не JSON, пробуем извлечь теги из текста (например, XML)
                # Упрощенный алгоритм извлечения тегов из XML
                tags = re.findall(r'<(\w+)>', source_data.data)
                source_tags = list(set(tags))  # Убираем дубликаты
        
        # Извлекаем атрибуты (теги) из целевого шаблона
        target_tags = []
        if isinstance(target_template.data, str):
            try:
                target_data_dict = json.loads(target_template.data)
                if isinstance(target_data_dict, dict):
                    target_tags = list(target_data_dict.keys())
                    # Если есть вложенные словари, добавляем их ключи с префиксом
                    for key, value in target_data_dict.items():
                        if isinstance(value, dict):
                            for nested_key in value.keys():
                                target_tags.append(f"{key}.{nested_key}")
            except json.JSONDecodeError:
                # Если не JSON, пробуем извлечь теги из текста (например, XML)
                # Упрощенный алгоритм извлечения тегов из XML
                tags = re.findall(r'<(\w+)>', target_template.data)
                target_tags = list(set(tags))  # Убираем дубликаты
        
        # Формируем данные для таблицы маппинга
        mapping_table = {
            'source_tags': source_tags,
            'target_tags': target_tags,
            'source_id': source_id,
            'source_type': source_type,
            'target': target
        }
        
        return JsonResponse({
            'status': 'success',
            'mapping_table': mapping_table
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Некорректный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при подготовке таблицы маппинга: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Ошибка: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_connection(request):
    """
    Проверка подключения и доступности целевых систем ATOM и TeamCenter.
    Выполняет реальные HTTP запросы к API систем.
    """
    try:
        target = request.GET.get('target', '').upper()
        sender = request.GET.get('sender', 'INTBUS').upper()  # Получаем отправителя из параметров запроса
        
        logger.info(f"Проверка соединения с target={target}, sender={sender}")
        
        # Базовое состояние для ответа
        connection_status = {
            'ATOM': {
                'status': 'unknown',
                'message': 'Проверка не выполнялась'
            },
            'TEAMCENTER': {
                'status': 'unknown',
                'message': 'Проверка не выполнялась'
            }
        }
        
        # Проверяем только запрошенную систему, или обе если параметр не указан
        if not target or target == 'ATOM':
            # Создаем тестовое сообщение для ATOM
            test_data = {
                'apikey': settings.ATOM_API_KEY,
                'sender': sender,  # Используем указанного отправителя
                'dataType': 'test',
                'data': {'test': True, 'timestamp': int(time.time())}
            }
            
            try:
                # Получаем URL для ATOM из настроек
                atom_url = settings.ATOM_SYNC_URL
                if not atom_url:
                    raise ValueError("URL для ATOM не настроен в конфигурации")
                
                logger.info(f"Проверка соединения с ATOM по адресу: {atom_url}, отправитель: {sender}")
                
                # Выполняем HTTP запрос с таймаутом 5 секунд
                response = requests.post(
                    atom_url,
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                
                # Анализируем ответ
                if response.status_code in [200, 201]:
                    connection_status['ATOM'] = {
                        'status': 'success',
                        'message': f'Соединение с ATOM успешно. Код ответа: {response.status_code}',
                        'response': response.text[:200] if response.text else ''
                    }
                    logger.info(f"Соединение с ATOM успешно. Код ответа: {response.status_code}")
                else:
                    connection_status['ATOM'] = {
                        'status': 'error',
                        'message': f'Ошибка соединения с ATOM. Код ответа: {response.status_code}',
                        'response': response.text[:200] if response.text else ''
                    }
                    logger.error(f"Ошибка соединения с ATOM. Код: {response.status_code}, ответ: {response.text[:200]}")
            except requests.RequestException as e:
                logger.error(f"Ошибка HTTP запроса к ATOM: {str(e)}")
                connection_status['ATOM'] = {
                    'status': 'error',
                    'message': f'Ошибка соединения с ATOM: {str(e)}',
                    'error_type': 'request_error'
                }
            except Exception as e:
                logger.error(f"Неожиданная ошибка при проверке соединения с ATOM: {str(e)}")
                connection_status['ATOM'] = {
                    'status': 'error',
                    'message': f'Ошибка: {str(e)}',
                    'error_type': 'unexpected_error'
                }
        
        if not target or target == 'TEAMCENTER':
            # Создаем тестовое сообщение для TeamCenter
            test_data = {
                'apikey': settings.TEAMCENTER_API_KEY,
                'sender': sender,  # Используем указанного отправителя
                'dataType': 'TEST_DATA',
                'data': {'test': True, 'timestamp': int(time.time())}
            }
            
            try:
                # Получаем URL для TeamCenter из настроек
                teamcenter_url = settings.TEAMCENTER_SYNC_URL
                if not teamcenter_url:
                    raise ValueError("URL для TeamCenter не настроен в конфигурации")
                
                logger.info(f"Проверка соединения с TeamCenter по адресу: {teamcenter_url}, отправитель: {sender}")
                
                # Выполняем HTTP запрос с таймаутом 5 секунд
                response = requests.post(
                    teamcenter_url,
                    json=test_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                
                # Анализируем ответ
                if response.status_code in [200, 201]:
                    connection_status['TEAMCENTER'] = {
                        'status': 'success',
                        'message': f'Соединение с TeamCenter успешно. Код ответа: {response.status_code}',
                        'response': response.text[:200] if response.text else ''
                    }
                    logger.info(f"Соединение с TeamCenter успешно. Код ответа: {response.status_code}")
                else:
                    connection_status['TEAMCENTER'] = {
                        'status': 'error',
                        'message': f'Ошибка соединения с TeamCenter. Код ответа: {response.status_code}',
                        'response': response.text[:200] if response.text else ''
                    }
                    logger.error(f"Ошибка соединения с TeamCenter. Код: {response.status_code}, ответ: {response.text[:200]}")
            except requests.RequestException as e:
                logger.error(f"Ошибка HTTP запроса к TeamCenter: {str(e)}")
                connection_status['TEAMCENTER'] = {
                    'status': 'error',
                    'message': f'Ошибка соединения с TeamCenter: {str(e)}',
                    'error_type': 'request_error'
                }
            except Exception as e:
                logger.error(f"Неожиданная ошибка при проверке соединения с TeamCenter: {str(e)}")
                connection_status['TEAMCENTER'] = {
                    'status': 'error',
                    'message': f'Ошибка: {str(e)}',
                    'error_type': 'unexpected_error'
                }
        
        # Возвращаем статус соединения с системами
        if target:
            # Если запрошена одна система, возвращаем только её статус
            if target in connection_status:
                return JsonResponse({
                    'status': 'success',
                    'target': target,
                    'sender': sender,
                    'connection': connection_status[target]
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Неизвестная целевая система: {target}'
                }, status=400)
        else:
            # Если не указана целевая система, возвращаем статус обеих систем
            return JsonResponse({
                'status': 'success',
                'sender': sender,
                'connections': connection_status
            })
        
    except Exception as e:
        logger.error(f"Ошибка при проверке соединения: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при проверке соединения: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def apply_mapping(request):
    """
    Применение маппинга полей и подготовка данных к отправке
    """
    try:
        # Получаем данные запроса
        data = json.loads(request.body)
        
        # Получаем исходные данные, целевую систему и маппинг полей
        source_id = data.get('source_id')
        source_type = data.get('source_type', 'nomenclature')
        target = data.get('target', '').upper()  # ATOM или TEAMCENTER
        field_mapping = data.get('field_mapping', {})
        
        if not source_id or not target:
            return JsonResponse({
                'status': 'error',
                'message': 'Отсутствуют обязательные параметры: source_id или target'
            }, status=400)
        
        if not field_mapping:
            return JsonResponse({'status': 'error', 'message': 'Отсутствует маппинг полей'}, status=400)
        
        # Получаем исходный объект из базы
        source_data = None
        if source_type.lower() == 'nomenclature':
            try:
                source_data = Nomenclature.objects.get(id=source_id)
            except Nomenclature.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'Номенклатура с ID={source_id} не найдена'}, status=404)
        elif source_type.lower() == 'lsi':
            try:
                source_data = LSI.objects.get(id=source_id)
            except LSI.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'ЛСИ с ID={source_id} не найдена'}, status=404)
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестный тип данных: {source_type}'}, status=400)
        
        # Получаем данные объекта
        source_data_dict = None
        if isinstance(source_data.data, str):
            try:
                clean_data = source_data.data.strip()
                if clean_data.startswith('\ufeff'):  # Удаляем BOM маркер если есть
                    clean_data = clean_data[1:]
                
                if clean_data:
                    source_data_dict = json.loads(clean_data)
                else:
                    source_data_dict = {}
            except json.JSONDecodeError:
                logger.error(f"Ошибка парсинга JSON, создаем минимальную структуру для {source_type}")
                # Создаем минимальную структуру
                source_data_dict = {
                    'name': f'{source_type.title()} {source_id}',
                    'code': f'{source_type[0].upper()}{source_id}'
                }
        else:
            source_data_dict = source_data.data
        
        if not source_data_dict:
            return JsonResponse({'status': 'error', 'message': 'Не удалось получить данные источника'}, status=400)
        
        # Применяем маппинг полей
        target_data_dict = {}
        for source_field, target_field in field_mapping.items():
            # Проверяем на наличие вложенных полей (например, field1.field2)
            if '.' in source_field:
                # Обработка вложенных полей в источнике
                fields = source_field.split('.')
                value = source_data_dict
                for field in fields:
                    if isinstance(value, dict) and field in value:
                        value = value[field]
                    else:
                        value = None
                        break
                
                if value is not None:
                    # Проверяем на вложенные поля в целевом объекте
                    if '.' in target_field:
                        # Создаем вложенные словари для целевого поля
                        target_fields = target_field.split('.')
                        current_dict = target_data_dict
                        
                        # Создаем структуру вложенных словарей
                        for i, field in enumerate(target_fields[:-1]):
                            if field not in current_dict:
                                current_dict[field] = {}
                            current_dict = current_dict[field]
                        
                        # Устанавливаем значение в самое глубокое поле
                        current_dict[target_fields[-1]] = value
                    else:
                        # Простое поле в целевом объекте
                        target_data_dict[target_field] = value
            elif source_field in source_data_dict:
                # Простое поле в источнике
                if '.' in target_field:
                    # Но вложенное в целевом объекте
                    target_fields = target_field.split('.')
                    current_dict = target_data_dict
                    
                    # Создаем структуру вложенных словарей
                    for i, field in enumerate(target_fields[:-1]):
                        if field not in current_dict:
                            current_dict[field] = {}
                        current_dict = current_dict[field]
                    
                    # Устанавливаем значение
                    current_dict[target_fields[-1]] = source_data_dict[source_field]
                else:
                    # Простое поле в обоих объектах
                    target_data_dict[target_field] = source_data_dict[source_field]
        
        # Для TeamCenter убеждаемся, что поле NAME в верхнем регистре существует
        if target == 'TEAMCENTER':
            if 'name' in target_data_dict and target_data_dict['name']:
                # Если есть поле name, дублируем его в NAME
                target_data_dict['NAME'] = target_data_dict['name']
                logger.debug(f"Добавлено поле NAME из name: {target_data_dict['name']}")
            elif not target_data_dict.get('NAME'):
                # Если нет ни name, ни NAME, создаем значение по умолчанию
                default_name = f"{source_type.title()}_{source_id}"
                target_data_dict['NAME'] = default_name
                if not target_data_dict.get('name'):
                    target_data_dict['name'] = default_name
                logger.warning(f"Создано поле NAME со значением по умолчанию: {default_name}")
        
        # Добавляем обязательные поля в зависимости от целевой системы
        if target == 'ATOM':
            result_json = {
                'apikey': source_data.apikey,
                'sender': 'INTBUS',
                'dataType': source_type.lower(),
                'data': target_data_dict
            }
        elif target == 'TEAMCENTER':
            tc_data_type = 'LSI_DATA' if source_type.lower() == 'lsi' else 'NOMENCLATURE_DATA'
            result_json = {
                'apikey': source_data.apikey,
                'sender': 'INTBUS',
                'dataType': tc_data_type,
                'data': target_data_dict
            }
            
            # Дополнительная проверка для TeamCenter - дублируем NAME на верхний уровень
            if 'NAME' in target_data_dict:
                result_json['NAME'] = target_data_dict['NAME']
            
            # Логирование для отладки
            logger.debug(f"Подготовленные данные для TeamCenter: {json.dumps(result_json, indent=2, ensure_ascii=False)}")
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестная целевая система: {target}'}, status=400)
        
        # Возвращаем подготовленные данные
        return JsonResponse({
            'status': 'success',
            'message': f'Маппинг успешно применен для {target}',
            'json_data': result_json
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Некорректный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при применении маппинга: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Ошибка: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def direct_send_to_target(request):
    """
    Прямая отправка данных из IntBus в целевую систему с возможностью указания отправителя
    """
    try:
        # Получаем данные запроса
        data = json.loads(request.body)
        
        # Получаем целевую систему и отправителя
        target = data.get('target', '').upper()
        sender = data.get('sender', 'INTBUS').upper()
        payload = data.get('data', {})
        
        logger.info(f"Прямая отправка данных в {target}, отправитель: {sender}")
        
        if not target:
            return JsonResponse({'status': 'error', 'message': 'Не указана целевая система'}, status=400)
        
        if not payload:
            return JsonResponse({'status': 'error', 'message': 'Отсутствуют данные для отправки'}, status=400)
        
        # Для TeamCenter убеждаемся, что поле NAME в верхнем регистре существует
        if target == 'TEAMCENTER':
            if 'name' in payload and payload['name']:
                # Если есть поле name, дублируем его в NAME
                payload['NAME'] = payload['name']
                logger.debug(f"В прямой отправке добавлено поле NAME из name: {payload['name']}")
            elif not payload.get('NAME'):
                # Если нет ни name, ни NAME, создаем значение по умолчанию
                default_name = f"DirectSend_{int(time.time())}"
                payload['NAME'] = default_name
                if not payload.get('name'):
                    payload['name'] = default_name
                logger.warning(f"В прямой отправке создано поле NAME со значением по умолчанию: {default_name}")
        
        # Формируем данные для отправки
        send_data = {
            'apikey': settings.ATOM_API_KEY if target == 'ATOM' else settings.TEAMCENTER_API_KEY,
            'sender': sender,
            'dataType': data.get('dataType', 'direct'),
            'data': payload
        }
        
        # Для TeamCenter дублируем NAME на верхний уровень
        if target == 'TEAMCENTER' and 'NAME' in payload:
            send_data['NAME'] = payload['NAME']
            logger.debug(f"NAME дублировано на верхний уровень: {payload['NAME']}")
            
        # Дополнительное логирование для TeamCenter
        if target == 'TEAMCENTER':
            logger.debug(f"Отправляемые данные в TeamCenter: {json.dumps(send_data, indent=2, ensure_ascii=False)}")
        
        # Получаем URL для целевой системы
        if target == 'ATOM':
            target_url = settings.ATOM_SYNC_URL
            if not target_url:
                return JsonResponse({'status': 'error', 'message': 'URL для ATOM не настроен в конфигурации'}, status=500)
        elif target == 'TEAMCENTER':
            target_url = settings.TEAMCENTER_SYNC_URL
            if not target_url:
                return JsonResponse({'status': 'error', 'message': 'URL для TeamCenter не настроен в конфигурации'}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестная целевая система: {target}'}, status=400)
        
        logger.info(f"Отправка данных на URL: {target_url}")
        
        # Отправляем запрос в целевую систему
        try:
            response = requests.post(
                target_url,
                json=send_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Анализируем ответ
            if response.status_code in [200, 201]:
                logger.info(f"Данные успешно отправлены в {target}. Код ответа: {response.status_code}")
                
                # Сохраняем копию отправленных данных в IntBus
                if data.get('save_copy', True):
                    try:
                        data_model = None
                        if 'lsi' in data.get('dataType', '').lower():
                            data_model = LSI(
                                apikey=send_data['apikey'],
                                sender=sender,
                                data=json.dumps(payload)
                            )
                            data_model.save()
                            logger.info(f"Сохранена копия отправленных данных ЛСИ с ID: {data_model.id}")
                        else:
                            data_model = Nomenclature(
                                apikey=send_data['apikey'],
                                sender=sender,
                                data=json.dumps(payload)
                            )
                            data_model.save()
                            logger.info(f"Сохранена копия отправленных данных номенклатуры с ID: {data_model.id}")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении копии данных: {str(e)}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Данные успешно отправлены в {target}',
                    'response_code': response.status_code,
                    'response': response.text[:200] if response.text else ''
                })
            else:
                logger.error(f"Ошибка при отправке данных в {target}. Код: {response.status_code}, ответ: {response.text[:200]}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Ошибка при отправке данных. Код ответа: {response.status_code}',
                    'response': response.text[:200] if response.text else ''
                }, status=500)
        except requests.RequestException as e:
            logger.error(f"Ошибка HTTP запроса: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка соединения: {str(e)}',
                'error_type': 'request_error'
            }, status=500)
    
    except json.JSONDecodeError as e:
        return JsonResponse({'status': 'error', 'message': f'Некорректный формат JSON: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при прямой отправке данных: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Ошибка: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def teamcenter_lsi_sync(request):
    """
    Специальный эндпоинт для приема данных LSI от TeamCenter,
    использующий отдельную модель TeamCenterLSI.
    """
    try:
        # Получаем данные запроса
        try:
            request_data = json.loads(request.body)
            logger.info(f"Получены данные от TeamCenter: {request_data.keys()}")
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Некорректный формат JSON'}, status=400)
        
        # Проверяем, что запрос содержит все необходимые поля
        if not all(k in request_data for k in ['source', 'dataType', 'data']):
            return JsonResponse({
                'status': 'error',
                'message': 'Отсутствуют обязательные поля: source, dataType, data'
            }, status=400)
        
        # Проверяем, что source и dataType соответствуют ожидаемым значениям
        source = request_data.get('source')
        data_type = request_data.get('dataType')
        
        if source != 'TeamCenter':
            return JsonResponse({
                'status': 'error',
                'message': f'Неверный источник: {source}, ожидался TeamCenter'
            }, status=400)
            
        if data_type != 'lsi':
            return JsonResponse({
                'status': 'error',
                'message': f'Неверный тип данных: {data_type}, ожидался lsi'
            }, status=400)
        
        # Получаем данные LSI
        lsi_data = request_data.get('data', {})
        
        # Проверяем обязательное поле position_name
        if 'position_name' not in lsi_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Отсутствует обязательное поле position_name в данных LSI'
            }, status=400)
        
        # Создаем запись TeamCenterLSI
        tc_lsi = TeamCenterLSI(
            apikey=request_data.get('apikey', 'default_apikey'),
            sender='TeamCenter',
            position_name=lsi_data.get('position_name'),
            uuid=lsi_data.get('uuid'),
            drawing_number=lsi_data.get('drawing_number'),
            dns=lsi_data.get('dns'),
            code_1=lsi_data.get('code_1'),
            code_2=lsi_data.get('code_2'),
            code_3=lsi_data.get('code_3'),
            code_4=lsi_data.get('code_4'),
            code_5=lsi_data.get('code_5'),
            cipher=lsi_data.get('cipher'),
            deletion_mark=lsi_data.get('deletion_mark', False),
            group_indicator=lsi_data.get('group_indicator'),
            lkn=lsi_data.get('lkn'),
            modification_code=lsi_data.get('modification_code'),
            object_type_code=lsi_data.get('object_type_code'),
            parent_record_id=lsi_data.get('parent_record_id'),
            position_code=lsi_data.get('position_code'),
            position_in_staff_structure_type=lsi_data.get('position_in_staff_structure_type'),
            quantity=lsi_data.get('quantity'),
            specialty=lsi_data.get('specialty')
        )
        
        # Сохраняем дополнительные данные в extra_data
        extra_data = {}
        for key, value in lsi_data.items():
            if not hasattr(tc_lsi, key):
                extra_data[key] = value
        
        if extra_data:
            tc_lsi.extra_data = json.dumps(extra_data)
        
        # Сохраняем запись
        tc_lsi.save()
        
        logger.info(f"Сохранены данные LSI из TeamCenter в специальную модель с ID: {tc_lsi.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Данные LSI из TeamCenter успешно сохранены',
            'id': tc_lsi.id
        })
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса от TeamCenter: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при обработке запроса: {str(e)}'
        }, status=500)

