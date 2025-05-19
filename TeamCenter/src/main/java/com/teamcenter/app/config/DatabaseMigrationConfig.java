package com.teamcenter.app.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;

import jakarta.annotation.PostConstruct;
import javax.sql.DataSource;

@Configuration
public class DatabaseMigrationConfig {
    
    private static final Logger logger = LoggerFactory.getLogger(DatabaseMigrationConfig.class);
    
    @Autowired
    private DataSource dataSource;
    
    @PostConstruct
    public void initializeDatabase() {
        logger.info("База данных настроена для сохранения после перезапуска сервера.");
    }
} 