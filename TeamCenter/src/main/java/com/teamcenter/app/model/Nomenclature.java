package com.teamcenter.app.model;

import jakarta.persistence.*;
import java.util.Date;

@Entity
@Table(name = "nomenclatures")
public class Nomenclature {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "component_id")
    private String componentID;
    
    @Column(name = "creation_date")
    @Temporal(TemporalType.TIMESTAMP)
    private Date creationDate;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    @Column(name = "item_id")
    private String itemID;
    
    @Column(name = "last_modified_date")
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastModifiedDate;
    
    @Column(name = "last_modified_user")
    private String lastModifiedUser;
    
    @Column
    private String name;
    
    private String owner;
    
    @Column(name = "project_list")
    private String projectList;
    
    @Column(name = "release_status")
    private String releaseStatus;
    
    private String revision;
    
    private String type;
    
    @Column(name = "unit_of_measure")
    private String unitOfMeasure;
    
    // Сохраняем существующие поля для обратной совместимости
    @Column(name = "abbreviation")
    private String abbreviation;
    
    @Column(name = "short_name")
    private String shortName;
    
    @Column(name = "full_name")
    private String fullName;
    
    @Column(name = "internal_code")
    private String internalCode;
    
    @Column(name = "cipher")
    private String cipher;
    
    @Column(name = "ekps_code")
    private String ekpsCode;
    
    @Column(name = "kvt_code")
    private String kvtCode;
    
    @Column(name = "drawing_number")
    private String drawingNumber;
    
    @Column(name = "type_of_nomenclature")
    private String typeOfNomenclature;

    // Конструкторы
    public Nomenclature() {
        this.creationDate = new Date();
        this.lastModifiedDate = new Date();
    }

    // Новый основной конструктор
    public Nomenclature(String componentID, String description, String itemID, String lastModifiedUser,
                   String name, String owner, String projectList, String releaseStatus,
                   String revision, String type, String unitOfMeasure) {
        this.componentID = componentID;
        this.creationDate = new Date();
        this.description = description;
        this.itemID = itemID;
        this.lastModifiedDate = new Date();
        this.lastModifiedUser = lastModifiedUser;
        this.name = name;
        this.owner = owner;
        this.projectList = projectList;
        this.releaseStatus = releaseStatus;
        this.revision = revision;
        this.type = type;
        this.unitOfMeasure = unitOfMeasure;
    }
    
    // Для обратной совместимости
    public Nomenclature(String abbreviation, String shortName, String fullName, String internalCode, String cipher,
                        String ekpsCode, String kvtCode, String drawingNumber, String typeOfNomenclature) {
        this.abbreviation = abbreviation;
        this.shortName = shortName;
        this.fullName = fullName;
        this.internalCode = internalCode;
        this.cipher = cipher;
        this.ekpsCode = ekpsCode;
        this.kvtCode = kvtCode;
        this.drawingNumber = drawingNumber;
        this.typeOfNomenclature = typeOfNomenclature;
        this.creationDate = new Date();
        this.lastModifiedDate = new Date();
        // Автозаполнение полей формата XML из старых полей
        this.name = fullName;
        this.itemID = internalCode;
        this.type = typeOfNomenclature;
    }

    // Геттеры и сеттеры для новых полей
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getComponentID() {
        return componentID;
    }

    public void setComponentID(String componentID) {
        this.componentID = componentID;
    }

    public Date getCreationDate() {
        return creationDate;
    }

    public void setCreationDate(Date creationDate) {
        this.creationDate = creationDate;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getItemID() {
        return itemID;
    }

    public void setItemID(String itemID) {
        this.itemID = itemID;
    }

    public Date getLastModifiedDate() {
        return lastModifiedDate;
    }

    public void setLastModifiedDate(Date lastModifiedDate) {
        this.lastModifiedDate = lastModifiedDate;
    }

    public String getLastModifiedUser() {
        return lastModifiedUser;
    }

    public void setLastModifiedUser(String lastModifiedUser) {
        this.lastModifiedUser = lastModifiedUser;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getProjectList() {
        return projectList;
    }

    public void setProjectList(String projectList) {
        this.projectList = projectList;
    }

    public String getReleaseStatus() {
        return releaseStatus;
    }

    public void setReleaseStatus(String releaseStatus) {
        this.releaseStatus = releaseStatus;
    }

    public String getRevision() {
        return revision;
    }

    public void setRevision(String revision) {
        this.revision = revision;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getUnitOfMeasure() {
        return unitOfMeasure;
    }

    public void setUnitOfMeasure(String unitOfMeasure) {
        this.unitOfMeasure = unitOfMeasure;
    }
    
    // Геттеры и сеттеры для старых полей
    public String getAbbreviation() {
        return abbreviation;
    }

    public void setAbbreviation(String abbreviation) {
        this.abbreviation = abbreviation;
    }

    public String getShortName() {
        return shortName;
    }

    public void setShortName(String shortName) {
        this.shortName = shortName;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
        // Автоматически обновляем и новое поле
        this.name = fullName;
    }

    public String getInternalCode() {
        return internalCode;
    }

    public void setInternalCode(String internalCode) {
        this.internalCode = internalCode;
        // Автоматически обновляем и новое поле
        this.itemID = internalCode;
    }

    public String getCipher() {
        return cipher;
    }

    public void setCipher(String cipher) {
        this.cipher = cipher;
    }

    public String getEkpsCode() {
        return ekpsCode;
    }

    public void setEkpsCode(String ekpsCode) {
        this.ekpsCode = ekpsCode;
    }

    public String getKvtCode() {
        return kvtCode;
    }

    public void setKvtCode(String kvtCode) {
        this.kvtCode = kvtCode;
    }

    public String getDrawingNumber() {
        return drawingNumber;
    }

    public void setDrawingNumber(String drawingNumber) {
        this.drawingNumber = drawingNumber;
    }

    public String getTypeOfNomenclature() {
        return typeOfNomenclature;
    }

    public void setTypeOfNomenclature(String typeOfNomenclature) {
        this.typeOfNomenclature = typeOfNomenclature;
        // Автоматически обновляем и новое поле
        this.type = typeOfNomenclature;
    }

    @Override
    public String toString() {
        return "Nomenclature{" +
                "id=" + id +
                ", componentID='" + componentID + '\'' +
                ", itemID='" + itemID + '\'' +
                ", name='" + name + '\'' +
                ", type='" + type + '\'' +
                ", revision='" + revision + '\'' +
                '}';
    }
} 