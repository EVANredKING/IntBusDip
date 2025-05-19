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

# Сборка проекта
RUN mvn clean package -DskipTests

FROM amazoncorretto:21-alpine

WORKDIR /app

# Создаем директории для H2 данных и логов
RUN mkdir -p /app/logs /app/data /app/frontend/build

# Копируем JAR-файл из предыдущего этапа
COPY --from=build /app/target/*.jar app.jar

# Копируем собранный фронтенд из предыдущего этапа
COPY --from=build /app/frontend/build /app/frontend/build

# Копируем файл конфигурации для Docker
COPY src/main/resources/application-docker.properties /app/

# Открываем порт
EXPOSE 3000

# Устанавливаем рабочую директорию и запускаем приложение
WORKDIR /app

# Устанавливаем переменную среды для активации профиля docker
ENV SPRING_PROFILES_ACTIVE=docker

# Запускаем приложение с явным указанием местоположения файла конфигурации
ENTRYPOINT ["java", "-jar", "app.jar", "--spring.config.location=file:/app/application-docker.properties"] 