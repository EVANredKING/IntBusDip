package com.teamcenter.app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class TeamCenterApplication {

    public static void main(String[] args) {
        SpringApplication.run(TeamCenterApplication.class, args);
    }
    
    // Bean RestTemplate перемещен в AppConfig
} 