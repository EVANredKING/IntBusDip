package com.teamcenter.app.controller;

import com.teamcenter.app.service.IntBusService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/intbus")
public class IntBusController {

    private final IntBusService intBusService;

    @Autowired
    public IntBusController(IntBusService intBusService) {
        this.intBusService = intBusService;
    }

    @PostMapping("/send")
    public ResponseEntity<String> sendDataToIntBus(@RequestBody Map<String, Object> data) {
        try {
            ResponseEntity<String> response = intBusService.sendDataToIntBus(data);
            return ResponseEntity.ok("Данные успешно отправлены в IntBus");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Ошибка при отправке данных: " + e.getMessage());
        }
    }

    @PostMapping("/send-lsi")
    public ResponseEntity<String> sendLSIData(@RequestBody List<Map<String, Object>> lsiItems) {
        try {
            ResponseEntity<String> response = intBusService.sendLSIData(lsiItems);
            return ResponseEntity.ok("Данные LSI успешно отправлены в IntBus");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Ошибка при отправке данных LSI: " + e.getMessage());
        }
    }
    
    @PostMapping("/send-xml")
    public ResponseEntity<String> sendXmlData(@RequestBody String xmlData) {
        try {
            ResponseEntity<String> response = intBusService.sendXmlData(xmlData);
            return ResponseEntity.ok("XML данные успешно отправлены в IntBus");
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Ошибка при отправке XML данных: " + e.getMessage());
        }
    }
} 