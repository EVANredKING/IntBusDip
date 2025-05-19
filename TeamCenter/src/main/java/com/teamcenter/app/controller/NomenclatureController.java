package com.teamcenter.app.controller;

import com.teamcenter.app.model.Nomenclature;
import com.teamcenter.app.repository.NomenclatureRepository;
import com.teamcenter.app.service.IntBusService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import java.util.HashMap;
import java.util.Map;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/nomenclature")
@CrossOrigin(origins = "http://localhost:3000", allowCredentials = "true", 
            allowedHeaders = "*", methods = {RequestMethod.GET, RequestMethod.POST, 
            RequestMethod.PUT, RequestMethod.DELETE, RequestMethod.OPTIONS})
public class NomenclatureController {

    private static final Logger logger = LoggerFactory.getLogger(NomenclatureController.class);
    
    @Autowired
    private NomenclatureRepository nomenclatureRepository;
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Autowired
    private IntBusService intBusService;
    
    @Value("${intbus.sync.url}")
    private String intbusSyncUrl;

    // Получить количество записей
    @GetMapping("/count")
    public Long getNomenclatureCount() {
        return nomenclatureRepository.count();
    }

    // Получить все записи номенклатуры
    @GetMapping
    public List<Nomenclature> getAllNomenclatures() {
        return nomenclatureRepository.findAll();
    }

    // Получить номенклатуру по ID
    @GetMapping("/{id}")
    public ResponseEntity<Nomenclature> getNomenclatureById(@PathVariable Long id) {
        Optional<Nomenclature> nomenclature = nomenclatureRepository.findById(id);
        return nomenclature
                .map(value -> new ResponseEntity<>(value, HttpStatus.OK))
                .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
    }

    // Создать новую номенклатуру
    @PostMapping
    public ResponseEntity<Nomenclature> createNomenclature(@RequestBody Nomenclature nomenclature) {
        Nomenclature savedNomenclature = nomenclatureRepository.save(nomenclature);
        return new ResponseEntity<>(savedNomenclature, HttpStatus.CREATED);
    }

