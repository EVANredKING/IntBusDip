import React from 'react';
import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';

const Home = ({ nomenclatureCount, lsiCount, loading }) => {
  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
        <p className="mt-2">Загрузка данных...</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="mb-4">Добро пожаловать в TeamCenter</h2>
      
      <div className="row">
        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">Номенклатура</h5>
              <p className="card-text">Управление элементами номенклатуры.</p>
              <p>Всего элементов: <span className="badge bg-primary">{nomenclatureCount}</span></p>
              <Link to="/nomenclature" className="btn btn-primary">Перейти</Link>
            </div>
          </div>
        </div>
        
        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">ЛСИ</h5>
              <p className="card-text">Логическая структура изделия.</p>
              <p>Всего элементов: <span className="badge bg-success">{lsiCount}</span></p>
              <Link to="/lsi" className="btn btn-success">Перейти</Link>
            </div>
          </div>
        </div>
        
        <div className="col-md-4 mb-4">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">Импорт/Экспорт</h5>
              <p className="card-text">Работа с Excel-файлами.</p>
              <div className="d-flex gap-2">
                <Link to="/excel/import" className="btn btn-info">Импорт</Link>
                <Link to="/excel/export" className="btn btn-secondary">Экспорт</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;