package com.teamcenter.app.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.web.servlet.config.annotation.ContentNegotiationConfigurer;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.PathResourceResolver;

import java.io.File;
import java.io.IOException;
import java.util.Map;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("http://localhost:3000")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }
    
    @Override
    public void configureContentNegotiation(ContentNegotiationConfigurer configurer) {
        configurer
            .favorParameter(false)
            .ignoreAcceptHeader(false)
            .useRegisteredExtensionsOnly(false)
            .defaultContentType(MediaType.TEXT_HTML)
            .mediaType("html", MediaType.TEXT_HTML)
            .mediaType("xml", MediaType.APPLICATION_XML)
            .mediaType("json", MediaType.APPLICATION_JSON)
            .mediaType("js", MediaType.valueOf("application/javascript"))
            .mediaType("css", MediaType.valueOf("text/css"))
            .mediaType("png", MediaType.IMAGE_PNG)
            .mediaType("jpg", MediaType.IMAGE_JPEG)
            .mediaType("jpeg", MediaType.IMAGE_JPEG)
            .mediaType("gif", MediaType.IMAGE_GIF);
    }
    
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/**")
                // Проверяем сначала в classpath:/static/, а если не нашли, то во frontend/build/
                .addResourceLocations("classpath:/static/", "file:frontend/build/", "file:/app/frontend/build/")
                .setCachePeriod(3600)
                .resourceChain(true)
                .addResolver(new PathResourceResolver() {
                    @Override
                    protected Resource getResource(String resourcePath, Resource location) throws IOException {
                        Resource requestedResource = location.createRelative(resourcePath);
                        
                        // Если запрошенный ресурс существует, возвращаем его
                        if (requestedResource.exists() && requestedResource.isReadable()) {
                            return requestedResource;
                        }
                        
                        // Если ресурс не найден и это не запрос к API, возвращаем index.html
                        if (!resourcePath.startsWith("api/")) {
                            // Проверяем frontend/build/index.html
                            File frontendBuild = new File("frontend/build/index.html");
                            if (frontendBuild.exists()) {
                                return new FileSystemResource(frontendBuild);
                            }
                            
                            // Проверяем /app/frontend/build/index.html (для Docker)
                            File dockerBuild = new File("/app/frontend/build/index.html");
                            if (dockerBuild.exists()) {
                                return new FileSystemResource(dockerBuild);
                            }
                            
                            // Если и там не нашли, пытаемся вернуть из classpath
                            return new ClassPathResource("/static/index.html");
                        }
                        
                        return null;
                    }
                });
        
        // Добавляем специальный обработчик для JavaScript файлов
        registry.addResourceHandler("/**/*.js")
                .addResourceLocations("classpath:/static/js/", "file:frontend/build/static/js/", "file:/app/frontend/build/static/js/")
                .setCachePeriod(3600)
                .resourceChain(true);
                
        // Добавляем специальный обработчик для CSS файлов
        registry.addResourceHandler("/**/*.css")
                .addResourceLocations("classpath:/static/css/", "file:frontend/build/static/css/", "file:/app/frontend/build/static/css/")
                .setCachePeriod(3600)
                .resourceChain(true);
    }
} 