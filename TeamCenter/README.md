# TeamCenter

Полнофункциональное приложение на базе Spring Boot и React.

## Требования

- Java 17
- Maven 3.8+
- Node.js 18+
- npm 8+

## Установка и запуск

### Установка Java

1. Загрузите JDK 17 с [официального сайта Oracle](https://www.oracle.com/java/technologies/downloads/#java17) или используйте OpenJDK
2. Установите JDK, следуя инструкциям установщика
3. Установите переменную среды JAVA_HOME, указывающую на папку установки JDK
4. Добавьте %JAVA_HOME%\bin в переменную PATH

### Установка Maven

1. Загрузите Maven с [официального сайта](https://maven.apache.org/download.cgi)
2. Распакуйте архив в выбранную папку
3. Установите переменную среды M2_HOME, указывающую на папку с Maven
4. Добавьте %M2_HOME%\bin в переменную PATH

### Запуск приложения

#### Вариант 1: Запуск с использованием Maven

```bash
mvn spring-boot:run
```

#### Вариант 2: Раздельный запуск бэкенда и фронтенда

Запуск бэкенда:
```bash
mvn spring-boot:run
```

Запуск фронтенда (в отдельном терминале):
```bash
cd frontend
npm install
npm start
```

## Структура проекта

- `src/main/java` - исходный код Java
- `src/main/resources` - ресурсы приложения (конфигурации, статические файлы)
- `frontend` - React-приложение

## API Endpoints

- GET `/api/hello` - тестовый эндпойнт

## Сборка для продакшена

```bash
mvn clean package
```

Собранный JAR-файл будет находиться в папке `target`. 