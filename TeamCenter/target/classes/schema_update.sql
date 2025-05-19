-- Добавление новых колонок в таблицу nomenclatures
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS component_id VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS creation_date TIMESTAMP;
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS item_id VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS last_modified_date TIMESTAMP;
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS last_modified_user VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS project_list VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS release_status VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS revision VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS type VARCHAR(255);
ALTER TABLE nomenclatures ADD COLUMN IF NOT EXISTS unit_of_measure VARCHAR(255);

-- Обновление существующих данных для синхронизации новых и старых полей
UPDATE nomenclatures SET 
  name = full_name,
  item_id = internal_code,
  type = type_of_nomenclature,
  creation_date = CURRENT_TIMESTAMP(),
  last_modified_date = CURRENT_TIMESTAMP()
WHERE name IS NULL;

-- Добавляем ограничение NOT NULL для обязательных полей
ALTER TABLE nomenclatures ALTER COLUMN name SET NOT NULL;
ALTER TABLE nomenclatures ALTER COLUMN item_id SET NOT NULL; 