from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
import json
import logging
import traceback
from nomenclature.models import Nomenclature, LSI
import re

# Настройка логирования
logger = logging.getLogger(__name__)

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

@csrf_exempt
@require_http_methods(["POST"])
def send_to_atom(request):
    """
    Отправка данных из IntBus в ATOM
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
        
        # Определяем тип данных для отправки
        data_type = 'nomenclature' if source_type.lower() == 'nomenclature' else 'lsi'
        
        # Если отправитель данных тот же (ATOM), то создаем JSON файл
        if source_data.sender.upper() == 'ATOM':
            # Разбираем данные источника (преобразуем из строки в структуру данных)
            source_data_dict = None
            if isinstance(source_data.data, str):
                try:
                    # Пробуем парсить как JSON
                    source_data_dict = json.loads(source_data.data)
                except json.JSONDecodeError:
                    # Если данные не в формате JSON, сохраняем как есть (XML или другой формат)
                    source_data_dict = {'xmlData': source_data.data}
            else:
                source_data_dict = source_data.data
            
            # Создаем JSON с обязательными атрибутами для ATOM
            result_json = {
                'apikey': source_data.apikey,
                'sender': 'INTBUS',
                'dataType': data_type,  # Добавляем dataType - обязательное поле для ATOM
                'data': source_data_dict
            }
            
            # Возвращаем готовый JSON файл
            return JsonResponse({
                'status': 'success',
                'message': 'Данные успешно подготовлены для ATOM',
                'json_data': result_json
            })
        else:
            # Если отправитель другой (не ATOM), нужно предоставить данные для маппинга
            return JsonResponse({
                'status': 'success',
                'message': 'Требуется маппинг данных',
                'source_id': source_id,
                'source_type': source_type,
                'target': 'ATOM',
                'requires_mapping': True
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Некорректный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при отправке в ATOM: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Ошибка: {str(e)}'}, status=500)

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
                'sender': 'INTBUS',
                'type': tc_data_type,  # Для TeamCenter используем поле 'type'
                'data': source_data_dict
            }
            
            # Возвращаем готовый JSON файл
            return JsonResponse({
                'status': 'success',
                'message': 'Данные успешно подготовлены для TeamCenter',
                'json_data': result_json
            })
        else:
            # Если отправитель другой (не TeamCenter), нужно предоставить данные для маппинга
            return JsonResponse({
                'status': 'success',
                'message': 'Требуется маппинг данных',
                'source_id': source_id,
                'source_type': source_type,
                'target': 'TEAMCENTER',
                'requires_mapping': True
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
    """
    try:
        target = request.GET.get('target', '').upper()
        
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
                'apikey': 'test_key',
                'sender': 'INTBUS',
                'dataType': 'test',
                'data': {'test': True}
            }
            
            try:
                # Здесь должен быть реальный запрос к ATOM API
                # Заменить URL на реальный
                logger.info("Проверка соединения с ATOM...")
                
                # Пример проверки - имитация
                # В реальном коде здесь должен быть HTTP запрос к ATOM
                connection_status['ATOM'] = {
                    'status': 'success',
                    'message': 'Соединение с ATOM успешно установлено'
                }
            except Exception as e:
                logger.error(f"Ошибка соединения с ATOM: {str(e)}")
                connection_status['ATOM'] = {
                    'status': 'error',
                    'message': f'Ошибка соединения: {str(e)}'
                }
        
        if not target or target == 'TEAMCENTER':
            # Создаем тестовое сообщение для TeamCenter
            test_data = {
                'apikey': 'test_key',
                'sender': 'INTBUS',
                'type': 'TEST_DATA',
                'data': {'test': True}
            }
            
            try:
                # Здесь должен быть реальный запрос к TeamCenter API
                # Заменить URL на реальный
                logger.info("Проверка соединения с TeamCenter...")
                
                # Пример проверки - имитация
                # В реальном коде здесь должен быть HTTP запрос к TeamCenter
                connection_status['TEAMCENTER'] = {
                    'status': 'success',
                    'message': 'Соединение с TeamCenter успешно установлено'
                }
            except Exception as e:
                logger.error(f"Ошибка соединения с TeamCenter: {str(e)}")
                connection_status['TEAMCENTER'] = {
                    'status': 'error',
                    'message': f'Ошибка соединения: {str(e)}'
                }
        
        # Возвращаем статус соединения с системами
        if target:
            # Если запрошена одна система, возвращаем только её статус
            if target in connection_status:
                return JsonResponse({
                    'status': 'success',
                    'target': target,
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
    Применение маппинга полей и отправка данных в целевую систему
    """
    try:
        # Получаем данные маппинга из запроса
        mapping_data = json.loads(request.body)
        
        # Проверяем обязательные поля
        required_fields = ['source_id', 'source_type', 'target', 'field_mapping']
        missing_fields = [field for field in required_fields if field not in mapping_data]
        
        if missing_fields:
            return JsonResponse({
                'status': 'error',
                'message': f'Отсутствуют обязательные поля: {missing_fields}'
            }, status=400)
        
        # Получаем параметры маппинга
        source_id = mapping_data['source_id']
        source_type = mapping_data['source_type']
        target = mapping_data['target'].upper()
        field_mapping = mapping_data['field_mapping']  # словарь вида {'source_field': 'target_field'}
        
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
        
        # Получаем данные источника
        source_data_dict = None
        if isinstance(source_data.data, str):
            try:
                source_data_dict = json.loads(source_data.data)
            except json.JSONDecodeError:
                # Если данные в XML или другом формате, пробуем извлечь теги
                # Упрощенный алгоритм извлечения данных из XML
                xml_data = source_data.data
                source_data_dict = {}
                
                # Пример очень простого извлечения значений из XML для демонстрации
                # В реальном коде здесь должен быть полноценный XML парсер
                for source_field, target_field in field_mapping.items():
                    # Ищем теги в XML
                    start_tag = f"<{source_field}>"
                    end_tag = f"</{source_field}>"
                    
                    start_pos = xml_data.find(start_tag)
                    if start_pos != -1:
                        start_pos += len(start_tag)
                        end_pos = xml_data.find(end_tag, start_pos)
                        if end_pos != -1:
                            value = xml_data[start_pos:end_pos].strip()
                            source_data_dict[source_field] = value
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
                'type': tc_data_type,
                'data': target_data_dict
            }
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

