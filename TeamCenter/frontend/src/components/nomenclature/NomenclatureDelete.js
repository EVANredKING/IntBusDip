import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const NomenclatureDelete = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [nomenclature, setNomenclature] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchNomenclature();
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

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await axios.delete(`/api/nomenclature/${id}`);
      navigate('/nomenclature');
    } catch (err) {
      setError('Ошибка при удалении: ' + err.message);
      console.error('Ошибка при удалении номенклатуры:', err);
      setDeleting(false);
    }
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

  if (!nomenclature) {
    return <div className="alert alert-warning" role="alert">Номенклатура не найдена</div>;
  }

  return (
    <div>
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Главная</Link></li>
              <li className="breadcrumb-item"><Link to="/nomenclature">Номенклатура</Link></li>
              <li className="breadcrumb-item active" aria-current="page">Удаление</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card mx-auto" style={{ maxWidth: '500px' }}>
        <div className="card-header bg-danger text-white">
          <h4 className="card-title mb-0">Удаление номенклатуры</h4>
        </div>
        <div className="card-body">
          <p>Вы уверены, что хотите удалить номенклатуру:</p>
          
          <div className="alert alert-secondary">
            <p><strong>ID:</strong> {nomenclature.id}</p>
            <p><strong>Краткое название:</strong> {nomenclature.shortName}</p>
            <p><strong>Полное название:</strong> {nomenclature.fullName}</p>
            <p><strong>Шифр:</strong> {nomenclature.cipher}</p>
          </div>
          
          <div className="alert alert-warning">
            <i className="bi bi-exclamation-triangle-fill"></i> Это действие нельзя отменить.
          </div>
          
          <div className="d-flex justify-content-between mt-4">
            <Link to="/nomenclature" className="btn btn-secondary">Отмена</Link>
            <button 
              onClick={handleDelete} 
              className="btn btn-danger" 
              disabled={deleting}
            >
              {deleting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Удаление...
                </>
              ) : 'Удалить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NomenclatureDelete; 