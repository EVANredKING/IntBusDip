import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const ExcelExport = () => {
  const [exportType, setExportType] = useState('nomenclature');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTypeChange = (e) => {
    setExportType(e.target.value);
    setError(null);
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Выполняем запрос для получения файла
      const response = await axios.get(`/api/excel/export/${exportType}`, {
        responseType: 'blob' // Важно для получения бинарных данных
      });
      
      // Создаем временную ссылку для скачивания файла
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Устанавливаем имя файла из заголовка ответа или используем значение по умолчанию
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${exportType}_export.xlsx`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // Удаляем временную ссылку
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Ошибка при экспорте данных: ' + err.message);
      console.error('Ошибка при экспорте:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Главная</Link></li>
              <li className="breadcrumb-item active" aria-current="page">Экспорт в Excel</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header bg-primary text-white">
          <h4 className="card-title mb-0">Экспорт данных в Excel</h4>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger" role="alert">{error}</div>
          )}
          
          <div className="mb-3">
            <label htmlFor="exportType" className="form-label">Тип данных для экспорта</label>
            <select 
              className="form-select" 
              id="exportType"
              value={exportType}
              onChange={handleTypeChange}
              disabled={loading}
            >
              <option value="nomenclature">Номенклатура</option>
              <option value="lsi">ЛСИ</option>
            </select>
          </div>
          
          <div className="alert alert-info">
            <i className="bi bi-info-circle me-2"></i>
            Данные будут экспортированы в формате Excel (.xlsx). 
            После нажатия на кнопку "Экспортировать" начнется загрузка файла.
          </div>
          
          <div className="d-flex justify-content-between">
            <Link to="/" className="btn btn-secondary">Назад</Link>
            <button 
              onClick={handleExport} 
              className="btn btn-primary" 
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Экспорт...
                </>
              ) : 'Экспортировать'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExcelExport; 