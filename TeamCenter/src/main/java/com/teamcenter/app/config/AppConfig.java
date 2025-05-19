package com.teamcenter.app.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.PropertyAccessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;

@Configuration
public class AppConfig {
    
    @Value("${intbus.http.connect-timeout:10000}")
    private int connectTimeout;
    
    @Value("${intbus.http.read-timeout:30000}")
    private int readTimeout;

    // Переименован бин для предотвращения конфликта с RestTemplate в RestTemplateConfig
    @Bean
    public RestTemplate customRestTemplate(RestTemplateBuilder builder) {
        // Создаем RestTemplate с кастомной конфигурацией
        RestTemplate restTemplate = builder
                .setConnectTimeout(Duration.ofMillis(connectTimeout))
                .setReadTimeout(Duration.ofMillis(readTimeout))
                .build();
        
        // Настраиваем Jackson для корректной сериализации и десериализации
        configureMessageConverters(restTemplate.getMessageConverters());
        
        // Устанавливаем обработчик ошибок, который не будет выбрасывать исключения на 401, 403, 404
        restTemplate.setErrorHandler(new DefaultResponseErrorHandler() {
            @Override
            public boolean hasError(org.springframework.http.client.ClientHttpResponse response) 
                    throws java.io.IOException {
                int statusCode = response.getStatusCode().value();
                // Не считаем ошибками коды 401, 403, 404 для более гибкой обработки
                return statusCode >= 500;
            }
        });
        
        return restTemplate;
    }
    
    /**
     * Настраивает HTTP конвертеры для правильной работы с JSON и текстом
     */
    private void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        // Настраиваем Jackson конвертер
        MappingJackson2HttpMessageConverter jacksonConverter = new MappingJackson2HttpMessageConverter();
        ObjectMapper objectMapper = new ObjectMapper();
        
        // Настраиваем видимость полей для сериализации
        objectMapper.setVisibility(PropertyAccessor.FIELD, JsonAutoDetect.Visibility.ANY);
        objectMapper.setVisibility(PropertyAccessor.GETTER, JsonAutoDetect.Visibility.NONE);
        objectMapper.setVisibility(PropertyAccessor.IS_GETTER, JsonAutoDetect.Visibility.NONE);
        objectMapper.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
        
        jacksonConverter.setObjectMapper(objectMapper);
        
        // Настраиваем StringHttpMessageConverter для корректной работы с UTF-8
        StringHttpMessageConverter stringConverter = new StringHttpMessageConverter(StandardCharsets.UTF_8);
        
        // Заменяем существующие конвертеры нашими
        for (int i = 0; i < converters.size(); i++) {
            if (converters.get(i) instanceof MappingJackson2HttpMessageConverter) {
                converters.set(i, jacksonConverter);
            } else if (converters.get(i) instanceof StringHttpMessageConverter) {
                converters.set(i, stringConverter);
            }
        }
        
        // Если конвертеры не были найдены, добавляем их
        boolean hasJacksonConverter = converters.stream()
                .anyMatch(converter -> converter instanceof MappingJackson2HttpMessageConverter);
        if (!hasJacksonConverter) {
            converters.add(jacksonConverter);
        }
        
        boolean hasStringConverter = converters.stream()
                .anyMatch(converter -> converter instanceof StringHttpMessageConverter);
        if (!hasStringConverter) {
            converters.add(stringConverter);
        }
    }
} 