import json
import logging
import xml.etree.ElementTree as ET
import re

logger = logging.getLogger(__name__)

def parse_source_data(source_obj):
    """
    Парсит данные из source_obj.data.
    Поддерживает форматы JSON и XML.
    
    Аргументы:
        source_obj: Объект номенклатуры или LSI
        
    Возвращает:
        dict: Извлеченные данные
    """
    source_data = {}
    
    if not hasattr(source_obj, 'data') or not source_obj.data:
        logger.warning(f"Объект {source_obj.__class__.__name__} с ID={source_obj.id} не содержит данных")
        return source_data
    
    # Парсим данные из поля data объекта
    if isinstance(source_obj.data, str):
        try:
            # Пробуем распарсить JSON
            data_dict = json.loads(source_obj.data)
            if isinstance(data_dict, dict):
                logger.info(f"Успешно распарсили JSON для {source_obj.__class__.__name__} с ID={source_obj.id}")
                source_data.update(data_dict)
        except json.JSONDecodeError:
            logger.info(f"Данные не в формате JSON, пробуем XML для {source_obj.__class__.__name__} с ID={source_obj.id}")
            # Если не JSON, пробуем найти XML теги
            if source_obj.data.strip().startswith('<?xml') or '<' in source_obj.data:
                try:
                    # Пробуем использовать стандартную библиотеку для парсинга XML
                    root = ET.fromstring(source_obj.data)
                    source_data.update(_process_xml_element(root))
                    logger.info(f"Успешно распарсили XML через ElementTree для {source_obj.__class__.__name__} с ID={source_obj.id}")
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге XML через ElementTree: {str(e)}, пробуем регулярные выражения")
                    # Если стандартный XML-парсер не сработал, используем регулярные выражения
                    source_data.update(_parse_xml_with_regex(source_obj.data))
                    logger.info(f"Успешно распарсили XML через регулярные выражения для {source_obj.__class__.__name__} с ID={source_obj.id}")
            else:
                logger.warning(f"Данные не похожи ни на JSON, ни на XML: {source_obj.__class__.__name__} с ID={source_obj.id}")
    elif isinstance(source_obj.data, dict):
        # Если data уже является словарем
        logger.info(f"Данные уже в формате словаря для {source_obj.__class__.__name__} с ID={source_obj.id}")
        source_data.update(source_obj.data)
    
    # Добавляем известные поля из XML ATOM или TeamCenter если нужно
    add_default_fields(source_data, source_obj)
    
    return source_data

def _process_xml_element(element, prefix=''):
    """Рекурсивно обрабатывает XML-элемент и его дочерние элементы"""
    result = {}
    
    # Получаем текстовое содержимое элемента
    if element.text and element.text.strip():
        result[prefix + element.tag] = element.text.strip()
    
    # Обрабатываем атрибуты элемента
    for attr_name, attr_value in element.attrib.items():
        result[f"{prefix}{element.tag}@{attr_name}"] = attr_value
    
    # Рекурсивно обрабатываем дочерние элементы
    for child in element:
        child_data = _process_xml_element(child, f"{prefix}{element.tag}." if prefix else "")
        result.update(child_data)
    
    return result

def _parse_xml_with_regex(xml_data):
    """Парсинг XML с помощью регулярных выражений"""
    result = {}
    pattern = r'<(\w+)>(.*?)</\1>'
    matches = re.findall(pattern, xml_data, re.DOTALL)
    
    for tag, value in matches:
        result[tag] = value.strip()
    
    return result

def add_default_fields(source_data, source_obj):
    """Добавляет поля по умолчанию в зависимости от источника данных"""
    if not hasattr(source_obj, 'sender'):
        return
        
    if source_obj.sender and source_obj.sender.upper() == 'ATOM':
        # Добавляем стандартные поля ATOM если они отсутствуют
        atom_fields = [
            'УУИД', 'СПК_ВидНоменклатуры', 'Аббревиатура', 'ДатаВведенияВДействие',
            'КодВнутренний', 'КодЕКПС', 'КодКВТ', 'КодПозицииКлассификатора',
            'КонтрольнаяСуммаЗаписи', 'НаименованиеКраткое', 'НаименованиеПолное',
            'ПометкаУдаления', 'ПризнакАрхивнойЗаписи', 'УникальныйКодКлассификатора',
            'ЧертежныйНомер', 'Шифр'
        ]
        
        for field in atom_fields:
            if field not in source_data:
                source_data[field] = ''
                
    elif source_obj.sender and source_obj.sender.upper() == 'TEAMCENTER':
        # Добавляем стандартные поля TeamCenter если они отсутствуют
        teamcenter_fields = [
            'componentID', 'creationDate', 'description', 'id', 'itemID',
            'lastModifiedDate', 'lastModifiedUser', 'name', 'owner',
            'project_list', 'releaseStatus', 'revision', 'type', 'unitOfMeasure'
        ]
        
        for field in teamcenter_fields:
            if field not in source_data:
                source_data[field] = ''
        
        # Добавляем поле NAME в верхнем регистре для TeamCenter
        # TeamCenter ожидает имя в поле NAME (в верхнем регистре)
        if 'name' in source_data and source_data['name']:
            source_data['NAME'] = source_data['name']
            logger.info(f"Добавлено поле NAME для TeamCenter: {source_data['NAME']}")
        elif 'НаименованиеПолное' in source_data and source_data['НаименованиеПолное']:
            source_data['NAME'] = source_data['НаименованиеПолное']
            logger.info(f"Поле NAME для TeamCenter установлено из НаименованиеПолное: {source_data['NAME']}")
        elif 'НаименованиеКраткое' in source_data and source_data['НаименованиеКраткое']:
            source_data['NAME'] = source_data['НаименованиеКраткое']
            logger.info(f"Поле NAME для TeamCenter установлено из НаименованиеКраткое: {source_data['NAME']}")
        elif hasattr(source_obj, 'name') and source_obj.name:
            source_data['NAME'] = source_obj.name
            logger.info(f"Поле NAME для TeamCenter установлено из атрибута объекта: {source_data['NAME']}")
        else:
            # Устанавливаем значение по умолчанию, если имя не найдено
            source_data['NAME'] = f"Object_{source_obj.pk}"
            logger.warning(f"Не найдено подходящее имя для TeamCenter, установлено по умолчанию: {source_data['NAME']}") 