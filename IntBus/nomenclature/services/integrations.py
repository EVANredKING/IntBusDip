import json
import time
import datetime as dt
from datetime import datetime
import logging
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict
from ..models import Nomenclature, LSI
from . import data_parser
import copy
from django.utils import timezone
import uuid

logger = logging.getLogger(__name__)

def send_to_target(request, source_type, pk, target):
    """
    Универсальная функция для отправки данных в целевую систему
    """
    try:
        if source_type == 'nomenclature':
            obj = Nomenclature.objects.get(pk=pk)
        elif source_type == 'lsi':
            obj = LSI.objects.get(pk=pk)
        else:
            raise ValueError(f"Неизвестный тип данных: {source_type}")
        
        # Проверяем, если отправитель уже совпадает с целевой системой
        if obj.sender.upper() == target:
            # Данные уже из целевой системы, отправляем напрямую
            return _direct_send(obj, target)
        else:
            # Отправитель другой, нужен маппинг полей
            logger.info(f'Требуется маппинг для отправки {source_type} ID:{pk} в {target}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Если AJAX запрос
                return JsonResponse({
                    'status': 'mapping_required',
                    'message': 'Требуется маппинг данных перед отправкой',
                    'source_id': pk,
                    'source_type': source_type,
                    'target': target
                })
            else:
                # Обычный запрос
                return redirect(f'/mapping/?source_id={pk}&source_type={source_type}&target={target}')
            
    except (Nomenclature.DoesNotExist, LSI.DoesNotExist):
        error_msg = f'{source_type.title()} с ID {pk} не найден'
        logger.error(error_msg)
        return JsonResponse({'status': 'error', 'message': error_msg}, status=404)
        
    except Exception as e:
        error_msg = f'Ошибка при отправке {source_type}: {str(e)}'
        logger.error(error_msg, exc_info=True)
        return JsonResponse({'status': 'error', 'message': error_msg}, status=500)

def _direct_send(source_obj, target):
    """
    Непосредственная отправка данных в целевую систему.
    
    Отправляет данные без маппинга напрямую в указанную целевую систему.
    
    Args:
        source_obj: Объект источника данных (Nomenclature или LSI)
        target: Целевая система (TEAMCENTER или ATOM)
        
    Returns:
        dict: Результат отправки
    """
    try:
        logger.info(f"Прямая отправка объекта {source_obj.pk} в {target}")
        
        # Получаем данные объекта
        try:
            # Пытаемся декодировать JSON если данные в виде строки
            if isinstance(source_obj.data, str):
                source_data = json.loads(source_obj.data)
            else:
                source_data = source_obj.data
                
            # Если source_data не словарь, создаем минимальную структуру
            if not isinstance(source_data, dict):
                source_data = {
                    'source_id': str(source_obj.pk),
                    'data': source_data  # Сохраняем исходные данные внутри структуры
                }
                logger.warning(f"Исходные данные были не словарем, а {type(source_data)}. Создана базовая структура.")
        except (json.JSONDecodeError, AttributeError) as e:
            # В случае ошибки декодирования создаем минимальную структуру
            source_data = {
                'source_id': str(source_obj.pk),
                'raw_data': str(source_obj.data)
            }
            logger.warning(f"Ошибка при разборе данных: {str(e)}. Создана базовая структура.")

        # Добавляем обязательные поля если их нет
        if 'name' not in source_data and 'code' not in source_data:
            # Проверяем, есть ли в raw_data XML с нужными полями
            xml_data = source_data.get('raw_data', '')
            has_kod_vnutrenniy = '<КодВнутренний>' in xml_data
            has_naimenovanie = '<НаименованиеПолное>' in xml_data or '<НаименованиеКраткое>' in xml_data
            
            if has_kod_vnutrenniy and has_naimenovanie:
                # Данные уже есть в XML, не добавляем автозаполнение
                logger.info("Обнаружены необходимые поля в XML данных, пропускаем автозаполнение")
            else:
                # Добавляем автозаполнение только если данных нет в XML
                source_data['name'] = f"Component {source_obj.pk}"
                source_data['code'] = f"CODE_{source_obj.pk}"
                logger.warning(f"Добавлены обязательные поля name и code для объекта {source_obj.pk}")
        
        # Обеспечиваем наличие NAME в верхнем регистре для TeamCenter
        if target == 'TEAMCENTER' and 'name' in source_data and not source_data.get('NAME'):
            source_data['NAME'] = source_data['name'].upper() if isinstance(source_data['name'], str) else str(source_data['name']).upper()
            logger.info(f"Добавлено поле NAME={source_data['NAME']} для TeamCenter")
        
        # Логируем данные для дебага
        logger.debug(f"Объект для отправки в {target}: {source_data}")
        
        # Отправляем данные
        if target == 'TEAMCENTER':
            result = send_to_teamcenter(source_data)
        elif target == 'ATOM':
            result = send_to_atom(source_data)
        else:
            error_msg = f"Неизвестная целевая система: {target}"
            logger.error(error_msg)
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
        # Логируем результат
        if result.get('success', False):
            log_msg = f"Успешная прямая отправка объекта {source_obj.pk} в {target}"
            logger.info(log_msg)
        else:
            log_msg = f"Ошибка при прямой отправке объекта {source_obj.pk} в {target}: {result.get('error', result.get('message', 'Неизвестная ошибка'))}"
            logger.error(log_msg)
        
        # Преобразуем результат в JsonResponse
        return JsonResponse(result)
    
    except Exception as e:
        error_msg = f"Исключение при прямой отправке объекта {source_obj.pk} в {target}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

def prepare_mapping_context(source_id, source_type, target):
    """Подготовка контекста для страницы маппинга"""
    # Получаем исходные данные
    source_obj = None
    
    if source_type == 'nomenclature':
        source_obj = Nomenclature.objects.get(id=source_id)
    elif source_type == 'lsi':
        source_obj = LSI.objects.get(id=source_id)
    else:
        raise ValueError(f"Неизвестный тип данных: {source_type}")
    
    # Получаем данные объекта
    source_data = model_to_dict(source_obj)
    parsed_data = data_parser.parse_source_data(source_obj)
    source_data.update(parsed_data)
    
    # Для LSI добавляем пустой список items если его нет
    if source_type == 'lsi' and 'items' not in source_data:
        source_data['items'] = []
        
    # Извлекаем поля для маппинга
    source_tags = _extract_source_tags(source_data)
    target_tags = _get_target_tags(target, source_type)
    
    # Создаем структуру mapping_data
    mapping_data = {
        'status': 'success',
        'message': '',
        'mapping_table': {
            'source_tags': source_tags,
            'target_tags': target_tags
        }
    }
    
    # Формируем контекст
    context = {
        'source_id': source_id,
        'source_type': source_type,
        'target': target,
        'target_display': target.title(),
        'source_data': {k: v for k, v in source_data.items() 
                     if isinstance(v, (str, int, float, bool)) 
                     and k not in ['apikey', 'data', 'sender', 'sent_to_atom', 'sent_to_teamcenter']},
        'mapping_data': mapping_data
    }
    
    return context

def _extract_source_tags(source_data):
    """Извлекает теги из исходных данных"""
    system_fields = ['apikey', 'data', 'sender', 'sent_to_atom', 'sent_to_teamcenter']
    source_tags = []
    
    # Добавляем все ключи верхнего уровня, исключая служебные поля
    source_tags.extend([key for key in source_data.keys() if key not in system_fields])
    
    # Если есть вложенные словари
    for key, value in source_data.items():
        if key not in system_fields and isinstance(value, dict):
            for nested_key in value.keys():
                source_tags.append(f"{key}.{nested_key}")
        
        # Если есть списки словарей
        if key not in system_fields and isinstance(value, list) and value and isinstance(value[0], dict):
            for nested_key in value[0].keys():
                source_tags.append(f"{key}.{nested_key}")
    
    # Удаляем дубликаты и фильтруем
    source_tags = list(set(source_tags))
    source_tags = [tag for tag in source_tags if "НоменклатураИзделие" not in tag]
    source_tags.sort()
    
    return source_tags

def _get_target_tags(target, source_type):
    """Возвращает список целевых тегов в зависимости от системы и типа данных"""
    if target == 'ATOM':
        if source_type == 'nomenclature':
            return [
                'name', 'code', 'description', 'type',
                'УУИД', 'СПК_ВидНоменклатуры', 'Аббревиатура', 'ДатаВведенияВДействие',
                'КодВнутренний', 'КодЕКПС', 'КодКВТ', 'КодПозицииКлассификатора',
                'КонтрольнаяСуммаЗаписи', 'НаименованиеКраткое', 'НаименованиеПолное',
                'ПометкаУдаления', 'ПризнакАрхивнойЗаписи', 'УникальныйКодКлассификатора',
                'ЧертежныйНомер', 'Шифр'
            ]
        else:  # LSI
            return [
                'name', 'lsi_id', 'description', 'type', 'items',
                'УУИД', 'СПК_ВидНоменклатуры', 'Аббревиатура', 'ДатаВведенияВДействие',
                'КодВнутренний', 'КодЕКПС', 'КодКВТ', 'КодПозицииКлассификатора',
                'КонтрольнаяСуммаЗаписи', 'НаименованиеКраткое', 'НаименованиеПолное',
                'ПометкаУдаления', 'ПризнакАрхивнойЗаписи', 'УникальныйКодКлассификатора',
                'ЧертежныйНомер', 'Шифр'
            ]
    elif target == 'TEAMCENTER':
        if source_type == 'nomenclature':
            return [
                'internalCode', 'fullName', 'shortName', 'abbreviation',
                'componentID', 'creationDate', 'description', 'id', 'itemID',
                'lastModifiedDate', 'lastModifiedUser', 'name', 'owner',
                'project_list', 'releaseStatus', 'revision', 'type', 'unitOfMeasure'
            ]
        else:  # LSI
            return [
                'name', 'description', 'items',
                'componentID', 'creationDate', 'id', 'itemID',
                'lastModifiedDate', 'lastModifiedUser', 'owner',
                'project_list', 'releaseStatus', 'revision', 'type', 'unitOfMeasure'
            ]
    
    return []

def apply_mapping(source_id, source_type, target, field_mapping):
    """Применяет маппинг полей и отправляет данные"""
    try:
        # Получаем исходные данные
        if source_type == 'nomenclature':
            source_obj = Nomenclature.objects.get(id=source_id)
        elif source_type == 'lsi':
            source_obj = LSI.objects.get(id=source_id)
        else:
            raise ValueError(f"Неизвестный тип данных: {source_type}")
        
        # Преобразуем объект в словарь
        source_data = model_to_dict(source_obj)
        parsed_data = data_parser.parse_source_data(source_obj)
        source_data.update(parsed_data)
        
        # Для LSI добавляем пустой список items если его нет
        if source_type == 'lsi' and 'items' not in source_data:
            source_data['items'] = []
        
        # Применяем маппинг
        target_data = _map_fields(source_data, field_mapping)
        
        # Добавляем обязательные поля
        target_data = _add_required_fields(target_data, target)
        
        # Отправляем данные
        try:
            if target == 'ATOM':
                result = send_to_atom(target_data)
            elif target == 'TEAMCENTER':
                result = send_to_teamcenter(target_data)
            else:
                raise ValueError(f"Неизвестная целевая система: {target}")
            
            # Проверяем, есть ли в результате ключ 'success'
            if 'success' not in result:
                # Добавляем ключ 'success' на основе статуса, если его нет
                result['success'] = result.get('status') == 'success'
                
            return JsonResponse(result)
        except Exception as e:
            logger.error(f"Ошибка при отправке данных: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'status': 'error', 'message': str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error applying mapping: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'status': 'error', 'message': str(e)}, status=500)

def _map_fields(source_data, field_mapping):
    """Применяет маппинг полей"""
    target_data = {}
    system_fields = ['apikey', 'data', 'sender', 'sent_to_atom', 'sent_to_teamcenter']
    
    for source_field, target_field in field_mapping.items():
        # Пропускаем служебные поля
        if source_field in system_fields:
            continue
            
        # Проверяем, есть ли вложенные поля (например, "items.name")
        if '.' in source_field:
            parts = source_field.split('.')
            parent_field = parts[0]
            child_field = '.'.join(parts[1:])
            
            # Пропускаем служебные родительские поля
            if parent_field in system_fields:
                continue
            
            if parent_field in source_data:
                if isinstance(source_data[parent_field], list):
                    # Для списков объектов
                    if target_field not in target_data:
                        target_data[target_field] = []
                    
                    for item in source_data[parent_field]:
                        if isinstance(item, dict) and child_field in item:
                            target_data[target_field].append(item[child_field])
                elif isinstance(source_data[parent_field], dict):
                    # Для вложенных словарей
                    if child_field in source_data[parent_field]:
                        target_data[target_field] = source_data[parent_field][child_field]
        else:
            # Простой случай - поле верхнего уровня
            if source_field in source_data:
                target_data[target_field] = source_data[source_field]
    
    return target_data

def _add_required_fields(target_data, target):
    """
    Добавляет обязательные поля для целевой системы.
    """
    if target == 'TEAMCENTER':
        # Безопасно получаем и обрабатываем значения, учитывая возможность None
        name_val = target_data.get('name')
        name_upper = name_val.upper() if name_val and isinstance(name_val, str) else ''
        
        fullname_val = target_data.get('fullName')
        fullname_upper = fullname_val.upper() if fullname_val and isinstance(fullname_val, str) else ''
        
        tc_fields = {
            'componentID': str(uuid.uuid4()) if not target_data.get('componentID') else target_data['componentID'],
            'creationDate': dt.datetime.now().isoformat() if not target_data.get('creationDate') else target_data['creationDate'],
            'NAME': target_data.get('NAME') or name_upper or fullname_upper or f"COMPONENT_{str(uuid.uuid4())[:8]}".upper()
        }
        
        # Проверяем, что NAME установлен, иначе устанавливаем дефолтное значение
        if not tc_fields['NAME']:
            name_fields = ['НаименованиеПолное', 'shortName', 'НаименованиеКраткое', 'code']
            for field in name_fields:
                if target_data.get(field):
                    tc_fields['NAME'] = target_data[field].upper() if isinstance(target_data[field], str) else str(target_data[field]).upper()
                    logger.info(f"NAME установлено из поля {field}: {tc_fields['NAME']}")
                    break
            
            # Если NAME всё ещё не установлен, задаем дефолтное значение
            if not tc_fields['NAME']:
                tc_fields['NAME'] = f"COMPONENT_{str(uuid.uuid4())[:8]}".upper()
                logger.warning(f"Установлено дефолтное значение для NAME: {tc_fields['NAME']}")
        
        # Если NAME доступен, но в нижнем регистре - преобразуем его в верхний
        elif tc_fields['NAME'] != tc_fields['NAME'].upper():
            tc_fields['NAME'] = tc_fields['NAME'].upper()
            logger.info(f"NAME преобразовано в верхний регистр: {tc_fields['NAME']}")
        
        # Добавляем поля только если их нет в target_data
        for field, value in tc_fields.items():
            if field not in target_data or target_data[field] is None:
                target_data[field] = value
                logger.debug(f"Добавлено обязательное поле {field}={value} для TeamCenter")
    
    elif target == 'ATOM':
        atom_fields = {
            'atom_id': str(uuid.uuid4()) if not target_data.get('atom_id') else target_data['atom_id'],
            'creation_date': dt.datetime.now().isoformat() if not target_data.get('creation_date') else target_data['creation_date'],
            'system_version': '1.0' if not target_data.get('system_version') else target_data['system_version']
        }
        
        # Добавляем поля только если их нет в target_data
        for field, value in atom_fields.items():
            if field not in target_data or target_data[field] is None:
                target_data[field] = value
                logger.debug(f"Добавлено обязательное поле {field}={value} для ATOM")
    
    return target_data

def send_to_atom(data):
    """
    Отправляет данные в ATOM.
    
    Args:
        data (dict): Данные для отправки
        
    Returns:
        dict: Результат отправки
    """
    try:
        # Извлекаем важные поля
        apikey = data.pop('apikey', 'test-atom-key') if 'apikey' in data else 'test-atom-key'
        data_type = data.pop('type', 'nomenclature')
        
        # Формируем структуру для ATOM
        prepared_data = {
            'apikey': apikey,
            'sender': 'INTBUS',
            'dataType': data_type,
            'data': data
        }
        
        # Пытаемся извлечь код и имя из XML данных
        raw_data = data.get('raw_data', '')
        code_from_xml = None
        name_from_xml = None
        uuid_from_xml = None
        
        # Извлекаем КодВнутренний из XML
        if '<КодВнутренний>' in raw_data and '</КодВнутренний>' in raw_data:
            start_idx = raw_data.find('<КодВнутренний>') + len('<КодВнутренний>')
            end_idx = raw_data.find('</КодВнутренний>')
            if start_idx < end_idx:
                code_from_xml = raw_data[start_idx:end_idx].strip()
                logger.info(f"Извлечен код из XML: {code_from_xml}")
        
        # Извлекаем УУИД из XML
        if '<УУИД>' in raw_data and '</УУИД>' in raw_data:
            start_idx = raw_data.find('<УУИД>') + len('<УУИД>')
            end_idx = raw_data.find('</УУИД>')
            if start_idx < end_idx:
                uuid_from_xml = raw_data[start_idx:end_idx].strip()
                logger.info(f"Извлечен УУИД из XML: {uuid_from_xml}")
        
        # Извлекаем НаименованиеПолное или НаименованиеКраткое из XML
        if '<НаименованиеПолное>' in raw_data and '</НаименованиеПолное>' in raw_data:
            start_idx = raw_data.find('<НаименованиеПолное>') + len('<НаименованиеПолное>')
            end_idx = raw_data.find('</НаименованиеПолное>')
            if start_idx < end_idx:
                name_from_xml = raw_data[start_idx:end_idx].strip()
                logger.info(f"Извлечено полное наименование из XML: {name_from_xml}")
        elif '<НаименованиеКраткое>' in raw_data and '</НаименованиеКраткое>' in raw_data:
            start_idx = raw_data.find('<НаименованиеКраткое>') + len('<НаименованиеКраткое>')
            end_idx = raw_data.find('</НаименованиеКраткое>')
            if start_idx < end_idx:
                name_from_xml = raw_data[start_idx:end_idx].strip()
                logger.info(f"Извлечено краткое наименование из XML: {name_from_xml}")
        
        # Используем извлеченные значения или значения из data, или значения по умолчанию
        prepared_data['code'] = code_from_xml or data.get('code', f"CODE_{str(int(time.time()))[-6:]}")
        prepared_data['name'] = name_from_xml or data.get('name', f"Название_{str(int(time.time()))[-6:]}")
        
        # Добавляем УУИД если он есть
        if uuid_from_xml or data.get('УУИД'):
            prepared_data['УУИД'] = uuid_from_xml or data.get('УУИД')
            logger.info(f"Добавлен УУИД в отправляемые данные: {prepared_data['УУИД']}")
        
        # Убеждаемся, что code и name есть в data и не перезаписываем их, если они уже существуют
        if 'code' not in prepared_data['data']:
            prepared_data['data']['code'] = prepared_data['code']
        
        if 'name' not in prepared_data['data']:
            prepared_data['data']['name'] = prepared_data['name']
            
        # Убеждаемся, что УУИД есть в data
        if 'УУИД' in prepared_data and 'УУИД' not in prepared_data['data']:
            prepared_data['data']['УУИД'] = prepared_data['УУИД']
            logger.info(f"УУИД добавлен в data: {prepared_data['data']['УУИД']}")
        
        # Отправляем данные
        logger.info(f"Отправка данных в ATOM: {json.dumps(prepared_data)[:1000]}...")
        
        # Используем полный URL для ATOM API
        atom_url = settings.ATOM_SYNC_URL
        logger.info(f"URL для отправки в ATOM: {atom_url}")
        
        response = requests.post(
            atom_url, 
            json=prepared_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Обрабатываем ответ
        if response.status_code in [200, 201]:
            logger.info(f"Данные успешно отправлены в ATOM: {response.text[:200]}")
            return {'success': True, 'status': 'success', 'message': 'Данные успешно отправлены'}
        else:
            error_msg = f"Ошибка при отправке в ATOM: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {'success': False, 'status': 'error', 'message': error_msg}
    
    except Exception as e:
        error_msg = f"Ошибка при отправке данных в ATOM: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'status': 'error', 'message': error_msg}

def send_to_teamcenter(data):
    """
    Отправляет данные в систему TeamCenter.
    
    Args:
        data (dict): Данные для отправки
    
    Returns:
        dict: Результат отправки с ключами success, error, response
    """
    try:
        url = settings.TEAMCENTER_URL
        apikey = settings.TEAMCENTER_APIKEY
        
        # Подготовка данных для отправки
        prepared_data = data.copy()
        
        # Убедимся, что NAME присутствует и в верхнем регистре
        name_fields = ['name', 'fullName', 'НаименованиеПолное', 'shortName', 'НаименованиеКраткое']
        
        # Если NAME не установлен, пытаемся найти его из других полей
        if not prepared_data.get('NAME'):
            for field in name_fields:
                if field in prepared_data and prepared_data[field]:
                    prepared_data['NAME'] = str(prepared_data[field]).upper()
                    logger.info(f"NAME установлен из поля {field}: {prepared_data['NAME']}")
                    break
        
        # Если NAME все еще не установлен, используем дефолтное значение
        if not prepared_data.get('NAME'):
            prepared_data['NAME'] = f"COMPONENT_{uuid.uuid4().hex[:8]}".upper()
            logger.warning(f"Установлено дефолтное NAME: {prepared_data['NAME']}")
        
        # Гарантируем, что NAME в верхнем регистре
        if prepared_data.get('NAME') and prepared_data['NAME'] != prepared_data['NAME'].upper():
            prepared_data['NAME'] = prepared_data['NAME'].upper()
            logger.info(f"NAME преобразован в верхний регистр: {prepared_data['NAME']}")
        
        # Проверяем наличие обязательных полей
        required_fields = ['id', 'name', 'NAME']
        for field in required_fields:
            if field not in prepared_data:
                # Для id генерируем случайный идентификатор, если его нет
                if field == 'id':
                    prepared_data['id'] = str(uuid.uuid4())
                    logger.warning(f"Установлено дефолтное значение для id: {prepared_data['id']}")
                # Для name берем значение из NAME или генерируем новое
                elif field == 'name' and 'NAME' in prepared_data:
                    prepared_data['name'] = prepared_data['NAME']
                    logger.info(f"Поле name установлено из NAME: {prepared_data['name']}")
                # Для NAME берем значение из name или генерируем новое
                elif field == 'NAME' and 'name' in prepared_data:
                    prepared_data['NAME'] = str(prepared_data['name']).upper()
                    logger.info(f"Поле NAME установлено из name: {prepared_data['NAME']}")
                else:
                    prepared_data[field] = f"{field.upper()}_{uuid.uuid4().hex[:8]}"
                    logger.warning(f"Установлено дефолтное значение для {field}: {prepared_data[field]}")
        
        # Создаем структуру данных для TeamCenter
        payload = {
            'apikey': apikey,
            'sender': 'INTBUS',
            'dataType': 'nomenclature',
            'data': prepared_data
        }
        
        # Финальная проверка - всегда должно быть NAME и не быть NULL
        if 'NAME' not in payload['data'] or payload['data']['NAME'] is None:
            default_name = f"DEFAULT_NAME_{uuid.uuid4().hex[:8]}".upper()
            payload['data']['NAME'] = default_name
            logger.warning(f"Критичное исправление: добавлено отсутствующее поле NAME: {default_name}")
        
        # Финальная проверка перед отправкой - запись в журнал
        logger.debug(f"Подготовленные данные для TeamCenter (окончательные):\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        # Отправка запроса
        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': apikey
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.REQUEST_TIMEOUT
        )
        
        # Обработка ответа
        if response.status_code == 200:
            logger.info(f"Успешная отправка в TeamCenter: {response.text[:100]}")
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {'raw_response': response.text}
            
            return {
                'success': True,
                'response': response_data,
                'status_code': response.status_code
            }
        else:
            error_msg = f"Ошибка при отправке в TeamCenter: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'status_code': response.status_code
            }
    
    except Exception as e:
        error_msg = f"Исключение при отправке в TeamCenter: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {'success': False, 'error': error_msg} 