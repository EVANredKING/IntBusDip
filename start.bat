@echo off
echo Запуск Docker контейнеров для IntBusDip...
docker-compose up -d
echo Контейнеры запущены. Доступные адреса:
echo IntBus: http://localhost:8081
echo ATOM: http://localhost:8082
echo TeamCenter: http://localhost:3000 