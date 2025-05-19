package com.teamcenter.app.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.teamcenter.app.model.LSI;
import com.teamcenter.app.model.Nomenclature;
import com.teamcenter.app.repository.LSIRepository;
import com.teamcenter.app.repository.NomenclatureRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api")
public class SyncController {

    private static final Logger logger = LoggerFactory.getLogger(SyncController.class);

    @Autowired
    private NomenclatureRepository nomenclatureRepository;

    @Autowired
    private LSIRepository lsiRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Endpoint для приема данных из IntBus
     */
    @PostMapping("/sync-from-intbus")
    public ResponseEntity<Map<String, Object>> receiveDataFromIntBus(@RequestBody Map<String, Object> requestData) {
        try {
            logger.info("Получены данные из IntBus: {}", requestData.keySet());

            // Проверяем наличие необходимых полей
            if (!requestData.containsKey("data")) {
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Неверный формат данных. Отсутствует обязательное поле 'data'."
                ));
            }

            // Получаем тип данных (может быть на верхнем уровне или внутри data)
            String dataType = null;
            
            // Проверяем dataType на верхнем уровне
            if (requestData.containsKey("dataType")) {
                dataType = (String) requestData.get("dataType");
                logger.debug("Найден dataType на верхнем уровне: {}", dataType);
            } 
            // Если dataType не найден на верхнем уровне, ищем внутри data
            else {
                Object dataObj = requestData.get("data");
                if (dataObj instanceof Map) {
                    Map<String, Object> data = (Map<String, Object>) dataObj;
                    if (data.containsKey("dataType")) {
                        dataType = (String) data.get("dataType");
                        logger.debug("Найден dataType внутри объекта data: {}", dataType);
                    }
                }
            }
            
