package com.teamcenter.app.controller;

import com.teamcenter.app.model.LSI;
import com.teamcenter.app.model.Nomenclature;
import com.teamcenter.app.repository.LSIRepository;
import com.teamcenter.app.repository.NomenclatureRepository;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@RestController
@RequestMapping("/api/excel")
public class ExcelController {

    @Autowired
    private NomenclatureRepository nomenclatureRepository;

    @Autowired
    private LSIRepository lsiRepository;

    // Экспорт данных в Excel
    @GetMapping("/export")
    public ResponseEntity<InputStreamResource> exportExcel() throws IOException {
        // Получаем данные из репозиториев
        List<Nomenclature> nomenclatures = nomenclatureRepository.findAll();
        List<LSI> lsiItems = lsiRepository.findAll();

        // Создаем новую книгу Excel
        try (Workbook workbook = new XSSFWorkbook(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            // Создаем лист для номенклатуры
            Sheet nomenclatureSheet = workbook.createSheet("Nomenclature");
            
            // Заголовки столбцов для номенклатуры
            Row headerRow = nomenclatureSheet.createRow(0);
            headerRow.createCell(0).setCellValue("ID");
            headerRow.createCell(1).setCellValue("Abbreviation");
            headerRow.createCell(2).setCellValue("Short Name");
            headerRow.createCell(3).setCellValue("Full Name");
            headerRow.createCell(4).setCellValue("Internal Code");
            headerRow.createCell(5).setCellValue("Cipher");
            headerRow.createCell(6).setCellValue("EKPS Code");
            headerRow.createCell(7).setCellValue("KVT Code");
            headerRow.createCell(8).setCellValue("Drawing Number");
            headerRow.createCell(9).setCellValue("Type of Nomenclature");

            // Заполняем данными
            int rowIdx = 1;
            for (Nomenclature nomenclature : nomenclatures) {
                Row row = nomenclatureSheet.createRow(rowIdx++);
                row.createCell(0).setCellValue(nomenclature.getId());
                row.createCell(1).setCellValue(nomenclature.getAbbreviation());
                row.createCell(2).setCellValue(nomenclature.getShortName());
                row.createCell(3).setCellValue(nomenclature.getFullName());
                row.createCell(4).setCellValue(nomenclature.getInternalCode());
                row.createCell(5).setCellValue(nomenclature.getCipher());
                row.createCell(6).setCellValue(nomenclature.getEkpsCode());
                row.createCell(7).setCellValue(nomenclature.getKvtCode());
                row.createCell(8).setCellValue(nomenclature.getDrawingNumber());
                row.createCell(9).setCellValue(nomenclature.getTypeOfNomenclature());
            }

            // Авто-размер для колонок
            for (int i = 0; i < 10; i++) {
                nomenclatureSheet.autoSizeColumn(i);
            }

            // Создаем лист для LSI
            Sheet lsiSheet = workbook.createSheet("LSI");
            
            // Заголовки столбцов для LSI
            headerRow = lsiSheet.createRow(0);
            headerRow.createCell(0).setCellValue("ID");
            headerRow.createCell(1).setCellValue("Name");
            headerRow.createCell(2).setCellValue("Description");

            // Заполняем данными
            rowIdx = 1;
            for (LSI lsi : lsiItems) {
                Row row = lsiSheet.createRow(rowIdx++);
                row.createCell(0).setCellValue(lsi.getId());
                row.createCell(1).setCellValue(lsi.getName());
                row.createCell(2).setCellValue(lsi.getDescription());
            }

            // Авто-размер для колонок
            for (int i = 0; i < 3; i++) {
                lsiSheet.autoSizeColumn(i);
            }

            // Записываем книгу в выходной поток
            workbook.write(out);
            
            // Создаем HTTP-заголовки для скачивания файла
            HttpHeaders headers = new HttpHeaders();
            headers.add("Content-Disposition", "attachment; filename=atom_data.xlsx");
            
            return ResponseEntity
                    .ok()
                    .headers(headers)
                    .contentType(MediaType.parseMediaType("application/vnd.ms-excel"))
                    .body(new InputStreamResource(new ByteArrayInputStream(out.toByteArray())));
        }
    }

    // Импорт данных из Excel
    @PostMapping("/import")
    public ResponseEntity<String> importExcel(@RequestParam("file") MultipartFile file,
                                             @RequestParam(value = "clearExisting", defaultValue = "false") boolean clearExisting) {
        try {
            // Открываем книгу Excel
            Workbook workbook = WorkbookFactory.create(file.getInputStream());
            
            // Обрабатываем лист "Nomenclature"
            Sheet nomenclatureSheet = workbook.getSheet("Nomenclature");
            if (nomenclatureSheet != null) {
                // Очищаем существующие данные, если указано
                if (clearExisting) {
                    nomenclatureRepository.deleteAll();
                }
                
                // Пропускаем заголовок
                List<Nomenclature> nomenclatures = new ArrayList<>();
                for (int i = 1; i <= nomenclatureSheet.getLastRowNum(); i++) {
                    Row row = nomenclatureSheet.getRow(i);
                    if (row != null) {
                        Nomenclature nomenclature = new Nomenclature();
                        
                        // Пропускаем ID, он будет сгенерирован автоматически
                        nomenclature.setAbbreviation(getStringCellValue(row.getCell(1)));
                        nomenclature.setShortName(getStringCellValue(row.getCell(2)));
                        nomenclature.setFullName(getStringCellValue(row.getCell(3)));
                        nomenclature.setInternalCode(getStringCellValue(row.getCell(4)));
                        nomenclature.setCipher(getStringCellValue(row.getCell(5)));
                        nomenclature.setEkpsCode(getStringCellValue(row.getCell(6)));
                        nomenclature.setKvtCode(getStringCellValue(row.getCell(7)));
                        nomenclature.setDrawingNumber(getStringCellValue(row.getCell(8)));
                        nomenclature.setTypeOfNomenclature(getStringCellValue(row.getCell(9)));
                        
                        nomenclatures.add(nomenclature);
                    }
                }
                
                // Сохраняем данные
                nomenclatureRepository.saveAll(nomenclatures);
            }
            
            // Обрабатываем лист "LSI"
            Sheet lsiSheet = workbook.getSheet("LSI");
            if (lsiSheet != null) {
                // Очищаем существующие данные, если указано
                if (clearExisting) {
                    lsiRepository.deleteAll();
                }
                
                // Пропускаем заголовок
                List<LSI> lsiItems = new ArrayList<>();
                for (int i = 1; i <= lsiSheet.getLastRowNum(); i++) {
                    Row row = lsiSheet.getRow(i);
                    if (row != null) {
                        LSI lsi = new LSI();
                        
                        // Пропускаем ID, он будет сгенерирован автоматически
                        lsi.setName(getStringCellValue(row.getCell(1)));
                        lsi.setDescription(getStringCellValue(row.getCell(2)));
                        
                        lsiItems.add(lsi);
                    }
                }
                
                // Сохраняем данные
                lsiRepository.saveAll(lsiItems);
            }
            
            workbook.close();
            
            return ResponseEntity.ok("Данные успешно импортированы");
        } catch (IOException e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Ошибка при импорте данных: " + e.getMessage());
        }
    }
    
    // Вспомогательный метод для получения строковых значений из ячеек Excel
    private String getStringCellValue(Cell cell) {
        if (cell == null) {
            return "";
        }
        
        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue();
            case NUMERIC:
                return String.valueOf(cell.getNumericCellValue());
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            default:
                return "";
        }
    }
} 