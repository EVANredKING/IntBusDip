import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const NomenclatureList = () => {
  const [nomenclatures, setNomenclatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [processingItems, setProcessingItems] = useState({});

  useEffect(() => {
    fetchNomenclatures();
  }, []);

  const fetchNomenclatures = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/nomenclature');
      setNomenclatures(response.data);
      setError(null);
    } catch (err) {
      setError('Ошибка при загрузке данных: ' + err.message);
      console.error('Ошибка при загрузке номенклатуры:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSendToIntBus = async (id) => {
    try {
      setProcessingItems(prev => ({ ...prev, [id]: true }));
      setSuccessMessage(null);
      setError(null);
      
      // Получение CSRF-токена из cookies
      const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('XSRF-TOKEN='))
        ?.split('=')[1];
      
      // Настройка заголовков с CSRF-токеном
      const headers = {
        'Content-Type': 'application/json',
        'X-XSRF-TOKEN': csrfToken || '',
        'X-Requested-With': 'XMLHttpRequest'
      };
      
      console.log('Отправка с заголовками:', headers);
      
      const response = await axios.post(`/api/nomenclature/sync/${id}`, {}, { 
        headers,
        withCredentials: true 
      });
      
      setSuccessMessage(`Данные номенклатуры #${id} успешно отправлены в IntBus`);
      
      setTimeout(() => {
        setSuccessMessage(null);
      }, 3000);
    } catch (err) {
      console.error('Детали ошибки:', {
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
        stack: err.stack
      });
      
      let errorMessage = 'Ошибка при отправке данных в IntBus';
      
      if (err.response?.data) {
        if (typeof err.response.data === 'object') {
          errorMessage += ': ' + JSON.stringify(err.response.data);
        } else {
          errorMessage += ': ' + err.response.data;
        }
      } else if (err.message) {
        errorMessage += ': ' + err.message;
      }
      
      setError(errorMessage);
    } finally {
      setProcessingItems(prev => ({ ...prev, [id]: false }));
    }
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
  };

  if (loading) {
    return <div className="d-flex justify-content-center mt-5">
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Загрузка...</span>
      </div>
    </div>;
  }

  if (error) {
    return <div className="alert alert-danger" role="alert">{error}</div>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Список номенклатуры</h2>
        <div>
          <Link to="/nomenclature/new" className="btn btn-success me-2">
            <i className="bi bi-plus-circle"></i> Добавить новую
          </Link>
          <a href="/api/excel/export" className="btn btn-primary">
            <i className="bi bi-file-excel"></i> Экспорт в Excel
          </a>
        </div>
      </div>
      
      {successMessage && (
        <div className="alert alert-success alert-dismissible fade show" role="alert">
          {successMessage}
          <button type="button" className="btn-close" onClick={() => setSuccessMessage(null)} aria-label="Close"></button>
        </div>
      )}

      {nomenclatures.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-striped table-hover">
            <thead className="table-primary">
              <tr>
                <th>ID</th>
                <th>Номенклатура</th>
                <th>Название</th>
                <th>Тип</th>
                <th>Ревизия</th>
                <th>Создано</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {nomenclatures.map(item => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.itemID || '-'}</td>
                  <td>{item.name}</td>
                  <td>{item.type || '-'}</td>
                  <td>{item.revision || '-'}</td>
                  <td>{formatDate(item.creationDate)}</td>
                  <td>
                    <div className="btn-group" role="group">
                      <Link to={`/nomenclature/edit/${item.id}`} className="btn btn-sm btn-warning">
                        Редактировать
                      </Link>
                      <Link to={`/nomenclature/delete/${item.id}`} className="btn btn-sm btn-danger ms-1">
                        Удалить
                      </Link>
                      <button 
                        className="btn btn-sm btn-success ms-1" 
                        onClick={() => handleSendToIntBus(item.id)}
                        disabled={processingItems[item.id]}
                      >
                        {processingItems[item.id] ? 
                          <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> : 
                          <i className="fas fa-share-square me-1"></i>
                        }
                        Отправить
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="alert alert-info">
          Номенклатура отсутствует. <Link to="/nomenclature/new">Добавить новую</Link>.
        </div>
      )}
    </div>
  );
};

export default NomenclatureList; 