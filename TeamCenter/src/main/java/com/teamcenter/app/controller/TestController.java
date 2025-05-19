package com.teamcenter.app.controller;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.teamcenter.app.service.IntBusService;

/**
 * Тестовый контроллер для проверки интеграции с IntBus.
 */
@RestController
@RequestMapping("/api/test")
public class TestController {

    @Autowired
    private IntBusService intBusService;

    /**
     * Тестовый метод для отправки простых данных в IntBus.
     * 
     * @return результат отправки
     */
    @GetMapping("/send-to-intbus")
    public ResponseEntity<String> testSendToIntBus() {
        try {
            System.out.println("Тестирование отправки данных в IntBus...");
            
            // Создаем тестовые данные
            Map<String, Object> testData = new HashMap<>();
            testData.put("testField", "testValue");
            testData.put("testNumber", 123);
            
            // Создаем вложенный объект
            Map<String, Object> nestedData = new HashMap<>();
            nestedData.put("nestedField", "nestedValue");
            testData.put("nestedObject", nestedData);
            
            // Отправляем данные в IntBus
            ResponseEntity<String> response = intBusService.sendDataToIntBus(testData);
            
            System.out.println("Результат отправки: " + response.getStatusCode());
            System.out.println("Тело ответа: " + response.getBody());
            
            return ResponseEntity.ok("Тест выполнен. Статус: " + response.getStatusCode() + 
                                     ", Тело: " + response.getBody());
        } catch (Exception e) {
            System.err.println("Ошибка при выполнении теста: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(500).body("Ошибка при выполнении теста: " + e.getMessage());
        }
    }

    /**
     * Тестовый метод для отправки данных ЛСИ в IntBus.
     * 
     * @return результат отправки
     */
    @GetMapping("/send-lsi-to-intbus")
    public ResponseEntity<String> testSendLSIToIntBus() {
        try {
            System.out.println("Тестирование отправки данных ЛСИ в IntBus...");
            
            // Создаем тестовые элементы ЛСИ
            List<Map<String, Object>> lsiItems = new ArrayList<>();
            
            // Элемент ЛСИ 1
            Map<String, Object> lsiItem1 = new HashMap<>();
            lsiItem1.put("name", "Тестовый элемент ЛСИ 1");
            lsiItem1.put("description", "Описание тестового элемента ЛСИ 1");
            lsiItem1.put("lsi_id", "LSI-TEST-001");
            lsiItems.add(lsiItem1);
            
            // Элемент ЛСИ 2
            Map<String, Object> lsiItem2 = new HashMap<>();
            lsiItem2.put("name", "Тестовый элемент ЛСИ 2");
            lsiItem2.put("description", "Описание тестового элемента ЛСИ 2");
            lsiItem2.put("lsi_id", "LSI-TEST-002");
            lsiItems.add(lsiItem2);
            
            // Отправляем данные ЛСИ в IntBus
            ResponseEntity<String> response = intBusService.sendLSIData(lsiItems);
            
            System.out.println("Результат отправки ЛСИ: " + response.getStatusCode());
            System.out.println("Тело ответа: " + response.getBody());
            
            return ResponseEntity.ok("Тест отправки ЛСИ выполнен. Статус: " + response.getStatusCode() + 
                                    ", Тело: " + response.getBody());
        } catch (Exception e) {
            System.err.println("Ошибка при выполнении теста отправки ЛСИ: " + e.getMessage());
            e.printStackTrace();
            return ResponseEntity.status(500).body("Ошибка при выполнении теста отправки ЛСИ: " + e.getMessage());
        }
    }
} 