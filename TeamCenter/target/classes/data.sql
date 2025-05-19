-- Добавление тестовых данных для LSI
INSERT INTO lsi_items (
    component_id, creation_date, description, item_id, last_modified_date, last_modified_user,
    name, owner, project_list, release_status, revision, type, unit_of_measure
) 
SELECT 
    'husN3fpxYS_s5DAAAAAAAAAAAAA', CURRENT_TIMESTAMP(), 'Тестовое описание', 'IL114300-A-024-00-00-00-A-00/00',
    CURRENT_TIMESTAMP(), 'Вахитов Р.Ю. (vakhitovry)', 'Система электроснабжения', 'multisite (multisite)',
    '', '', '00', 'IL2_OpSystemRevision', ''
WHERE NOT EXISTS (
    SELECT 1 FROM lsi_items WHERE component_id = 'husN3fpxYS_s5DAAAAAAAAAAAAA'
);

-- Добавление тестовых данных для номенклатуры
INSERT INTO nomenclatures (
    component_id, creation_date, description, item_id, last_modified_date, last_modified_user,
    name, owner, project_list, release_status, revision, type, unit_of_measure,
    abbreviation, short_name, full_name, internal_code, cipher, ekps_code, kvt_code, drawing_number, type_of_nomenclature
) 
SELECT
    'xyzABC123_456DEFGHIJKLMNOPQ', CURRENT_TIMESTAMP(), 'Тестовая номенклатура', 'NM123456-B-001-00-00-00-B-00/01',
    CURRENT_TIMESTAMP(), 'Иванов И.И. (ivanovii)', 'Блок управления системой электроснабжения', 'engineer (engineer)',
    '', '', '01', 'IL2_ControlBlock', '',
    'БУ', 'Блок управления', 'Блок управления системой электроснабжения', 'NM123456-B-001-00-00-00-B-00/01',
    'БУ-001', '654321', '789012', 'ЧЕРТЕЖ-001-2023', 'Блок'
WHERE NOT EXISTS (
    SELECT 1 FROM nomenclatures WHERE component_id = 'xyzABC123_456DEFGHIJKLMNOPQ'
); 