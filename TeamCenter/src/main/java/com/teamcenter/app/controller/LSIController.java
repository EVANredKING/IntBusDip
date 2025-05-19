package com.teamcenter.app.controller;

import com.teamcenter.app.model.LSI;
import com.teamcenter.app.repository.LSIRepository;
import com.teamcenter.app.service.IntBusService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.util.HashMap;
import java.util.Map;

import java.util.List;
import java.util.Optional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;

@RestController
@RequestMapping("/api/lsi")
@CrossOrigin(origins = "http://localhost:3000", allowCredentials = "true", 
            allowedHeaders = "*", methods = {RequestMethod.GET, RequestMethod.POST, 
            RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS})
public class LSIController {

    private static final Logger logger = LoggerFactory.getLogger(LSIController.class);
    
    @Autowired
    private LSIRepository lsiRepository;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Autowired
    private IntBusService intBusService;
    
    @Value("${intbus.sync.url}")
    private String intbusSyncUrl;

    // Получить количество записей
    @GetMapping("/count")
    public Long getLSICount() {
        return lsiRepository.count();
    }

    // Получить все записи LSI
    @GetMapping
    public List<LSI> getAllLSIs() {
        return lsiRepository.findAll();
    }

    // Получить LSI по ID
    @GetMapping("/{id}")
    public ResponseEntity<LSI> getLSIById(@PathVariable Long id) {
        Optional<LSI> lsi = lsiRepository.findById(id);
        return lsi
                .map(value -> new ResponseEntity<>(value, HttpStatus.OK))
                .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    // Создать новую LSI
    @PostMapping
    public ResponseEntity<LSI> createLSI(@RequestBody LSI lsi) {
        LSI savedLSI = lsiRepository.save(lsi);
        return new ResponseEntity<>(savedLSI, HttpStatus.CREATED);
    }

    // Обновить существующую LSI
    @PutMapping("/{id}")
    public ResponseEntity<LSI> updateLSI(@PathVariable Long id, @RequestBody LSI lsiDetails) {
        Optional<LSI> optionalLSI = lsiRepository.findById(id);
        
        if (optionalLSI.isPresent()) {
            LSI lsi = optionalLSI.get();
            
            // Обновляем все поля LSI согласно формату XML
            lsi.setComponentID(lsiDetails.getComponentID());
            lsi.setDescription(lsiDetails.getDescription());
            lsi.setItemID(lsiDetails.getItemID());
            lsi.setLastModifiedDate(new java.util.Date());
            lsi.setLastModifiedUser(lsiDetails.getLastModifiedUser());
            lsi.setName(lsiDetails.getName());
            lsi.setOwner(lsiDetails.getOwner());
            lsi.setProjectList(lsiDetails.getProjectList());
            lsi.setReleaseStatus(lsiDetails.getReleaseStatus());
            lsi.setRevision(lsiDetails.getRevision());
            lsi.setType(lsiDetails.getType());
            lsi.setUnitOfMeasure(lsiDetails.getUnitOfMeasure());
            
            LSI updatedLSI = lsiRepository.save(lsi);
            return new ResponseEntity<>(updatedLSI, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }
    
    // Отправить данные LSI в IntBus
    @PostMapping("/sync/{id}")
    @CrossOrigin(origins = "http://localhost:3000", allowCredentials = "true")
    public ResponseEntity<String> sendToIntBus(
            @PathVariable("id") Long id, 
            @CookieValue(name = "XSRF-TOKEN", required = false) String csrfToken,
            @RequestHeader(value = "X-XSRF-TOKEN", required = false) String headerCsrfToken) {
        try {
            // Логируем запрос
            logger.info("Получен запрос на синхронизацию ЛСИ #{}", id);
            
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (optionalLSI.isPresent()) {
                LSI lsi = optionalLSI.get();
                
                // Формируем простую плоскую структуру данных без использования поля name
                Map<String, Object> lsiData = new HashMap<>();
                
                // 1. ID и базовые поля
                lsiData.put("id", lsi.getId());
                lsiData.put("uuid", lsi.getComponentID());
                lsiData.put("position_name", lsi.getName()); // Единственное упоминание имени через position_name
                lsiData.put("drawing_number", lsi.getItemID());
                
                // 2. Дополнительные поля
                if (lsi.getDescription() != null) {
                    lsiData.put("dns", lsi.getDescription());
                }
                
                if (lsi.getRevision() != null) {
                    lsiData.put("code_1", lsi.getRevision());
                }
                
                if (lsi.getType() != null) {
                    lsiData.put("code_2", lsi.getType());
                }
                
                if (lsi.getUnitOfMeasure() != null) {
                    lsiData.put("code_3", lsi.getUnitOfMeasure());
                }
                
                // 3. Создаем отдельные поля вместо custom_data
                if (lsi.getOwner() != null) {
                    lsiData.put("tc_owner", lsi.getOwner());
                }
                
                if (lsi.getReleaseStatus() != null) {
                    lsiData.put("tc_release_status", lsi.getReleaseStatus());
                }
                
                if (lsi.getProjectList() != null) {
                    lsiData.put("tc_project_list", lsi.getProjectList());
                }
                
                if (lsi.getLastModifiedUser() != null) {
                    lsiData.put("tc_last_modified_user", lsi.getLastModifiedUser());
                }
                
                // 4. Финальная структура запроса - dataType на верхнем уровне, не внутри data
                Map<String, Object> requestData = new HashMap<>();
                requestData.put("data", lsiData);
                requestData.put("source", "TeamCenter");
                requestData.put("dataType", "lsi");
                
                // Отладочная информация
                logger.debug("Подготовленные данные LSI: {}", lsiData.keySet());
                
                // Используем сервис для отправки данных
                try {
                    logger.info("Отправка данных LSI в IntBus: {}", requestData);
                    ResponseEntity<String> response = intBusService.sendDataToIntBus(requestData);
                    
                    if (response.getStatusCode().is2xxSuccessful()) {
                        return new ResponseEntity<>(response.getBody(), HttpStatus.OK);
                    } else {
                        String errorBody = response.getBody() != null ? response.getBody() : "Нет тела ответа";
                        logger.error("Ошибка ответа: {}", errorBody);
                        return new ResponseEntity<>("Ошибка при отправке данных: " + response.getStatusCode() + " " + errorBody, 
                                                  HttpStatus.INTERNAL_SERVER_ERROR);
                    }
                } catch (Exception e) {
                    logger.error("Ошибка при отправке данных в IntBus: {}", e.getMessage(), e);
                    return new ResponseEntity<>("Ошибка при отправке запроса: " + e.getMessage(), 
                                              HttpStatus.INTERNAL_SERVER_ERROR);
                }
            } else {
                logger.warn("LSI с ID {} не найдена", id);
                return new ResponseEntity<>("LSI не найдена", HttpStatus.NOT_FOUND);
            }
        } catch (Exception e) {
            logger.error("Общая ошибка в методе sendToIntBus: {}", e.getMessage(), e);
            return new ResponseEntity<>("Ошибка при отправке данных: " + e.getMessage(), 
                                      HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // Удалить LSI
    @DeleteMapping("/{id}")
    public ResponseEntity<HttpStatus> deleteLSI(@PathVariable Long id) {
        try {
            lsiRepository.deleteById(id);
            logger.info("LSI с ID {} успешно удалена", id);
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        } catch (Exception e) {
            logger.error("Ошибка при удалении LSI с ID {}: {}", id, e.getMessage(), e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // Удалить все записи LSI
    @DeleteMapping
    public ResponseEntity<HttpStatus> deleteAllLSIs() {
        try {
            lsiRepository.deleteAll();
            logger.info("Все записи LSI успешно удалены");
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        } catch (Exception e) {
            logger.error("Ошибка при удалении всех записей LSI: {}", e.getMessage(), e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    
    // Внутренний класс для обертки данных LSI
    private static class LSIWrapper {
        private LSI data;
        private String dataType;
        private String source;
        
        public LSI getData() {
            return data;
        }
        
        public void setData(LSI data) {
            this.data = data;
        }
        
        public String getDataType() {
            return dataType;
        }
        
        public void setDataType(String dataType) {
            this.dataType = dataType;
        }
        
        public String getSource() {
            return source;
        }
        
        public void setSource(String source) {
            this.source = source;
        }
    }

    // Диагностический метод для проверки структуры данных LSI
    @GetMapping("/diagnostic/{id}")
    public ResponseEntity<Map<String, Object>> diagnoseLSI(@PathVariable Long id) {
        try {
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (optionalLSI.isPresent()) {
                LSI lsi = optionalLSI.get();
                
                // Формируем структуру данных как для отправки, но возвращаем ее клиенту
                Map<String, Object> lsiData = new HashMap<>();
                
                // Базовые поля
                lsiData.put("id", lsi.getId());
                lsiData.put("uuid", lsi.getComponentID());
                lsiData.put("position_name", lsi.getName());
                lsiData.put("drawing_number", lsi.getItemID());
                
                // Дополнительные поля
                if (lsi.getDescription() != null) {
                    lsiData.put("dns", lsi.getDescription());
                }
                
                if (lsi.getRevision() != null) {
                    lsiData.put("code_1", lsi.getRevision());
                }
                
                if (lsi.getType() != null) {
                    lsiData.put("code_2", lsi.getType());
                }
                
                if (lsi.getUnitOfMeasure() != null) {
                    lsiData.put("code_3", lsi.getUnitOfMeasure());
                }
                
                // TeamCenter специфичные поля
                if (lsi.getOwner() != null) {
                    lsiData.put("tc_owner", lsi.getOwner());
                }
                
                if (lsi.getReleaseStatus() != null) {
                    lsiData.put("tc_release_status", lsi.getReleaseStatus());
                }
                
                if (lsi.getProjectList() != null) {
                    lsiData.put("tc_project_list", lsi.getProjectList());
                }
                
                if (lsi.getLastModifiedUser() != null) {
                    lsiData.put("tc_last_modified_user", lsi.getLastModifiedUser());
                }
                
                // Создаем итоговую структуру запроса
                Map<String, Object> requestData = new HashMap<>();
                requestData.put("data", lsiData);
                requestData.put("source", "TeamCenter");
                requestData.put("dataType", "lsi");
                
                return ResponseEntity.ok(requestData);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            logger.error("Ошибка при диагностике LSI: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    // Вызов прямого тестового эндпоинта IntBus
    @GetMapping("/test-intbus/{id}")
    public ResponseEntity<String> testIntBusConnection(@PathVariable Long id) {
        try {
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (!optionalLSI.isPresent()) {
                return ResponseEntity.notFound().build();
            }
            
            // Получаем данные LSI через диагностический метод
            ResponseEntity<Map<String, Object>> diagnosticResponse = diagnoseLSI(id);
            if (!diagnosticResponse.getStatusCode().is2xxSuccessful()) {
                return ResponseEntity.status(diagnosticResponse.getStatusCode())
                    .body("Не удалось получить диагностические данные LSI");
            }
            
            Map<String, Object> requestData = diagnosticResponse.getBody();
            
            // Проверяем соединение с IntBus
            try {
                // Получаем CSRF токен
                String csrfUrl = intbusSyncUrl.replace("/sync", "/get-csrf-token");
                ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
                String csrfToken = null;
                if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                    csrfToken = (String) csrfResponse.getBody().get("token");
                    logger.info("Получен CSRF токен для тестирования: {}", csrfToken);
                }
                
                // Создаем заголовки
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                if (csrfToken != null) {
                    headers.add("X-CSRF-TOKEN", csrfToken);
                }
                
                // Создаем запрос
                HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestData, headers);
                
                // Отправляем в IntBus
                String testUrl = intbusSyncUrl + "/test";  // Используем тестовый эндпоинт
                ResponseEntity<String> response = restTemplate.postForEntity(testUrl, request, String.class);
                
                logger.info("Тестовый ответ от IntBus: {} - {}", response.getStatusCode(), response.getBody());
                
                return ResponseEntity.ok("Тест соединения с IntBus: " + response.getStatusCode() + " - " + response.getBody());
            } catch (Exception e) {
                logger.error("Ошибка при тестировании соединения с IntBus: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Ошибка при тестировании соединения: " + e.getMessage());
            }
        } catch (Exception e) {
            logger.error("Общая ошибка при тестировании IntBus: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Общая ошибка при тестировании: " + e.getMessage());
        }
    }

    // Отправить данные LSI в IntBus с использованием строковых значений
    @PostMapping("/direct-sync/{id}")
    public ResponseEntity<String> sendToIntBusDirectly(@PathVariable Long id) {
        try {
            logger.info("Получен запрос на прямую синхронизацию ЛСИ #{}", id);
            
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (!optionalLSI.isPresent()) {
                return ResponseEntity.notFound().build();
            }
            
            LSI lsi = optionalLSI.get();
            
            // Создаем JSON строку напрямую, минуя Map
            StringBuilder jsonBuilder = new StringBuilder();
            jsonBuilder.append("{\n");
            jsonBuilder.append("  \"source\": \"TeamCenter\",\n");
            jsonBuilder.append("  \"dataType\": \"lsi\",\n");
            jsonBuilder.append("  \"data\": {\n");
            
            // Добавляем обязательные поля
            jsonBuilder.append("    \"id\": ").append(lsi.getId()).append(",\n");
            jsonBuilder.append("    \"uuid\": \"").append(escapeJson(lsi.getComponentID())).append("\",\n");
            jsonBuilder.append("    \"position_name\": \"").append(escapeJson(lsi.getName())).append("\",\n");
            jsonBuilder.append("    \"drawing_number\": \"").append(escapeJson(lsi.getItemID())).append("\"");
            
            // Добавляем опциональные поля, если они есть
            if (lsi.getDescription() != null) {
                jsonBuilder.append(",\n    \"dns\": \"").append(escapeJson(lsi.getDescription())).append("\"");
            }
            
            if (lsi.getRevision() != null) {
                jsonBuilder.append(",\n    \"code_1\": \"").append(escapeJson(lsi.getRevision())).append("\"");
            }
            
            if (lsi.getType() != null) {
                jsonBuilder.append(",\n    \"code_2\": \"").append(escapeJson(lsi.getType())).append("\"");
            }
            
            if (lsi.getUnitOfMeasure() != null) {
                jsonBuilder.append(",\n    \"code_3\": \"").append(escapeJson(lsi.getUnitOfMeasure())).append("\"");
            }
            
            jsonBuilder.append("\n  }\n");
            jsonBuilder.append("}");
            
            String jsonData = jsonBuilder.toString();
            logger.debug("Подготовленные данные LSI в JSON формате: {}", jsonData);
            
            // Получаем CSRF токен
            String csrfUrl = intbusSyncUrl.replace("/sync", "/get-csrf-token");
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            String csrfToken = null;
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                csrfToken = (String) csrfResponse.getBody().get("token");
            }
            
            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (csrfToken != null) {
                headers.add("X-CSRF-TOKEN", csrfToken);
            }
            
            // Добавляем заголовок с position_name
            headers.add("X-Position-Name", lsi.getName());
            
            // Создаем запрос
            HttpEntity<String> request = new HttpEntity<>(jsonData, headers);
            
            // Отправляем в IntBus
            ResponseEntity<String> response = restTemplate.postForEntity(intbusSyncUrl, request, String.class);
            
            logger.info("Ответ от IntBus на прямую отправку: {} - {}", response.getStatusCode(), response.getBody());
            
            if (response.getStatusCode().is2xxSuccessful()) {
                return ResponseEntity.ok("Данные успешно отправлены: " + response.getBody());
            } else {
                return ResponseEntity.status(response.getStatusCode())
                    .body("Ошибка при отправке данных: " + response.getBody());
            }
        } catch (Exception e) {
            logger.error("Ошибка при прямой отправке данных в IntBus: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Ошибка при отправке данных: " + e.getMessage());
        }
    }
    
    // Метод для экранирования JSON строк
    private String escapeJson(String input) {
        if (input == null) {
            return "";
        }
        return input.replace("\\", "\\\\")
                   .replace("\"", "\\\"")
                   .replace("\n", "\\n")
                   .replace("\r", "\\r")
                   .replace("\t", "\\t");
    }

    // Отправить данные LSI в IntBus с использованием минимального набора полей
    @PostMapping("/minimal-sync/{id}")
    public ResponseEntity<String> sendToIntBusMinimal(@PathVariable Long id) {
        try {
            logger.info("Получен запрос на минимальную синхронизацию ЛСИ #{}", id);
            
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (!optionalLSI.isPresent()) {
                return ResponseEntity.notFound().build();
            }
            
            LSI lsi = optionalLSI.get();
            
            // Создаем JSON строку с минимальным набором полей
            String jsonData = String.format(
                "{\n" +
                "  \"source\": \"TeamCenter\",\n" +
                "  \"dataType\": \"lsi\",\n" +
                "  \"data\": {\n" +
                "    \"id\": %d,\n" +
                "    \"uuid\": \"%s\",\n" +
                "    \"position_name\": \"%s\",\n" +
                "    \"drawing_number\": \"%s\"\n" +
                "  }\n" +
                "}",
                lsi.getId(),
                escapeJson(lsi.getComponentID()),
                escapeJson(lsi.getName()),
                escapeJson(lsi.getItemID())
            );
            
            logger.debug("Минимальные данные LSI в JSON формате: {}", jsonData);
            
            // Получаем CSRF токен
            String csrfUrl = intbusSyncUrl.replace("/sync", "/get-csrf-token");
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            String csrfToken = null;
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                csrfToken = (String) csrfResponse.getBody().get("token");
            }
            
            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (csrfToken != null) {
                headers.add("X-CSRF-TOKEN", csrfToken);
            }
            
            // Добавляем заголовок с position_name
            headers.add("X-Position-Name", lsi.getName());
            
            // Создаем запрос - отправляем как строку, а не как Map
            HttpEntity<String> request = new HttpEntity<>(jsonData, headers);
            
            try {
                // Отправляем в IntBus
                ResponseEntity<String> response = restTemplate.exchange(
                    intbusSyncUrl, 
                    org.springframework.http.HttpMethod.POST,
                    request, 
                    String.class
                );
                
                logger.info("Ответ от IntBus на минимальную отправку: {} - {}", response.getStatusCode(), response.getBody());
                
                if (response.getStatusCode().is2xxSuccessful()) {
                    return ResponseEntity.ok("Данные успешно отправлены: " + response.getBody());
                } else {
                    return ResponseEntity.status(response.getStatusCode())
                        .body("Ошибка при отправке данных: " + response.getBody());
                }
            } catch (org.springframework.web.client.HttpClientErrorException e) {
                logger.error("HTTP ошибка при отправке в IntBus: {}, Тело: {}", e.getStatusCode(), e.getResponseBodyAsString());
                return ResponseEntity.status(e.getStatusCode())
                    .body("Ошибка при отправке данных: " + e.getResponseBodyAsString());
            }
        } catch (Exception e) {
            logger.error("Ошибка при минимальной отправке данных в IntBus: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Ошибка при отправке данных: " + e.getMessage());
        }
    }

    // Отправить данные LSI в IntBus в raw формате
    @PostMapping("/raw-sync/{id}")
    public ResponseEntity<String> sendToIntBusRaw(@PathVariable Long id) {
        try {
            logger.info("Получен запрос на RAW синхронизацию ЛСИ #{}", id);
            
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (!optionalLSI.isPresent()) {
                return ResponseEntity.notFound().build();
            }
            
            LSI lsi = optionalLSI.get();
            
            // Создаем запрос в виде URL-encoded form data
            MultiValueMap<String, String> formData = new LinkedMultiValueMap<>();
            formData.add("source", "TeamCenter");
            formData.add("dataType", "lsi");
            formData.add("position_name", lsi.getName());
            formData.add("uuid", lsi.getComponentID());
            formData.add("id", lsi.getId().toString());
            formData.add("drawing_number", lsi.getItemID());
            
            // Получаем CSRF токен
            String csrfUrl = intbusSyncUrl.replace("/sync", "/get-csrf-token");
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            String csrfToken = null;
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                csrfToken = (String) csrfResponse.getBody().get("token");
            }
            
            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
            if (csrfToken != null) {
                headers.add("X-CSRF-TOKEN", csrfToken);
            }
            
            // Добавляем заголовок с position_name
            headers.add("X-Position-Name", lsi.getName());
            
            // Создаем запрос
            HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(formData, headers);
            
            try {
                // Получаем URL для raw-синхронизации
                String rawSyncUrl = intbusSyncUrl + "/raw";
                
                // Отправляем в IntBus
                ResponseEntity<String> response = restTemplate.exchange(
                    rawSyncUrl,
                    org.springframework.http.HttpMethod.POST,
                    request, 
                    String.class
                );
                
                logger.info("Ответ от IntBus на RAW отправку: {} - {}", response.getStatusCode(), response.getBody());
                
                if (response.getStatusCode().is2xxSuccessful()) {
                    return ResponseEntity.ok("Данные успешно отправлены: " + response.getBody());
                } else {
                    return ResponseEntity.status(response.getStatusCode())
                        .body("Ошибка при отправке данных: " + response.getBody());
                }
            } catch (org.springframework.web.client.HttpClientErrorException e) {
                logger.error("HTTP ошибка при RAW отправке в IntBus: {}, Тело: {}", e.getStatusCode(), e.getResponseBodyAsString());
                return ResponseEntity.status(e.getStatusCode())
                    .body("Ошибка при отправке данных: " + e.getResponseBodyAsString());
            }
        } catch (Exception e) {
            logger.error("Ошибка при RAW отправке данных в IntBus: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Ошибка при отправке данных: " + e.getMessage());
        }
    }

    // Отправить данные LSI в IntBus через специальный эндпоинт для TeamCenter LSI
    @PostMapping("/teamcenter-sync/{id}")
    public ResponseEntity<String> sendToTeamCenterLsiEndpoint(@PathVariable Long id) {
        try {
            logger.info("Получен запрос на отправку LSI #{} через специальный эндпоинт", id);
            
            Optional<LSI> optionalLSI = lsiRepository.findById(id);
            
            if (!optionalLSI.isPresent()) {
                return ResponseEntity.notFound().build();
            }
            
            LSI lsi = optionalLSI.get();
            
            // Создаем JSON с данными LSI в правильном формате для TeamCenterLSI
            String jsonData = String.format(
                "{\n" +
                "  \"source\": \"TeamCenter\",\n" +
                "  \"dataType\": \"lsi\",\n" +
                "  \"data\": {\n" +
                "    \"position_name\": \"%s\",\n" +
                "    \"uuid\": \"%s\",\n" +
                "    \"drawing_number\": \"%s\",\n" +
                "    \"dns\": \"%s\",\n" +
                "    \"code_1\": \"%s\",\n" +
                "    \"code_2\": \"%s\",\n" +
                "    \"code_3\": \"%s\"\n" +
                "  }\n" +
                "}",
                escapeJson(lsi.getName()),
                escapeJson(lsi.getComponentID()),
                escapeJson(lsi.getItemID()),
                escapeJson(lsi.getDescription() != null ? lsi.getDescription() : ""),
                escapeJson(lsi.getRevision() != null ? lsi.getRevision() : ""),
                escapeJson(lsi.getType() != null ? lsi.getType() : ""),
                escapeJson(lsi.getUnitOfMeasure() != null ? lsi.getUnitOfMeasure() : "")
            );
            
            logger.debug("Подготовленные данные LSI для специального эндпоинта: {}", jsonData);
            
            // Получаем CSRF токен
            String csrfUrl = intbusSyncUrl.replace("/sync", "/get-csrf-token");
            ResponseEntity<Map> csrfResponse = restTemplate.getForEntity(csrfUrl, Map.class);
            String csrfToken = null;
            if (csrfResponse.getBody() != null && csrfResponse.getBody().containsKey("token")) {
                csrfToken = (String) csrfResponse.getBody().get("token");
            }
            
            // Создаем заголовки
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (csrfToken != null) {
                headers.add("X-CSRF-TOKEN", csrfToken);
            }
            
            // Получаем URL для специального эндпоинта
            String specialEndpointUrl = intbusSyncUrl.replace("/sync", "/teamcenter-lsi");
            
            // Создаем запрос и отправляем
            HttpEntity<String> request = new HttpEntity<>(jsonData, headers);
            try {
                ResponseEntity<String> response = restTemplate.exchange(
                    specialEndpointUrl, 
                    org.springframework.http.HttpMethod.POST,
                    request, 
                    String.class
                );
                
                logger.info("Ответ от IntBus через специальный эндпоинт: {} - {}", 
                            response.getStatusCode(), response.getBody());
                
                if (response.getStatusCode().is2xxSuccessful()) {
                    return ResponseEntity.ok("Данные успешно отправлены: " + response.getBody());
                } else {
                    return ResponseEntity.status(response.getStatusCode())
                        .body("Ошибка при отправке данных: " + response.getBody());
                }
            } catch (org.springframework.web.client.HttpClientErrorException e) {
                logger.error("HTTP ошибка при отправке в IntBus через специальный эндпоинт: {}, Тело: {}", 
                             e.getStatusCode(), e.getResponseBodyAsString());
                return ResponseEntity.status(e.getStatusCode())
                    .body("Ошибка при отправке данных: " + e.getResponseBodyAsString());
            }
        } catch (Exception e) {
            logger.error("Ошибка при отправке данных в IntBus через специальный эндпоинт: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Ошибка при отправке данных: " + e.getMessage());
        }
    }
} 