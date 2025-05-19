import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const NomenclatureForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [nomenclature, setNomenclature] = useState({
    // Поля формата XML
    componentID: '',
    description: '',
    itemID: '',
    lastModifiedUser: '',
    name: '',
    owner: '',
    projectList: '',
    releaseStatus: '',
    revision: '',
    type: '',
    unitOfMeasure: '',
    // Старые поля (для обратной совместимости)
    abbreviation: '',
    shortName: '',
    fullName: '',
    internalCode: '',
    cipher: '',
    ekpsCode: '',
    kvtCode: '',
    drawingNumber: '',
    typeOfNomenclature: ''
  });
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const isEditMode = !!id;

  useEffect(() => {
    if (isEditMode) {
      fetchNomenclature();
    }
  }, [id]);

  const fetchNomenclature = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/nomenclature/${id}`);
      setNomenclature(response.data);
      setError(null);
    } catch (err) {
      setError('Ошибка при загрузке данных: ' + err.message);
      console.error('Ошибка при загрузке номенклатуры:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNomenclature(prev => {
      // Автоматически обновляем связанные поля
      const newState = { ...prev, [name]: value };
      
      // Синхронизация старых и новых полей
      if (name === 'fullName') newState.name = value;
      if (name === 'name') newState.fullName = value;
      
      if (name === 'internalCode') newState.itemID = value;
      if (name === 'itemID') newState.internalCode = value;
      
      if (name === 'typeOfNomenclature') newState.type = value;
      if (name === 'type') newState.typeOfNomenclature = value;
      
      return newState;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Валидация обязательных полей
    const errors = {};
    if (!nomenclature.name.trim()) errors.name = 'Название обязательно';
    if (!nomenclature.itemID.trim()) errors.itemID = 'ID элемента обязателен';
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    setIsSubmitting(true);
    setValidationErrors({});
    
    try {
      let response;
      
      // Установка правильных заголовков для запроса
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (isEditMode) {
        response = await axios.put(`/api/nomenclature/${id}`, nomenclature, { headers });
        setSaveStatus({ success: true, message: 'Номенклатура успешно обновлена!' });
      } else {
        response = await axios.post('/api/nomenclature', nomenclature, { headers });
        resetForm();
        setSaveStatus({ success: true, message: 'Номенклатура успешно создана!' });
      }
      
      setTimeout(() => {
        setSaveStatus(null);
      }, 3000);
    } catch (err) {
      console.error('Ошибка при сохранении номенклатуры:', err);
      
      // Улучшенная обработка ошибок
      let errorMessage = 'Ошибка при сохранении номенклатуры';
      
      if (err.response) {
        // Получаем данные ответа сервера
        if (typeof err.response.data === 'object') {
          errorMessage += `: ${JSON.stringify(err.response.data)}`;
        } else if (typeof err.response.data === 'string') {
          errorMessage += `: ${err.response.data}`;
        } else {
          errorMessage += `: Код ошибки ${err.response.status}`;
        }
      } else if (err.message) {
        errorMessage += `: ${err.message}`;
      }
      
      setSaveStatus({
        success: false,
        message: errorMessage
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleSendToIntBus = async () => {
    try {
      setLoading(true);
      setSuccessMessage(null);
      setError(null);
      
      const response = await axios.post(`/api/nomenclature/${id}/send-to-intbus`);
      setSuccessMessage('Данные успешно отправлены в IntBus');
    } catch (err) {
      setError('Ошибка при отправке данных в IntBus: ' + (err.response?.data || err.message));
      console.error('Ошибка при отправке данных в IntBus:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setNomenclature({
      // Поля формата XML
      componentID: '',
      description: '',
      itemID: '',
      lastModifiedUser: '',
      name: '',
      owner: '',
      projectList: '',
      releaseStatus: '',
      revision: '',
      type: '',
      unitOfMeasure: '',
      // Старые поля (для обратной совместимости)
      abbreviation: '',
      shortName: '',
      fullName: '',
      internalCode: '',
      cipher: '',
      ekpsCode: '',
      kvtCode: '',
      drawingNumber: '',
      typeOfNomenclature: ''
    });
  };

  if (loading && isEditMode) {
    return <div className="d-flex justify-content-center mt-5">
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Загрузка...</span>
      </div>
    </div>;
  }

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Главная</Link></li>
              <li className="breadcrumb-item"><Link to="/nomenclature">Номенклатура</Link></li>
              <li className="breadcrumb-item active" aria-current="page">
                {isEditMode ? `Редактирование #${id}` : 'Создание'}
              </li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card mb-4 shadow-sm">
        <div className="card-header bg-primary text-white">
          <h4 className="card-title mb-0">
            {isEditMode ? `Редактирование номенклатуры #${id}` : 'Создание новой номенклатуры'}
          </h4>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-danger" role="alert">{error}</div>}
          {successMessage && <div className="alert alert-success" role="alert">{successMessage}</div>}
          
          {saveStatus && (
            <div className={`alert ${saveStatus.success ? 'alert-success' : 'alert-danger'}`} role="alert">
              {saveStatus.message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Основные поля из XML формата */}
            <h5 className="mt-3 mb-3">Основная информация</h5>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="itemID" className="form-label">ID элемента *</label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.itemID ? 'is-invalid' : ''}`}
                  id="itemID"
                  name="itemID"
                  value={nomenclature.itemID}
                  onChange={handleInputChange}
                  required
                  placeholder="Например: IL114300-A-024-00-00-00-A-00/00"
                />
                {validationErrors.itemID && <div className="invalid-feedback">{validationErrors.itemID}</div>}
              </div>
              
              <div className="col-md-6 mb-3">
                <label htmlFor="name" className="form-label">Название *</label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.name ? 'is-invalid' : ''}`}
                  id="name"
                  name="name"
                  value={nomenclature.name}
                  onChange={handleInputChange}
                  required
                />
                {validationErrors.name && <div className="invalid-feedback">{validationErrors.name}</div>}
              </div>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="componentID" className="form-label">ID компонента</label>
                <input
                  type="text"
                  className="form-control"
                  id="componentID"
                  name="componentID"
                  value={nomenclature.componentID}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="col-md-6 mb-3">
                <label htmlFor="type" className="form-label">Тип</label>
                <input
                  type="text"
                  className="form-control"
                  id="type"
                  name="type"
                  value={nomenclature.type}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="revision" className="form-label">Ревизия</label>
                <input
                  type="text"
                  className="form-control"
                  id="revision"
                  name="revision"
                  value={nomenclature.revision}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="col-md-6 mb-3">
                <label htmlFor="lastModifiedUser" className="form-label">Последний редактировавший</label>
                <input
                  type="text"
                  className="form-control"
                  id="lastModifiedUser"
                  name="lastModifiedUser"
                  value={nomenclature.lastModifiedUser}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="mb-3">
              <label htmlFor="description" className="form-label">Описание</label>
              <textarea
                className="form-control"
                id="description"
                name="description"
                rows="5"
                value={nomenclature.description}
                onChange={handleInputChange}
              ></textarea>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="owner" className="form-label">Владелец</label>
                <input
                  type="text"
                  className="form-control"
                  id="owner"
                  name="owner"
                  value={nomenclature.owner}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="col-md-6 mb-3">
                <label htmlFor="projectList" className="form-label">Список проектов</label>
                <input
                  type="text"
                  className="form-control"
                  id="projectList"
                  name="projectList"
                  value={nomenclature.projectList}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="releaseStatus" className="form-label">Статус выпуска</label>
                <input
                  type="text"
                  className="form-control"
                  id="releaseStatus"
                  name="releaseStatus"
                  value={nomenclature.releaseStatus}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="col-md-6 mb-3">
                <label htmlFor="unitOfMeasure" className="form-label">Единица измерения</label>
                <input
                  type="text"
                  className="form-control"
                  id="unitOfMeasure"
                  name="unitOfMeasure"
                  value={nomenclature.unitOfMeasure}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            {/* Дополнительные поля (для обратной совместимости) */}
            <h5 className="mt-4 mb-3">Дополнительная информация</h5>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="abbreviation" className="form-label">Сокращение</label>
                <input
                  type="text"
                  className="form-control"
                  id="abbreviation"
                  name="abbreviation"
                  value={nomenclature.abbreviation}
                  onChange={handleInputChange}
                />
              </div>
              <div className="col-md-6 mb-3">
                <label htmlFor="shortName" className="form-label">Краткое название</label>
                <input
                  type="text"
                  className="form-control"
                  id="shortName"
                  name="shortName"
                  value={nomenclature.shortName}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="cipher" className="form-label">Шифр</label>
                <input
                  type="text"
                  className="form-control"
                  id="cipher"
                  name="cipher"
                  value={nomenclature.cipher}
                  onChange={handleInputChange}
                />
              </div>
              <div className="col-md-6 mb-3">
                <label htmlFor="drawingNumber" className="form-label">Номер чертежа</label>
                <input
                  type="text"
                  className="form-control"
                  id="drawingNumber"
                  name="drawingNumber"
                  value={nomenclature.drawingNumber}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="ekpsCode" className="form-label">Код ЕКПС</label>
                <input
                  type="text"
                  className="form-control"
                  id="ekpsCode"
                  name="ekpsCode"
                  value={nomenclature.ekpsCode}
                  onChange={handleInputChange}
                />
              </div>
              <div className="col-md-6 mb-3">
                <label htmlFor="kvtCode" className="form-label">Код КВТ</label>
                <input
                  type="text"
                  className="form-control"
                  id="kvtCode"
                  name="kvtCode"
                  value={nomenclature.kvtCode}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="d-flex justify-content-between mt-4">
              <div>
                <button type="submit" className="btn btn-primary me-2" disabled={loading || isSubmitting}>
                  {loading ? 'Сохранение...' : isSubmitting ? 'Сохранение...' : 'Сохранить'}
                </button>
                <Link to="/nomenclature" className="btn btn-secondary">Отмена</Link>
              </div>
              
              {isEditMode && (
                <button 
                  type="button" 
                  className="btn btn-success" 
                  onClick={handleSendToIntBus} 
                  disabled={loading}
                >
                  <i className="fas fa-share-square me-1"></i>
                  {loading ? 'Отправка...' : 'Отправить в IntBus'}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NomenclatureForm; 