package com.teamcenter.app.model;

import jakarta.persistence.*;
import java.util.Date;

@Entity
@Table(name = "lsi_items")
public class LSI {

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

    // Конструкторы
    public LSI() {
        this.creationDate = new Date();
        this.lastModifiedDate = new Date();
    }

    public LSI(String componentID, String description, String itemID, String lastModifiedUser,
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

    // Геттеры и сеттеры
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

    @Override
    public String toString() {
        return "LSI{" +
                "id=" + id +
                ", componentID='" + componentID + '\'' +
                ", itemID='" + itemID + '\'' +
                ", name='" + name + '\'' +
                ", type='" + type + '\'' +
                ", revision='" + revision + '\'' +
                '}';
    }
} 