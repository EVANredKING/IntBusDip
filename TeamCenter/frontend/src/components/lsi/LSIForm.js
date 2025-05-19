import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const LSIForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [lsi, setLsi] = useState({
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
    unitOfMeasure: ''
  });
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const isEditMode = !!id;

  useEffect(() => {
    if (isEditMode) {
      fetchLSI();
    }
  }, [id]);

  const fetchLSI = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/lsi/${id}`);
      setLsi(response.data);
      setError(null);
    } catch (err) {
      setError('Ошибка при загрузке данных: ' + err.message);
      console.error('Ошибка при загрузке ЛСИ:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLsi(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!lsi.name.trim() || !lsi.itemID.trim()) {
      setValidationErrors({ 
        name: !lsi.name.trim() ? 'Название обязательно для заполнения' : '',
        itemID: !lsi.itemID.trim() ? 'ID элемента обязателен для заполнения' : ''
      });
      return;
    }
    
    setIsSubmitting(true);
    setValidationErrors({});
    
    try {
      let response;
      
      if (isEditMode) {
        response = await axios.put(`/api/lsi/${id}`, lsi, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        setSaveStatus({ success: true, message: 'ЛСИ успешно обновлена!' });
      } else {
        response = await axios.post('/api/lsi', lsi, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        resetForm();
        setSaveStatus({ success: true, message: 'ЛСИ успешно создана!' });
      }
      
      setTimeout(() => {
        setSaveStatus(null);
      }, 3000);
    } catch (err) {
      console.error('Ошибка при сохранении ЛСИ:', err);
      
      let errorMessage = 'Ошибка при сохранении ЛСИ';
      
      if (err.response) {
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
      
      const response = await axios.post(`/api/lsi/${id}/send-to-intbus`);
      setSuccessMessage('Данные успешно отправлены в IntBus');
    } catch (err) {
      setError('Ошибка при отправке данных в IntBus: ' + (err.response?.data || err.message));
      console.error('Ошибка при отправке данных в IntBus:', err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setLsi({
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
      unitOfMeasure: ''
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
              <li className="breadcrumb-item"><Link to="/lsi">ЛСИ</Link></li>
              <li className="breadcrumb-item active" aria-current="page">
                {isEditMode ? `Редактирование #${id}` : 'Создание'}
              </li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header bg-primary text-white">
          <h4 className="card-title mb-0">
            {isEditMode ? `Редактирование ЛСИ #${id}` : 'Создание новой ЛСИ'}
          </h4>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger" role="alert">{error}</div>
          )}
          
          {successMessage && (
            <div className="alert alert-success" role="alert">{successMessage}</div>
          )}
          
          {saveStatus && (
            <div className={`alert ${saveStatus.success ? 'alert-success' : 'alert-danger'}`} role="alert">{saveStatus.message}</div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label htmlFor="itemID" className="form-label">ID элемента *</label>
                <input
                  type="text"
                  className={`form-control ${validationErrors.itemID ? 'is-invalid' : ''}`}
                  id="itemID"
                  name="itemID"
                  value={lsi.itemID}
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
                  value={lsi.name}
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
                  value={lsi.componentID}
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
                  value={lsi.type}
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
                  value={lsi.revision}
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
                  value={lsi.lastModifiedUser}
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
                value={lsi.description}
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
                  value={lsi.owner}
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
                  value={lsi.projectList}
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
                  value={lsi.releaseStatus}
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
                  value={lsi.unitOfMeasure}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            
            <div className="d-flex justify-content-between mt-4">
              <div>
                <button type="submit" className="btn btn-primary me-2" disabled={loading || isSubmitting}>
                  {loading ? 'Сохранение...' : isSubmitting ? 'Сохранение...' : 'Сохранить'}
                </button>
                <Link to="/lsi" className="btn btn-secondary">Отмена</Link>
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

export default LSIForm; 