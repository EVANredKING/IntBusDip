package com.teamcenter.app.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.HashSet;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;

@Service
public class IntBusService {

    private final RestTemplate restTemplate;
    
    @Value("${intbus.sync.url}")
    private String syncUrl;
    
    @Value("${intbus.csrf.url}")
    private String csrfUrl;
    
    @Value("${intbus.apikey}")
    private String apiKey;
    
    @Value("${intbus.sender}")
    private String sender;

    private static final Logger log = LoggerFactory.getLogger(IntBusService.class);

    @Autowired
    public IntBusService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Отправляет данные в IntBus в формате {apikey, sender, data}
     * 
     * @param data Данные для отправки
     * @return Ответ от сервера IntBus
     */
    public ResponseEntity<String> sendDataToIntBus(Map<String, Object> data) {
        log.info("Отправка данных в IntBus: {}", data);
        
        try {
            // Проверка наличия обязательных полей
            if (!data.containsKey("data") || !data.containsKey("dataType") || !data.containsKey("source")) {
                log.error("Ошибка: отсутствуют обязательные поля в данных для IntBus");
                return new ResponseEntity<>("Ошибка: отсутствуют обязательные поля в данных", HttpStatus.BAD_REQUEST);
            }
            
            // Получаем тип данных для специальных заголовков
            String dataType = (String) data.get("dataType");
            log.debug("Тип данных для отправки: {}", dataType);
            
            // Получаем данные и глубоко клонируем их для безопасного изменения
            Map<String, Object> dataClone = new HashMap<>();
            dataClone.put("source", data.get("source"));
            dataClone.put("dataType", dataType);
            
            Object dataObj = data.get("data");
            if (dataObj instanceof Map) {
                Map<String, Object> dataMap = new HashMap<>((Map<String, Object>) dataObj);
                
                // Если это LSI данные, обрабатываем каждое поле особым образом
                if ("lsi".equals(dataType)) {
                    // 1. Удаляем все поля, связанные с "name"
                    dataMap.remove("name");
                    
                    // 2. Обработка вложенных объектов, чтобы удалить любые поля "name"
                    for (String key : new HashSet<>(dataMap.keySet())) {
                        Object value = dataMap.get(key);
                        if (value instanceof Map) {
                            Map<String, Object> nestedMap = (Map<String, Object>) value;
                            nestedMap.remove("name");
                            if (key.contains("name") && !key.equals("position_name")) {
                                // Если ключ содержит слово "name", и это не position_name, переименуем его
                                dataMap.put("tc_" + key, nestedMap);
                                dataMap.remove(key);
                            }
                        }
                    }
                    
                    log.debug("LSI данные после обработки: {}", dataMap.keySet());
                }
                
                dataClone.put("data", dataMap);
            } else {
                dataClone.put("data", dataObj);
            }
            
            // Создаем финальную структуру запроса и преобразуем ее в строку для отладки
            Map<String, Object> payload = dataClone;
            
            try {
                ObjectMapper mapper = new ObjectMapper();
                String jsonPayload = mapper.writeValueAsString(payload);
                log.debug("JSON данные для отправки: {}", jsonPayload);
            } catch (Exception e) {
                log.warn("Не удалось сериализовать данные в JSON для логирования: {}", e.getMessage());
            }
            
            // Получаем CSRF-токен
            String csrfToken = getCsrfToken();
            
            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.add("X-CSRF-TOKEN", csrfToken);
            
            // Если это данные LSI, добавляем специальный заголовок с именем позиции
            if ("lsi".equals(dataType)) {
                Map<String, Object> lsiData = (Map<String, Object>) payload.get("data");
                if (lsiData.containsKey("position_name")) {
                    String positionName = String.valueOf(lsiData.get("position_name"));
                    headers.add("X-Position-Name", positionName);
                    log.debug("Добавлен заголовок X-Position-Name: {}", positionName);
                }
            }
            
            // Создаем HTTP-запрос
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);
            
            // Отправляем данные в IntBus
            log.info("Отправка HTTP-запроса в IntBus");
            ResponseEntity<String> response = restTemplate.postForEntity(syncUrl, request, String.class);
            
            // Логируем результат
            log.info("Ответ от IntBus: {} - {}", response.getStatusCodeValue(), response.getBody());
            
            return response;
        } catch (Exception e) {
            log.error("Ошибка при отправке данных в IntBus: {}", e.getMessage(), e);
            return new ResponseEntity<>("Ошибка при отправке данных: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    /**
     * Отправляет данные LSI в IntBus в формате {apikey, sender, data}
     * 
     * @param lsiItems Список элементов LSI
     * @return Ответ от сервера IntBus
     */
    public ResponseEntity<String> sendLSIData(List<Map<String, Object>> lsiItems) {
        try {
            // Получаем CSRF-токен
            String csrfToken = null;
            try {
                ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
                if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                    csrfToken = csrfResponse.getBody().get("token").toString();
                    System.out.println("Получен CSRF-токен: " + csrfToken);
                }
            } catch (Exception e) {
                System.err.println("Ошибка при получении CSRF-токена: " + e.getMessage());
            }

            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            // Добавляем CSRF-токен если он есть
            if (csrfToken != null) {
                headers.set("X-CSRFToken", csrfToken);
            }
            
            // Подготавливаем данные LSI с явным маркером типа данных
            Map<String, Object> lsiData = new HashMap<>();
            lsiData.put("type", "LSI_DATA");
            lsiData.put("items", lsiItems);  // Убираем dataType из вложенных данных
            
            // Создаем структуру данных в требуемом формате
            Map<String, Object> payload = new HashMap<>();
            payload.put("apikey", apiKey);
            payload.put("sender", sender);
            payload.put("data", lsiData);
            payload.put("dataType", "lsi");  // Добавляем dataType на верхний уровень
            
            // Преобразуем payload в JSON строку для отладки
            ObjectMapper objectMapper = new ObjectMapper();
            try {
                String jsonPayload = objectMapper.writeValueAsString(payload);
                System.out.println("Отправка данных ЛСИ в IntBus. JSON payload: " + jsonPayload);
            } catch (Exception e) {
                System.err.println("Ошибка при сериализации payload в JSON: " + e.getMessage());
            }
            
            // Выводим данные для отладки
            System.out.println("URL для отправки данных ЛСИ: " + syncUrl);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);
            
            // Отправляем запрос и возвращаем результат
            ResponseEntity<String> response = restTemplate.postForEntity(syncUrl, request, String.class);
            System.out.println("Ответ от сервера на отправку ЛСИ: " + response.getStatusCode() + ", body: " + response.getBody());
            
            return response;
        } catch (Exception e) {
            System.err.println("Ошибка при отправке данных ЛСИ: " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Ошибка при отправке данных ЛСИ: " + e.getMessage(), e);
        }
    }
    
    /**
     * Отправляет XML данные в IntBus в формате {apikey, sender, data}
     * 
     * @param xmlData XML данные в виде строки
     * @return Ответ от сервера IntBus
     */
    public ResponseEntity<String> sendXmlData(String xmlData) {
        HttpHeaders headers = createHeaders();
        
        // Создаем структуру данных в требуемом формате с XML в поле data
        Map<String, Object> payload = new HashMap<>();
        payload.put("apikey", apiKey);
        payload.put("sender", sender);
        payload.put("data", xmlData);
        payload.put("dataType", "xml"); // Добавляем dataType на верхний уровень
        
        // Преобразуем payload в JSON строку для отладки
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            String jsonPayload = objectMapper.writeValueAsString(payload);
            System.out.println("Отправка XML данных в IntBus. JSON payload: " + jsonPayload);
        } catch (Exception e) {
            System.err.println("Ошибка при сериализации payload в JSON: " + e.getMessage());
        }
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);
        
        // Отправляем запрос и возвращаем результат
        ResponseEntity<String> response = restTemplate.postForEntity(syncUrl, request, String.class);
        System.out.println("Ответ от сервера на отправку XML: " + response.getStatusCode() + ", body: " + response.getBody());
        
        return response;
    }
    
    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        // Получаем CSRF токен, если необходимо
        try {
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                headers.set("X-CSRF-TOKEN", csrfResponse.getBody().get("token").toString());
            }
        } catch (Exception e) {
            // Логируем ошибку, но продолжаем без CSRF токена
            System.err.println("Failed to obtain CSRF token: " + e.getMessage());
        }
        
        return headers;
    }

    private String getCsrfToken() {
        try {
            log.debug("Получение CSRF-токена с URL: {}", csrfUrl);
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                String token = csrfResponse.getBody().get("token").toString();
                log.debug("Получен CSRF-токен: {}", token);
                return token;
            } else {
                log.warn("CSRF-токен не найден в ответе");
                return null;
            }
        } catch (Exception e) {
            log.error("Ошибка при получении CSRF-токена: {}", e.getMessage());
            return null; // Продолжаем без токена
        }
    }
} 