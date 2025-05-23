# IntBus - Система просмотра номенклатуры и ЛСИ

IntBus - это веб-приложение на Django для просмотра данных номенклатуры и логической структуры изделий (ЛСИ). Проект является аналогом системы ATOM, но без возможности редактирования, создания и удаления данных.

## Основные возможности

- Просмотр номенклатуры
- Просмотр логической структуры изделий (ЛСИ)
- Экспорт данных в Excel
- Система аутентификации пользователей
- Современный адаптивный интерфейс на основе Bootstrap 5

## Ограничения

- Нет возможности создавать новые записи
- Нет возможности редактировать существующие записи
- Нет возможности удалять записи
- Нет функционала импорта данных

## Требования

- Python 3.8+
- Django 4.0+
- Pandas
- XlsxWriter (для экспорта данных)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/intbus.git
cd intbus
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Выполните миграции:
```bash
python manage.py migrate
```

5. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

6. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Структура проекта

- `intbus_project/` - основной проект Django
- `nomenclature/` - приложение для просмотра данных
- `nomenclature/models.py` - модели данных (Nomenclature, LSI)
- `nomenclature/views.py` - представления для обработки запросов
- `nomenclature/templates/` - шаблоны HTML

## Использование

1. Просмотр номенклатуры
   - Перейдите в раздел "Номенклатура"
   - Просматривайте данные в таблице

2. Просмотр логической структуры изделий (ЛСИ)
   - Перейдите в раздел "ЛСИ"
   - Просматривайте данные в таблице

3. Экспорт данных
   - Используйте функцию "Экспорт в Excel" в меню "Экспорт"

## Авторизация

В системе автоматически создается тестовый пользователь:
- Логин: testuser
- Пароль: password123 