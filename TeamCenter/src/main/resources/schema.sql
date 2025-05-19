-- Создание таблицы для LSI, если она не существует
CREATE TABLE IF NOT EXISTS lsi_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    component_id VARCHAR(255) NOT NULL,
    creation_date TIMESTAMP,
    description VARCHAR(2000),
    item_id VARCHAR(255) NOT NULL,
    last_modified_date TIMESTAMP,
    last_modified_user VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255),
    project_list VARCHAR(255),
    release_status VARCHAR(255),
    revision VARCHAR(50),
    type VARCHAR(255),
    unit_of_measure VARCHAR(50),
    CONSTRAINT uq_lsi_component_id UNIQUE (component_id),
    CONSTRAINT uq_lsi_item_id UNIQUE (item_id)
);

-- Создание таблицы для номенклатуры, если она не существует
CREATE TABLE IF NOT EXISTS nomenclatures (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    component_id VARCHAR(255) NOT NULL,
    creation_date TIMESTAMP,
    description VARCHAR(2000),
    item_id VARCHAR(255) NOT NULL,
    last_modified_date TIMESTAMP,
    last_modified_user VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255),
    project_list VARCHAR(255),
    release_status VARCHAR(255),
    revision VARCHAR(50),
    type VARCHAR(255),
    unit_of_measure VARCHAR(50),
    abbreviation VARCHAR(50),
    short_name VARCHAR(255),
    full_name VARCHAR(255),
    internal_code VARCHAR(100),
    cipher VARCHAR(100),
    ekps_code VARCHAR(100),
    kvt_code VARCHAR(100),
    drawing_number VARCHAR(100),
    type_of_nomenclature VARCHAR(100),
    CONSTRAINT uq_nomenclature_component_id UNIQUE (component_id),
    CONSTRAINT uq_nomenclature_item_id UNIQUE (item_id)
); 