import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';
//import 'bootstrap-icons/font/bootstrap-icons.css';
import './App.css';

// Компоненты
import Home from './components/Home';
import NomenclatureList from './components/nomenclature/NomenclatureList';
import NomenclatureForm from './components/nomenclature/NomenclatureForm';
import NomenclatureDelete from './components/nomenclature/NomenclatureDelete';
import LSIList from './components/lsi/LSIList';
import LSIForm from './components/lsi/LSIForm';
import LSIDelete from './components/lsi/LSIDelete';
import ExcelImport from './components/excel/ExcelImport';
import ExcelExport from './components/excel/ExcelExport';

function App() {
  const [nomenclatureCount, setNomenclatureCount] = useState(0);
  const [lsiCount, setLsiCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Загрузка счетчиков
    fetchCounts();
  }, []);

  const fetchCounts = async () => {
    try {
      setLoading(true);
      
      // Параллельные запросы для получения количества записей
      const [nomenclatureResponse, lsiResponse] = await Promise.all([
        axios.get('/api/nomenclature/count'),
        axios.get('/api/lsi/count')
      ]);
      
      setNomenclatureCount(nomenclatureResponse.data);
      setLsiCount(lsiResponse.data);
      setError(null);
    } catch (err) {
      console.error('Ошибка при загрузке счетчиков:', err);
      setError('Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Router>
      <div className="App">
        <header className="bg-dark text-white py-3 mb-4">
          <div className="container">
            <div className="d-flex justify-content-between align-items-center">
              <Link to="/" className="text-white text-decoration-none">
                <h1 className="h3 mb-0">TeamCenter</h1>
              </Link>
              <div>
                <span className="badge bg-primary me-2">
                  <i className="bi bi-database me-1"></i> Номенклатура: {nomenclatureCount}
                </span>
                <span className="badge bg-success">
                  <i className="bi bi-layers me-1"></i> ЛСИ: {lsiCount}
                </span>
              </div>
            </div>
          </div>
        </header>

        <main className="container pb-5">
          {error && (
            <div className="alert alert-danger" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>
              {error}
            </div>
          )}

          <Routes>
            {/* Главная страница */}
            <Route 
              path="/" 
              element={
                <Home 
                  nomenclatureCount={nomenclatureCount} 
                  lsiCount={lsiCount}
                  loading={loading}
                />
              } 
            />
            
            {/* Маршруты для номенклатуры */}
            <Route path="/nomenclature" element={<NomenclatureList />} />
            <Route path="/nomenclature/new" element={<NomenclatureForm />} />
            <Route path="/nomenclature/edit/:id" element={<NomenclatureForm />} />
            <Route path="/nomenclature/delete/:id" element={<NomenclatureDelete />} />
            
            {/* Маршруты для ЛСИ */}
            <Route path="/lsi" element={<LSIList />} />
            <Route path="/lsi/new" element={<LSIForm />} />
            <Route path="/lsi/edit/:id" element={<LSIForm />} />
            <Route path="/lsi/delete/:id" element={<LSIDelete />} />
            
            {/* Маршруты для работы с Excel */}
            <Route path="/excel/import" element={<ExcelImport />} />
            <Route path="/excel/export" element={<ExcelExport />} />
          </Routes>
        </main>

        <footer className="bg-light py-3 text-center text-muted fixed-bottom">
          <div className="container">
            <small>&copy; 2025 TeamCenter. Все права защищены</small>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App; 