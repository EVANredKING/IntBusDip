FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install psycopg2-binary

# Создаем директорию для логов
RUN mkdir -p /app/logs

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=atom_project.docker_settings

EXPOSE 8001

# Ожидание доступности базы данных
CMD python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    python manage.py runserver 0.0.0.0:8001 