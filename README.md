# IntBusDip

## Запуск проекта в Docker

### Требования
- Docker
- Docker Compose

### Запуск контейнеров
1. Убедитесь, что Docker запущен на вашей системе
2. Откройте командную строку или терминал в корне проекта
3. Запустите скрипт `start.bat` (Windows) или выполните команду:
   ```
   docker-compose up -d
   ```
4. Дождитесь запуска всех контейнеров

### Остановка контейнеров
Для остановки контейнеров запустите скрипт `stop.bat` (Windows) или выполните команду:
```
docker-compose down
```

### Доступ к сервисам
После запуска контейнеров сервисы будут доступны по следующим адресам:
- IntBus: http://localhost:8081
- ATOM: http://localhost:8082
- TeamCenter: http://localhost:3000
- База данных PostgreSQL: localhost:5432

### Логи и отладка
Для просмотра логов контейнеров используйте команду:
```
docker-compose logs -f [service_name]
```
где [service_name] - одно из: intbus, atom, teamcenter, db 