import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const ExcelImport = () => {
  const [file, setFile] = useState(null);
  const [importType, setImportType] = useState('nomenclature');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [results, setResults] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setSuccess(null);
    setResults(null);
  };

  const handleTypeChange = (e) => {
    setImportType(e.target.value);
    setError(null);
    setSuccess(null);
    setResults(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Пожалуйста, выберите файл для импорта');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      const response = await axios.post(`/api/excel/import/${importType}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setSuccess(`Файл успешно импортирован. ${response.data.importedCount} записей добавлено.`);
      setResults(response.data);
      setError(null);
    } catch (err) {
      setError('Ошибка при импорте файла: ' + (err.response?.data?.message || err.message));
      console.error('Ошибка при импорте:', err);
      setSuccess(null);
      setResults(null);
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
              <li className="breadcrumb-item active" aria-current="page">Импорт из Excel</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card">
        <div className="card-header bg-primary text-white">
          <h4 className="card-title mb-0">Импорт данных из Excel</h4>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger" role="alert">{error}</div>
          )}
          
          {success && (
            <div className="alert alert-success" role="alert">{success}</div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="importType" className="form-label">Тип данных для импорта</label>
              <select 
                className="form-select" 
                id="importType"
                value={importType}
                onChange={handleTypeChange}
                disabled={loading}
              >
                <option value="nomenclature">Номенклатура</option>
                <option value="lsi">ЛСИ</option>
              </select>
            </div>
            
            <div className="mb-3">
              <label htmlFor="file" className="form-label">Excel-файл</label>
              <input 
                type="file" 
                className="form-control" 
                id="file"
                onChange={handleFileChange}
                accept=".xlsx,.xls"
                disabled={loading}
              />
              <div className="form-text">
                Поддерживаются файлы Excel в форматах .xlsx и .xls
              </div>
            </div>
            
            <div className="d-flex justify-content-between">
              <Link to="/" className="btn btn-secondary">Назад</Link>
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={loading || !file}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Загрузка...
                  </>
                ) : 'Импортировать'}
              </button>
            </div>
          </form>
          
          {results && (
            <div className="mt-4">
              <h5>Результаты импорта</h5>
              <table className="table table-bordered">
                <tbody>
                  <tr>
                    <th>Тип данных</th>
                    <td>{importType === 'nomenclature' ? 'Номенклатура' : 'ЛСИ'}</td>
                  </tr>
                  <tr>
                    <th>Обработано строк</th>
                    <td>{results.totalRows}</td>
                  </tr>
                  <tr>
                    <th>Импортировано записей</th>
                    <td>{results.importedCount}</td>
                  </tr>
                  {results.errors && results.errors.length > 0 && (
                    <tr>
                      <th>Ошибки</th>
                      <td>
                        <ul className="mb-0">
                          {results.errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
              
              <div className="mt-3">
                <Link 
                  to={importType === 'nomenclature' ? '/nomenclature' : '/lsi'} 
                  className="btn btn-success"
                >
                  Перейти к {importType === 'nomenclature' ? 'номенклатуре' : 'ЛСИ'}
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExcelImport; 