    // Обновить существующую номенклатуру
    @PutMapping("/{id}")
    public ResponseEntity<Nomenclature> updateNomenclature(@PathVariable Long id, @RequestBody Nomenclature nomenclatureDetails) {
        Optional<Nomenclature> optionalNomenclature = nomenclatureRepository.findById(id);
        
        if (optionalNomenclature.isPresent()) {
            Nomenclature nomenclature = optionalNomenclature.get();
            
            // Обновляем поля формата XML
            nomenclature.setComponentID(nomenclatureDetails.getComponentID());
            nomenclature.setDescription(nomenclatureDetails.getDescription());
            nomenclature.setItemID(nomenclatureDetails.getItemID());
            nomenclature.setLastModifiedDate(new java.util.Date());
            nomenclature.setLastModifiedUser(nomenclatureDetails.getLastModifiedUser());
            nomenclature.setName(nomenclatureDetails.getName());
            nomenclature.setOwner(nomenclatureDetails.getOwner());
            nomenclature.setProjectList(nomenclatureDetails.getProjectList());
            nomenclature.setReleaseStatus(nomenclatureDetails.getReleaseStatus());
            nomenclature.setRevision(nomenclatureDetails.getRevision());
            nomenclature.setType(nomenclatureDetails.getType());
            nomenclature.setUnitOfMeasure(nomenclatureDetails.getUnitOfMeasure());
            
            // Обновляем старые поля для обратной совместимости
            nomenclature.setAbbreviation(nomenclatureDetails.getAbbreviation());
            nomenclature.setShortName(nomenclatureDetails.getShortName());
            nomenclature.setFullName(nomenclatureDetails.getFullName());
            nomenclature.setInternalCode(nomenclatureDetails.getInternalCode());
            nomenclature.setCipher(nomenclatureDetails.getCipher());
            nomenclature.setEkpsCode(nomenclatureDetails.getEkpsCode());
            nomenclature.setKvtCode(nomenclatureDetails.getKvtCode());
            nomenclature.setDrawingNumber(nomenclatureDetails.getDrawingNumber());
            nomenclature.setTypeOfNomenclature(nomenclatureDetails.getTypeOfNomenclature());
            
            Nomenclature updatedNomenclature = nomenclatureRepository.save(nomenclature);
            return new ResponseEntity<>(updatedNomenclature, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(HttpStatus.NOT_FOUND);
        }
    }

    // Отправить данные номенклатуры в IntBus
    @PostMapping("/sync/{id}")
    @CrossOrigin(origins = "http://localhost:3000", allowCredentials = "true")
    public ResponseEntity<String> sendToIntBus(
            @PathVariable("id") Long id, 
            @CookieValue(name = "XSRF-TOKEN", required = false) String csrfToken,
            @RequestHeader(value = "X-XSRF-TOKEN", required = false) String headerCsrfToken) {
        try {
            // Логируем запрос
            logger.info("Получен запрос на синхронизацию номенклатуры #{}", id);
            
            Optional<Nomenclature> optionalNomenclature = nomenclatureRepository.findById(id);
            
            if (optionalNomenclature.isPresent()) {
                Nomenclature nomenclature = optionalNomenclature.get();
                
                // Формируем данные для отправки
                Map<String, Object> requestData = new HashMap<>();
                Map<String, Object> nomenclatureData = new HashMap<>();
                
                // Заполняем данными из номенклатуры (формата XML)
                nomenclatureData.put("id", nomenclature.getId());
                nomenclatureData.put("componentID", nomenclature.getComponentID());
                nomenclatureData.put("creationDate", nomenclature.getCreationDate());
                nomenclatureData.put("description", nomenclature.getDescription());
                nomenclatureData.put("itemID", nomenclature.getItemID());
                nomenclatureData.put("lastModifiedDate", nomenclature.getLastModifiedDate());
                nomenclatureData.put("lastModifiedUser", nomenclature.getLastModifiedUser());
                nomenclatureData.put("name", nomenclature.getName());
                nomenclatureData.put("owner", nomenclature.getOwner());
                nomenclatureData.put("projectList", nomenclature.getProjectList());
                nomenclatureData.put("releaseStatus", nomenclature.getReleaseStatus());
                nomenclatureData.put("revision", nomenclature.getRevision());
                nomenclatureData.put("type", nomenclature.getType());
                nomenclatureData.put("unitOfMeasure", nomenclature.getUnitOfMeasure());
                
                // Также добавляем старые поля для совместимости
                nomenclatureData.put("abbreviation", nomenclature.getAbbreviation());
                nomenclatureData.put("shortName", nomenclature.getShortName());
                nomenclatureData.put("fullName", nomenclature.getFullName());
                nomenclatureData.put("internalCode", nomenclature.getInternalCode());
                nomenclatureData.put("cipher", nomenclature.getCipher());
                nomenclatureData.put("ekpsCode", nomenclature.getEkpsCode());
                nomenclatureData.put("kvtCode", nomenclature.getKvtCode());
                nomenclatureData.put("drawingNumber", nomenclature.getDrawingNumber());
                nomenclatureData.put("typeOfNomenclature", nomenclature.getTypeOfNomenclature());
                
                // Формируем финальный запрос
                requestData.put("data", nomenclatureData);
                requestData.put("dataType", "nomenclature");
                requestData.put("source", "TeamCenter");
                
                // Используем сервис для отправки данных
                try {
                    ResponseEntity<String> response = intBusService.sendDataToIntBus(requestData);
                    
                    if (response.getStatusCode().is2xxSuccessful()) {
                        return new ResponseEntity<>(response.getBody(), HttpStatus.OK);
                    } else {
                        String errorBody = response.getBody() != null ? response.getBody() : "Нет тела ответа";
                        logger.error("Ошибка ответа: {}", errorBody);
                        return new ResponseEntity<>("Ошибка при отправке данных: " + response.getStatusCode() + " " + errorBody, 
                                                  HttpStatus.INTERNAL_SERVER_ERROR);
                    }
                } catch (Exception e) {
                    logger.error("Ошибка при отправке данных в IntBus: {}", e.getMessage(), e);
                    return new ResponseEntity<>("Ошибка при отправке запроса: " + e.getMessage(), 
                                              HttpStatus.INTERNAL_SERVER_ERROR);
                }
            } else {
                logger.warn("Номенклатура с ID {} не найдена", id);
                return new ResponseEntity<>("Номенклатура не найдена", HttpStatus.NOT_FOUND);
            }
        } catch (Exception e) {
            logger.error("Общая ошибка в методе sendToIntBus: {}", e.getMessage(), e);
            return new ResponseEntity<>("Ошибка при отправке данных: " + e.getMessage(), 
                                      HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // Удалить номенклатуру
    @DeleteMapping("/{id}")
    public ResponseEntity<HttpStatus> deleteNomenclature(@PathVariable Long id) {
        try {
            nomenclatureRepository.deleteById(id);
            logger.info("Номенклатура с ID {} успешно удалена", id);
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        } catch (Exception e) {
            logger.error("Ошибка при удалении номенклатуры с ID {}: {}", id, e.getMessage(), e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // Удалить все записи номенклатуры
    @DeleteMapping
    public ResponseEntity<HttpStatus> deleteAllNomenclatures() {
        try {
            nomenclatureRepository.deleteAll();
            logger.info("Все записи номенклатуры успешно удалены");
            return new ResponseEntity<>(HttpStatus.NO_CONTENT);
        } catch (Exception e) {
            logger.error("Ошибка при удалении всех записей номенклатуры: {}", e.getMessage(), e);
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
} 