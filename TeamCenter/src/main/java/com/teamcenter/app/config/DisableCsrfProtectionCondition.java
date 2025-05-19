package com.teamcenter.app.config;

import org.springframework.context.annotation.Condition;
import org.springframework.context.annotation.ConditionContext;
import org.springframework.core.env.Environment;
import org.springframework.core.type.AnnotatedTypeMetadata;

/**
 * Условие для отключения CSRF-защиты во время отладки
 */
public class DisableCsrfProtectionCondition implements Condition {

    @Override
    public boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata) {
        Environment env = context.getEnvironment();
        
        // Условие - отключить CSRF в режиме разработки
        String[] activeProfiles = env.getActiveProfiles();
        for (String profile : activeProfiles) {
            if (profile.equals("dev") || profile.equals("development")) {
                return true;
            }
        }
        
        return Boolean.parseBoolean(env.getProperty("app.security.disable-csrf", "false"));
    }
} 