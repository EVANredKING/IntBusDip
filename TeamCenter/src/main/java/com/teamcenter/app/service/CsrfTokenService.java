package com.teamcenter.app.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class CsrfTokenService {

    private static final Logger logger = LoggerFactory.getLogger(CsrfTokenService.class);
    
    @Value("${intbus.sync.url}")
    private String intbusSyncUrl;
    
    @Autowired
    private RestTemplate restTemplate;
    
    private String csrfToken;
    private long lastFetchTime = 0;
    private static final long TOKEN_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 минут
    
    /**
     * Получает CSRF-токен с сервера Django
     */
    public String getCsrfToken() {
        long currentTime = System.currentTimeMillis();
        
        // Проверяем, нужно ли обновить токен
        if (csrfToken == null || currentTime - lastFetchTime > TOKEN_REFRESH_INTERVAL) {
            fetchCsrfToken();
        }
        
        return csrfToken;
    }
    
    /**
     * Извлекает CSRF-токен из ответа сервера
     */
    private void fetchCsrfToken() {
        try {
            logger.debug("Получение CSRF-токена с сервера Django");
            
            // URL для загрузки страницы
            String baseUrl;
            try {
                if (intbusSyncUrl.contains("/sync/api/sync")) {
                    baseUrl = intbusSyncUrl.substring(0, intbusSyncUrl.indexOf("/sync/api/sync"));
                } else if (intbusSyncUrl.contains("/api/sync")) {
                    baseUrl = intbusSyncUrl.substring(0, intbusSyncUrl.indexOf("/api/sync"));
                } else {
                    baseUrl = "http://localhost:8081";
                    logger.warn("Не удалось корректно извлечь базовый URL, используем значение по умолчанию: {}", baseUrl);
                }
            } catch (Exception e) {
                baseUrl = "http://localhost:8081";
                logger.warn("Ошибка при извлечении базового URL: {}, используем значение по умолчанию: {}", e.getMessage(), baseUrl);
            }
            
            String csrfUrl = baseUrl + "/";
            
            logger.info("URL для получения CSRF-токена: {}", csrfUrl);
            
            // Выполняем GET-запрос для получения cookies
            HttpHeaders headers = new HttpHeaders();
            headers.add("User-Agent", "Mozilla/5.0 TeamCenter Integration");
            HttpEntity<String> entity = new HttpEntity<>(headers);
            
            try {
                ResponseEntity<String> response = restTemplate.exchange(
                    csrfUrl, 
                    HttpMethod.GET, 
                    entity, 
                    String.class
                );
                
                logger.info("Получен ответ от сервера, статус: {}", response.getStatusCode());
                
                // Извлекаем CSRF-токен из cookies
                List<String> cookies = response.getHeaders().get("Set-Cookie");
                if (cookies != null && !cookies.isEmpty()) {
                    logger.debug("Получены cookies: {}", cookies);
                    
                    for (String cookie : cookies) {
                        if (cookie.contains("csrftoken")) {
                            logger.debug("Найден cookie с csrftoken: {}", cookie);
                            
                            Pattern pattern = Pattern.compile("csrftoken=([^;]+)");
                            Matcher matcher = pattern.matcher(cookie);
                            if (matcher.find()) {
                                csrfToken = matcher.group(1);
                                logger.debug("Извлечен токен: {}, длина: {}", csrfToken, csrfToken.length());
                                
                                // Django может использовать токены разной длины (32, 64), поэтому мы не будем строго проверять длину
                                lastFetchTime = System.currentTimeMillis();
                                logger.info("Получен CSRF-токен из cookies: {}...[обрезано]", 
                                    csrfToken.length() > 8 ? csrfToken.substring(0, 8) : csrfToken);
                                return;
                            } else {
                                logger.warn("Cookie csrftoken найден, но не удалось извлечь значение: {}", cookie);
                            }
                        }
                    }
                    
                    logger.warn("Cookie csrftoken не найден среди полученных cookies");
                } else {
                    logger.warn("Cookies не получены в ответе от сервера");
                }
                
                // Если токен не найден в cookies, ищем в содержимом страницы
                String pageContent = response.getBody();
                if (pageContent != null && !pageContent.isEmpty()) {
                    logger.debug("Размер тела ответа: {} байт", pageContent.length());
                    
                    // Ищем токен в странице (Django часто вставляет его в форму)
                    Pattern pattern = Pattern.compile("name=['\"]csrfmiddlewaretoken['\"]\\s+value=['\"]([^'\"]+)['\"]");
                    Matcher matcher = pattern.matcher(pageContent);
                    if (matcher.find()) {
                        csrfToken = matcher.group(1);
                        logger.debug("Извлечен токен из HTML: {}, длина: {}", csrfToken, csrfToken.length());
                        
                        lastFetchTime = System.currentTimeMillis();
                        logger.info("Получен CSRF-токен из содержимого страницы: {}...[обрезано]", 
                            csrfToken.length() > 8 ? csrfToken.substring(0, 8) : csrfToken);
                        return;
                    } else {
                        logger.warn("Токен не найден в содержимом страницы");
                        
                        // Отладочная информация: выводим начало содержимого страницы
                        int previewLength = Math.min(200, pageContent.length());
                        logger.debug("Начало содержимого страницы: {}", pageContent.substring(0, previewLength));
                    }
                } else {
                    logger.warn("Пустое тело ответа от сервера");
                }
                
                // Если дошли до этой точки, значит токен не найден
                // Создаем временный токен для тестирования
                if (csrfToken == null || csrfToken.isEmpty()) {
                    csrfToken = "temporaryToken123456789";
                    logger.warn("CSRF-токен не найден, используем временный токен для тестирования: {}", csrfToken);
                    lastFetchTime = System.currentTimeMillis();
                }
                
            } catch (Exception e) {
                logger.error("Ошибка при выполнении запроса к серверу Django: {}", e.getMessage(), e);
                // Установка временного токена для тестирования
                csrfToken = "temporaryToken123456789";
                logger.warn("Установлен временный токен для тестирования: {}", csrfToken);
                lastFetchTime = System.currentTimeMillis();
            }
            
        } catch (Exception e) {
            logger.error("Критическая ошибка при получении CSRF-токена: {}", e.getMessage(), e);
            // Установка временного токена для тестирования
            csrfToken = "temporaryToken123456789";
            logger.warn("Установлен временный токен для тестирования из-за ошибки: {}", csrfToken);
            lastFetchTime = System.currentTimeMillis();
        }
    }
} 