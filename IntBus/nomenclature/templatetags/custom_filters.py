from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Фильтр для шаблонов Django, позволяющий получить значение словаря по ключу.
    Пример использования: {{ my_dict|get_item:key_var }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key) 