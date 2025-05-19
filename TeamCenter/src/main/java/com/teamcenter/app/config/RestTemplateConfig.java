package com.teamcenter.app.config;



import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.BufferingClientHttpRequestFactory;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;

@Configuration
public class RestTemplateConfig {

    @Value("${intbus.http.connect-timeout:30000}")
    private int connectTimeout;

    @Value("${intbus.http.read-timeout:30000}")
    private int readTimeout;
    
    @Value("${intbus.http.connection-request-timeout:30000}")
    private int connectionRequestTimeout;

    // Переименован бин для предотвращения конфликта с RestTemplate в AppConfig
    @Bean
    public RestTemplate bufferingRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeout);
        factory.setReadTimeout(readTimeout);
        
        // Используем буфер для тела запроса - это поможет с отладкой
        BufferingClientHttpRequestFactory bufferingFactory = new BufferingClientHttpRequestFactory(factory);
        
        RestTemplate restTemplate = new RestTemplate(bufferingFactory);
        
        // Добавляем конвертеры для JSON
        MappingJackson2HttpMessageConverter jacksonConverter = new MappingJackson2HttpMessageConverter();
        StringHttpMessageConverter stringConverter = new StringHttpMessageConverter();
        
        // Устанавливаем конвертеры
        restTemplate.getMessageConverters().add(0, jacksonConverter);
        restTemplate.getMessageConverters().add(1, stringConverter);
        
        return restTemplate;
    }
    
    // Бин для обратной совместимости
    @Bean
    public RestTemplate restTemplate() {
        return bufferingRestTemplate();
    }
    
    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }
} 