            // Если dataType все еще не найден, возвращаем ошибку
            if (dataType == null) {
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Неверный формат данных. Отсутствует обязательное поле 'dataType'."
                ));
            }
            
            Map<String, Object> data = null;
            
            // Получаем данные
            if (requestData.get("data") instanceof Map) {
                data = (Map<String, Object>) requestData.get("data");
            } else {
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Неверный формат поля 'data'. Ожидается объект."
                ));
            }

            // Обработка данных в зависимости от типа
            if ("nomenclature".equals(dataType)) {
                return processNomenclatureData(data);
            } else if ("lsi".equals(dataType)) {
                return processLsiData(data);
            } else {
                logger.warn("Получен неизвестный тип данных: {}", dataType);
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Неизвестный тип данных: " + dataType
                ));
            }
        } catch (Exception e) {
            logger.error("Ошибка при обработке данных из IntBus", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "status", "error",
                    "message", "Ошибка при обработке данных: " + e.getMessage()
            ));
        }
    }

    /**
     * Обработка данных номенклатуры
     */
    private ResponseEntity<Map<String, Object>> processNomenclatureData(Map<String, Object> data) {
        try {
            logger.debug("Обработка данных номенклатуры: {}", data.keySet());
            
            if (!data.containsKey("internalCode") || data.get("internalCode") == null) {
                logger.error("Отсутствует или пустой внутренний код номенклатуры");
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Отсутствует внутренний код номенклатуры"
                ));
            }

            String internalCode = String.valueOf(data.get("internalCode"));
            if (internalCode.trim().isEmpty()) {
                logger.error("Пустой внутренний код номенклатуры");
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Пустой внутренний код номенклатуры"
                ));
            }
            
            logger.info("Обработка номенклатуры из IntBus с внутренним кодом: {}", internalCode);

            // Проверяем существует ли номенклатура
            Optional<Nomenclature> existingItem = nomenclatureRepository.findByInternalCode(internalCode);

            Nomenclature nomenclature;
            boolean isNew = false;

            if (existingItem.isPresent()) {
                // Обновляем существующую запись
                nomenclature = existingItem.get();
                logger.info("Найдена существующая номенклатура с ID: {}", nomenclature.getId());
            } else {
                // Создаем новую номенклатуру
                nomenclature = new Nomenclature();
                nomenclature.setInternalCode(internalCode);
                isNew = true;
                logger.info("Создание новой номенклатуры с внутренним кодом: {}", internalCode);
            }

            // Безопасно обновляем поля с преобразованием типов
            if (data.containsKey("abbreviation") && data.get("abbreviation") != null) {
                nomenclature.setAbbreviation(String.valueOf(data.get("abbreviation")));
            }
            
            if (data.containsKey("shortName") && data.get("shortName") != null) {
                nomenclature.setShortName(String.valueOf(data.get("shortName")));
            }
            
            if (data.containsKey("fullName") && data.get("fullName") != null) {
                nomenclature.setFullName(String.valueOf(data.get("fullName")));
            }
            
            if (data.containsKey("cipher") && data.get("cipher") != null) {
                nomenclature.setCipher(String.valueOf(data.get("cipher")));
            }
            
            if (data.containsKey("ekpsCode") && data.get("ekpsCode") != null) {
                nomenclature.setEkpsCode(String.valueOf(data.get("ekpsCode")));
            }
            
            if (data.containsKey("kvtCode") && data.get("kvtCode") != null) {
                nomenclature.setKvtCode(String.valueOf(data.get("kvtCode")));
            }
            
            if (data.containsKey("drawingNumber") && data.get("drawingNumber") != null) {
                nomenclature.setDrawingNumber(String.valueOf(data.get("drawingNumber")));
            }
            
            if (data.containsKey("typeOfNomenclature") && data.get("typeOfNomenclature") != null) {
                nomenclature.setTypeOfNomenclature(String.valueOf(data.get("typeOfNomenclature")));
            }
            
            // Проверяем и устанавливаем обязательное поле name, пробуя разные варианты имени
            String name = null;
            
            // Пробуем получить поле name разными способами
            if (data.containsKey("name") && data.get("name") != null) {
                name = String.valueOf(data.get("name"));
                logger.debug("Используем поле name: {}", name);
            } else if (data.containsKey("NAME") && data.get("NAME") != null) {
                name = String.valueOf(data.get("NAME"));
                logger.debug("Используем поле NAME: {}", name);
            } else if (data.containsKey("shortName") && data.get("shortName") != null) {
                name = String.valueOf(data.get("shortName"));
                logger.info("Поле name отсутствует, используем shortName: {}", name);
            } else if (data.containsKey("fullName") && data.get("fullName") != null) {
                name = String.valueOf(data.get("fullName"));
                logger.info("Поля name и shortName отсутствуют, используем fullName: {}", name);
            } else {
                name = "Номенклатура-" + internalCode;
                logger.warn("Отсутствуют поля name, shortName и fullName. Используем сгенерированное имя: {}", name);
            }
            
            // Проверяем, что name не пустой
            if (name == null || name.trim().isEmpty()) {
                name = "Номенклатура-" + internalCode;
                logger.warn("Поле name пустое. Используем сгенерированное имя: {}", name);
            }
            
            nomenclature.setName(name);

            // Сохраняем запись
            try {
                nomenclatureRepository.save(nomenclature);
                logger.info("Номенклатура с ID {} успешно {}", nomenclature.getId(), isNew ? "создана" : "обновлена");
                
                return ResponseEntity.ok(Map.of(
                        "status", "success",
                        "message", "Номенклатура успешно " + (isNew ? "создана" : "обновлена"),
                        "id", nomenclature.getId()
                ));
            } catch (Exception e) {
                logger.error("Ошибка при сохранении номенклатуры: {}", e.getMessage(), e);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                        "status", "error",
                        "message", "Ошибка при сохранении номенклатуры: " + e.getMessage()
                ));
            }
        } catch (Exception e) {
            logger.error("Ошибка при обработке данных номенклатуры", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "status", "error",
                    "message", "Ошибка при обработке данных номенклатуры: " + e.getMessage()
            ));
        }
    }

    /**
     * Обработка данных LSI
     */
    private ResponseEntity<Map<String, Object>> processLsiData(Map<String, Object> data) {
        try {
            // Ищем название LSI в разных возможных полях
            String lsiName = null;
            
            logger.debug("Обработка данных LSI: {}", data.keySet());
            
            // Сначала проверяем position_name
            if (data.containsKey("position_name") && data.get("position_name") != null) {
                lsiName = String.valueOf(data.get("position_name"));
                logger.debug("Найдено поле position_name: {}", lsiName);
            } 
            // Затем проверяем поле name
            else if (data.containsKey("name") && data.get("name") != null) {
                lsiName = String.valueOf(data.get("name"));
                logger.debug("Найдено поле name: {}", lsiName);
            }
            // Также проверяем в custom_data
            else if (data.containsKey("custom_data") && data.get("custom_data") instanceof Map) {
                Map<String, Object> customData = (Map<String, Object>) data.get("custom_data");
                if (customData.containsKey("name") && customData.get("name") != null) {
                    lsiName = String.valueOf(customData.get("name"));
                    logger.debug("Найдено поле custom_data.name: {}", lsiName);
                }
            }
            
            // Если имя не найдено, возвращаем ошибку
            if (lsiName == null || lsiName.trim().isEmpty()) {
                logger.error("Не найдено название LSI в полях position_name, name или custom_data.name");
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "error",
                        "message", "Отсутствует название LSI (поле position_name, name или custom_data.name)"
                ));
            }
            
            logger.info("Обработка LSI из IntBus с названием: {}", lsiName);

            // Проверяем существует ли LSI
            Optional<LSI> existingLsi = lsiRepository.findByName(lsiName);

            LSI lsi;
            boolean isNew = false;

            if (existingLsi.isPresent()) {
                // Обновляем существующую запись
                lsi = existingLsi.get();
                logger.info("Найдена существующая LSI с ID: {}", lsi.getId());
            } else {
                // Создаем новую LSI
                lsi = new LSI();
                lsi.setName(lsiName);
                isNew = true;
                logger.info("Создание новой LSI с названием: {}", lsiName);
            }

            // Обновляем поля с маппингом полей из IntBus
            // Обработка описания - возможно разные ключи
            if (data.containsKey("description") && data.get("description") != null) {
                lsi.setDescription(String.valueOf(data.get("description")));
            } else if (data.containsKey("dns") && data.get("dns") != null) {
                lsi.setDescription(String.valueOf(data.get("dns")));
            }
            
            // Устанавливаем другие поля, если они есть
            if (data.containsKey("componentID") && data.get("componentID") != null) {
                lsi.setComponentID(String.valueOf(data.get("componentID")));
            } else if (data.containsKey("uuid") && data.get("uuid") != null) {
                lsi.setComponentID(String.valueOf(data.get("uuid")));
            }
            
            if (data.containsKey("itemID") && data.get("itemID") != null) {
                lsi.setItemID(String.valueOf(data.get("itemID")));
            } else if (data.containsKey("drawing_number") && data.get("drawing_number") != null) {
                lsi.setItemID(String.valueOf(data.get("drawing_number")));
            }

            if (data.containsKey("revision") && data.get("revision") != null) {
                lsi.setRevision(String.valueOf(data.get("revision")));
            }
            
            if (data.containsKey("type") && data.get("type") != null) {
                lsi.setType(String.valueOf(data.get("type")));
            }
            
            if (data.containsKey("unitOfMeasure") && data.get("unitOfMeasure") != null) {
                lsi.setUnitOfMeasure(String.valueOf(data.get("unitOfMeasure")));
            }
            
            if (data.containsKey("owner") && data.get("owner") != null) {
                lsi.setOwner(String.valueOf(data.get("owner")));
            }
            
            if (data.containsKey("releaseStatus") && data.get("releaseStatus") != null) {
                lsi.setReleaseStatus(String.valueOf(data.get("releaseStatus")));
            }
            
            // Сохраняем запись в базе данных
            lsiRepository.save(lsi);
            
            logger.info("LSI с ID {} успешно {}", lsi.getId(), isNew ? "создана" : "обновлена");

            return ResponseEntity.ok(Map.of(
                    "status", "success",
                    "message", "LSI успешно " + (isNew ? "создана" : "обновлена"),
                    "id", lsi.getId()
            ));
        } catch (Exception e) {
            logger.error("Ошибка при обработке данных LSI", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "status", "error",
                    "message", "Ошибка при обработке данных LSI: " + e.getMessage()
            ));
        }
    }
} 