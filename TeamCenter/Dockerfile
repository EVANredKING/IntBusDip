FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app

# Копируем файл pom.xml для загрузки зависимостей
COPY pom.xml .

# Копируем исходники
COPY src ./src
COPY frontend ./frontend

# Отключаем сборку фронтенда в maven и собираем его отдельно
RUN sed -i 's/<execution>.*<id>npm run build<\/id>.*<\/execution>/<!-- отключено -->/g' pom.xml && \
    sed -i 's/<execution>.*<id>install node and npm<\/id>.*<\/execution>/<!-- отключено -->/g' pom.xml && \
    sed -i 's/<execution>.*<id>npm install<\/id>.*<\/execution>/<!-- отключено -->/g' pom.xml

# Устанавливаем Node.js и собираем фронтенд вручную
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    cd frontend && npm install && npm run build && cd ..

# Изменяем пути в index.html (с абсолютных на относительные)
RUN sed -i 's|href="/|href="./|g' frontend/build/index.html && \
    sed -i 's|src="/|src="./|g' frontend/build/index.html

# Сборка проекта
RUN mvn clean package -DskipTests

FROM amazoncorretto:21-alpine

WORKDIR /app

# Создаем директории для H2 данных, логов и статических файлов
RUN mkdir -p /app/logs /app/data /app/frontend/build/static/js /app/frontend/build/static/css /app/frontend/build/static/media

# Копируем JAR-файл из предыдущего этапа
COPY --from=build /app/target/*.jar app.jar

# Копируем собранный фронтенд из предыдущего этапа - важно сохранить структуру директорий
COPY --from=build /app/frontend/build/ /app/frontend/build/

# Копируем файл конфигурации для Docker
COPY src/main/resources/application-docker.properties /app/

# Проверяем содержимое директории frontend/build (для отладки)
RUN ls -la /app/frontend/build/ && \
    ls -la /app/frontend/build/static/ && \
    ls -la /app/frontend/build/static/js/ && \
    ls -la /app/frontend/build/static/css/

# Открываем порт
EXPOSE 3000

# Устанавливаем рабочую директорию и запускаем приложение
WORKDIR /app

# Устанавливаем переменную среды для активации профиля docker
ENV SPRING_PROFILES_ACTIVE=docker

# Запускаем приложение с явным указанием местоположения файла конфигурации
ENTRYPOINT ["java", "-jar", "app.jar", "--spring.config.location=file:/app/application-docker.properties"] 