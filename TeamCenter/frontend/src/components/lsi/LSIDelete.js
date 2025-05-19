import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const LSIDelete = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);
  const [lsi, setLsi] = useState(null);

  useEffect(() => {
    fetchLSI();
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

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await axios.delete(`/api/lsi/${id}`);
      navigate('/lsi');
    } catch (err) {
      setError('Ошибка при удалении: ' + err.message);
      console.error('Ошибка при удалении ЛСИ:', err);
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

  return (
    <div className="container">
      <div className="row">
        <div className="col-12">
          <nav aria-label="breadcrumb">
            <ol className="breadcrumb">
              <li className="breadcrumb-item"><Link to="/">Главная</Link></li>
              <li className="breadcrumb-item"><Link to="/lsi">ЛСИ</Link></li>
              <li className="breadcrumb-item active" aria-current="page">Удаление #{id}</li>
            </ol>
          </nav>
        </div>
      </div>

      <div className="card border-danger">
        <div className="card-header bg-danger text-white">
          <h4 className="card-title mb-0">Подтверждение удаления</h4>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger" role="alert">{error}</div>
          )}

          {lsi && (
            <>
              <div className="alert alert-warning">
                <strong>Внимание!</strong> Это действие невозможно отменить. 
                Вы уверены, что хотите удалить эту запись ЛСИ?
              </div>

              <table className="table table-bordered">
                <tbody>
                  <tr>
                    <th style={{ width: '200px' }}>ID</th>
                    <td>{lsi.id}</td>
                  </tr>
                  <tr>
                    <th>Название</th>
                    <td>{lsi.name}</td>
                  </tr>
                  <tr>
                    <th>Описание</th>
                    <td>{lsi.description}</td>
                  </tr>
                </tbody>
              </table>

              <div className="d-flex justify-content-between mt-4">
                <Link to="/lsi" className="btn btn-secondary">
                  Отмена
                </Link>
                <button 
                  className="btn btn-danger" 
                  onClick={handleDelete} 
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
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default LSIDelete; 