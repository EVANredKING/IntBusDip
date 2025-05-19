package com.teamcenter.app.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // Правило для JavaScript файлов
        registry.addResourceHandler("/static/js/**")
                .addResourceLocations("file:frontend/build/static/js/", "file:/app/frontend/build/static/js/", "classpath:/static/js/")
                .setCachePeriod(3600);
                
        // Правило для CSS файлов
        registry.addResourceHandler("/static/css/**")
                .addResourceLocations("file:frontend/build/static/css/", "file:/app/frontend/build/static/css/", "classpath:/static/css/")
                .setCachePeriod(3600);
                
        // Правило для медиа-файлов
        registry.addResourceHandler("/static/media/**")
                .addResourceLocations("file:frontend/build/static/media/", "file:/app/frontend/build/static/media/", "classpath:/static/media/")
                .setCachePeriod(3600);
                
        // Правило для корневых файлов (favicon.ico, manifest.json и т.д.)
        registry.addResourceHandler("/*.ico", "/*.json", "/*.png")
                .addResourceLocations("file:frontend/build/", "file:/app/frontend/build/", "classpath:/static/")
                .setCachePeriod(3600);
                
        // Правило по умолчанию для всех остальных статических ресурсов
        registry.addResourceHandler("/**")
                .addResourceLocations("file:frontend/build/", "file:/app/frontend/build/", "classpath:/static/")
                .setCachePeriod(3600);
    }
    
    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        // Маршрутизация всех путей, не начинающихся с /api, на index.html
        registry.addViewController("/").setViewName("forward:/index.html");
        registry.addViewController("/{x:[^\\.]*}").setViewName("forward:/index.html");
        registry.addViewController("/{x:^(?!api$).*$}/**/{y:[^\\.]*}").setViewName("forward:/index.html");
    }
} 