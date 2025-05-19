package com.teamcenter.app.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpMethod;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.fasterxml.jackson.databind.ObjectMapper;

import com.teamcenter.app.service.CsrfTokenService;
import com.teamcenter.app.service.IntBusService;

@RestController
@RequestMapping("/api/debug")
public class DebugController {

    private static final Logger logger = LoggerFactory.getLogger(DebugController.class);

    @Autowired
    private RestTemplate restTemplate;
    
    @Value("${intbus.sync.url}")
    private String intbusSyncUrl;
    
    @Autowired
    private CsrfTokenService csrfTokenService;
    
    @Autowired
    private IntBusService intBusService;
    
    @GetMapping("/info")
    public Map<String, String> getInfo() {
        Map<String, String> info = new HashMap<>();
        info.put("intbusSyncUrl", intbusSyncUrl);
        logger.info("Запрошена информация о конфигурации");
        return info;
    }
    
    @PostMapping("/test-connection")
    public ResponseEntity<String> testConnection(@RequestBody(required = false) Map<String, Object> testData) {
        try {
            if (testData == null) {
                testData = new HashMap<>();
                testData.put("data", Collections.singletonMap("test", "value"));
                testData.put("dataType", "test");
                testData.put("source", "TeamCenter");
                logger.info("Создан тестовый набор данных, так как тело запроса отсутствует");
            } else {
                logger.info("Получены пользовательские данные для тестирования");
            }
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            logger.info("Тестовые данные для отправки: {}", testData);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(testData, headers);
            
            logger.info("Отправка тестового запроса на URL: {}", intbusSyncUrl);
            logger.debug("Заголовки: {}", headers);
            
            try {
                ResponseEntity<String> response = restTemplate.postForEntity(
                    intbusSyncUrl, 
                    request, 
                    String.class
                );
                
                logger.info("Получен ответ: {}", response.getStatusCode());
                logger.debug("Тело ответа: {}", response.getBody());
                
                return new ResponseEntity<>(
                    "Тест успешен. Статус: " + response.getStatusCode() + ", Ответ: " + response.getBody(),
                    HttpStatus.OK
                );
            } catch (Exception e) {
                logger.error("Ошибка при тестовом запросе: {}", e.getMessage());
                logger.error("Класс ошибки: {}", e.getClass().getName(), e);
                
                Throwable cause = e.getCause();
                if (cause != null) {
                    logger.error("Причина: {}", cause.getMessage());
                    logger.error("Класс причины: {}", cause.getClass().getName());
                }
                
                return new ResponseEntity<>(
                    "Ошибка теста: " + e.getMessage() + (cause != null ? ", Причина: " + cause.getMessage() : ""),
                    HttpStatus.INTERNAL_SERVER_ERROR
                );
            }
        } catch (Exception e) {
            logger.error("Общая ошибка: {}", e.getMessage(), e);
            return new ResponseEntity<>("Общая ошибка: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    @PostMapping("/verify-json")
    public ResponseEntity<Map<String, Object>> verifyJsonFormat(@RequestBody(required = false) Map<String, Object> testData) {
        try {
            logger.info("Проверка формата JSON");
            
            // Создаем тестовые данные, если не предоставлены
            if (testData == null || testData.isEmpty()) {
                testData = new HashMap<>();
                Map<String, String> dataObject = new HashMap<>();
                dataObject.put("field1", "value1");
                dataObject.put("field2", "value2");
                
                testData.put("data", dataObject);
                testData.put("dataType", "test");
                testData.put("source", "TeamCenter");
                
                logger.info("Созданы тестовые данные: {}", testData);
            }
            
            // Проверяем формат и структуру данных
            Map<String, Object> result = new HashMap<>();
            result.put("valid", true);
            result.put("originalData", testData);
            
            // Сериализуем в JSON и обратно для проверки
            ObjectMapper mapper = new ObjectMapper();
            String json = mapper.writeValueAsString(testData);
            
            result.put("serializedJson", json);
            
            // Проверяем структуру
            if (!testData.containsKey("data")) {
                result.put("warning", "Отсутствует обязательное поле 'data'");
                result.put("valid", false);
            }
            
            if (!testData.containsKey("dataType")) {
                result.put("warning", "Отсутствует обязательное поле 'dataType'");
                result.put("valid", false);
            }
            
            if (!testData.containsKey("source")) {
                result.put("warning", "Отсутствует обязательное поле 'source'");
                result.put("valid", false);
            }
            
            // Тестовый запрос к IntBus (опционально)
            if (Boolean.TRUE.equals(result.get("valid"))) {
                try {
                    HttpHeaders headers = new HttpHeaders();
                    headers.setContentType(MediaType.APPLICATION_JSON);
                    
                    HttpEntity<Map<String, Object>> entity = new HttpEntity<>(testData, headers);
                    
                    result.put("requestHeaders", headers.toString());
                    result.put("requestBody", testData);
                    
                    // Делаем тестовый запрос к локальному эхо-эндпоинту
                    ResponseEntity<String> response = restTemplate.postForEntity(
                        "/api/debug/echo", entity, String.class);
                    
                    result.put("testRequestSuccess", true);
                    result.put("testRequestStatus", response.getStatusCode());
                    result.put("testRequestResponse", response.getBody());
                } catch (Exception e) {
                    result.put("testRequestSuccess", false);
                    result.put("testRequestError", e.getMessage());
                }
            }
            
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (Exception e) {
            logger.error("Ошибка при проверке формата JSON: {}", e.getMessage(), e);
            
            Map<String, Object> error = new HashMap<>();
            error.put("error", "Ошибка при проверке: " + e.getMessage());
            error.put("stackTrace", e.getStackTrace());
            
            return new ResponseEntity<>(error, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    @PostMapping("/echo")
    public ResponseEntity<Map<String, Object>> echo(@RequestBody Map<String, Object> requestData) {
        logger.info("Получен запрос к echo-эндпоинту: {}", requestData);
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("echo", requestData);
        response.put("timestamp", System.currentTimeMillis());
        
        return new ResponseEntity<>(response, HttpStatus.OK);
    }
    
    @GetMapping("/check-intbus")
    public ResponseEntity<Map<String, Object>> checkIntBusConnection() {
        Map<String, Object> result = new HashMap<>();
        result.put("intbusSyncUrl", intbusSyncUrl);
        
        try {
            // Проверяем соединение с IntBus с методом OPTIONS
            HttpHeaders headers = new HttpHeaders();
            HttpEntity<String> entity = new HttpEntity<>(headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                intbusSyncUrl, 
                org.springframework.http.HttpMethod.OPTIONS,
                entity,
                String.class
            );
            
            result.put("connectionSuccess", true);
            result.put("statusCode", response.getStatusCode().toString());
            result.put("headers", response.getHeaders().toString());
            
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (Exception e) {
            logger.error("Ошибка при проверке соединения с IntBus: {}", e.getMessage(), e);
            
            result.put("connectionSuccess", false);
            result.put("error", e.getMessage());
            result.put("errorType", e.getClass().getName());
            
            if (e.getCause() != null) {
                result.put("errorCause", e.getCause().getMessage());
            }
            
            return new ResponseEntity<>(result, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    @GetMapping("/csrf")
    public ResponseEntity<Map<String, Object>> testCsrf() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // URL для загрузки главной страницы Django
            String baseUrl = intbusSyncUrl.substring(0, intbusSyncUrl.indexOf("/sync/api/sync"));
            String csrfUrl = baseUrl + "/";
            result.put("baseUrl", baseUrl);
            result.put("csrfUrl", csrfUrl);
            
            logger.info("Тестирование CSRF, URL: {}", csrfUrl);
            
            // Выполняем GET-запрос для получения cookies
            HttpHeaders headers = new HttpHeaders();
            HttpEntity<String> entity = new HttpEntity<>(headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                csrfUrl, 
                HttpMethod.GET, 
                entity, 
                String.class
            );
            
            result.put("statusCode", response.getStatusCode().toString());
            result.put("headers", response.getHeaders().toString());
            
            // Ищем CSRF-токен в cookies
            List<String> cookies = response.getHeaders().get("Set-Cookie");
            if (cookies != null) {
                result.put("cookies", cookies);
                
                for (String cookie : cookies) {
                    if (cookie.contains("csrftoken")) {
                        Pattern pattern = Pattern.compile("csrftoken=([^;]+)");
                        Matcher matcher = pattern.matcher(cookie);
                        if (matcher.find()) {
                            String csrfToken = matcher.group(1);
                            result.put("csrfToken", csrfToken);
                            
                            // Тест отправки запроса с CSRF токеном
                            Map<String, Object> testData = new HashMap<>();
                            Map<String, Object> dataObject = new HashMap<>();
                            dataObject.put("test", "value");
                            testData.put("data", dataObject);
                            testData.put("dataType", "test");
                            testData.put("source", "TeamCenter");
                            
                            HttpHeaders testHeaders = new HttpHeaders();
                            testHeaders.setContentType(MediaType.APPLICATION_JSON);
                            testHeaders.add("X-CSRFToken", csrfToken);
                            testHeaders.add("Cookie", "csrftoken=" + csrfToken);
                            testHeaders.add("Referer", intbusSyncUrl);
                            
                            HttpEntity<Map<String, Object>> testEntity = new HttpEntity<>(testData, testHeaders);
                            
                            try {
                                ResponseEntity<String> testResponse = restTemplate.postForEntity(
                                    intbusSyncUrl, 
                                    testEntity,
                                    String.class
                                );
                                
                                result.put("testSuccess", true);
                                result.put("testStatusCode", testResponse.getStatusCode().toString());
                                result.put("testResponse", testResponse.getBody());
                            } catch (Exception e) {
                                result.put("testSuccess", false);
                                result.put("testError", e.getMessage());
                                logger.error("Ошибка при тестовом запросе с CSRF: {}", e.getMessage(), e);
                            }
                            
                            break;
                        }
                    }
                }
            } else {
                result.put("csrfTokenFound", false);
                logger.warn("CSRF-токен не найден в cookies");
            }
            
            // Проверяем содержимое HTML-страницы на наличие CSRF-токена
            String content = response.getBody();
            if (content != null) {
                Pattern pattern = Pattern.compile("name='csrfmiddlewaretoken' value='([^']+)'");
                Matcher matcher = pattern.matcher(content);
                if (matcher.find()) {
                    String csrfToken = matcher.group(1);
                    result.put("csrfTokenFromHtml", csrfToken);
                }
            }
            
            return new ResponseEntity<>(result, HttpStatus.OK);
        } catch (Exception e) {
            logger.error("Ошибка при тестировании CSRF: {}", e.getMessage(), e);
            
            result.put("error", e.getMessage());
            result.put("errorType", e.getClass().getName());
            
            return new ResponseEntity<>(result, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    @GetMapping("/csrf-token")
    public String getCsrfToken() {
        String token = csrfTokenService.getCsrfToken();
        logger.info("Получен CSRF-токен: {}", token);
        return "CSRF-токен получен: " + (token != null ? token.substring(0, 8) + "..." : "null");
    }
    
    @GetMapping("/test-intbus")
    public String testIntBusConnection() {
        try {
            Map<String, Object> testData = new HashMap<>();
            Map<String, Object> data = new HashMap<>();
            data.put("test", "value");
            data.put("timestamp", System.currentTimeMillis());
            
            testData.put("data", data);
            testData.put("dataType", "test");
            testData.put("source", "TeamCenter");
            
            logger.info("Тестирование соединения с IntBus. URL: {}", intbusSyncUrl);
            
            try {
                ResponseEntity<String> response = intBusService.sendDataToIntBus(testData);
                
                logger.info("Тест IntBus успешен. Статус: {}, Ответ: {}", 
                    response.getStatusCodeValue(), response.getBody());
                
                return "Ответ от IntBus: " + response.getStatusCodeValue() + " " + response.getBody();
            } catch (Exception e) {
                logger.error("Ошибка при тестировании соединения с IntBus: {}", e.getMessage(), e);
                
                // Попытка прямого запроса через RestTemplate
                logger.info("Попытка прямого запроса через RestTemplate...");
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                headers.add("User-Agent", "TeamCenter Test Client");
                
                HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(testData, headers);
                
                try {
                    ResponseEntity<String> directResponse = restTemplate.postForEntity(
                        intbusSyncUrl, 
                        requestEntity, 
                        String.class
                    );
                    
                    logger.info("Прямой запрос успешен. Статус: {}, Ответ: {}", 
                        directResponse.getStatusCodeValue(), directResponse.getBody());
                    
                    return "Ошибка через сервис: " + e.getMessage() + 
                           "\nНо прямой запрос успешен. Статус: " + directResponse.getStatusCodeValue() + 
                           " Ответ: " + directResponse.getBody();
                } catch (Exception ex) {
                    logger.error("Ошибка и при прямом запросе: {}", ex.getMessage(), ex);
                    return "Ошибки:\n1. " + e.getMessage() + "\n2. Прямой запрос: " + ex.getMessage();
                }
            }
        } catch (Exception e) {
            logger.error("Общая ошибка при тестировании: {}", e.getMessage(), e);
            return "Общая ошибка: " + e.getMessage();
        }
    }
} 