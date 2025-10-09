// frontend/src/components/CompetitorsView.jsx
import React, { useState, useEffect } from 'react';
import CompetitorsTable from './CompetitorsTable';
import AddCompetitorModal from './Modals/AddCompetitorModal';
import ChangeFieldCompetitorModal from './Modals/ChangeFieldCompetitorModal';
import ApplyFiltersModal from './Modals/ApplyFiltersModal';
import api from '../services/api';
import { toast } from 'react-toastify';

const CompetitorsView = ({ onClose }) => {
  const [competitors, setCompetitors] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  
  // Модальные окна
  const [showAddModal, setShowAddModal] = useState(false);
  const [showChangeFieldModal, setShowChangeFieldModal] = useState(false);
  const [showFiltersModal, setShowFiltersModal] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadCompetitors();
    loadStats();
  }, []);

  const loadCompetitors = async () => {
    setLoading(true);
    try {
      const response = await api.getCompetitors();
      if (response.success) {
        setCompetitors(response.competitors || []);
      } else {
        toast.error('Ошибка загрузки конкурентов');
      }
    } catch (error) {
      console.error('Error loading competitors:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.getCompetitorsStats();
      if (response.success) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleAdd = async (competitorData) => {
    try {
      const response = await api.addCompetitor(competitorData);
      if (response.success) {
        toast.success('Конкурент добавлен');
        loadCompetitors();
        loadStats();
      } else {
        throw new Error(response.error || 'Ошибка добавления');
      }
    } catch (error) {
      throw error;
    }
  };

  const handleDataChange = async (id, field, value) => {
    try {
      const response = await api.updateCompetitor(id, field, value);
      
      if (response.success) {
        toast.success('Данные обновлены');
        loadCompetitors();
        loadStats();
      } else {
        toast.error(response.error || 'Ошибка обновления');
      }
    } catch (error) {
      console.error('Error updating competitor:', error);
      toast.error('Ошибка при сохранении');
    }
  };

  const handleDelete = async () => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи для удаления');
      return;
    }

    if (!window.confirm(`Удалить выбранные записи (${selectedIds.length})?`)) {
      return;
    }

    try {
      const response = await api.deleteCompetitors(selectedIds);

      if (response.success) {
        toast.success(response.message);
        setSelectedIds([]);
        loadCompetitors();
        loadStats();
      } else {
        toast.error(response.error || 'Ошибка удаления');
      }
    } catch (error) {
      console.error('Error deleting competitors:', error);
      toast.error('Ошибка при удалении');
    }
  };

  const handleCopyDomain = () => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи');
      return;
    }

    const selectedCompetitors = competitors.filter(c => selectedIds.includes(c.id));
    const domains = selectedCompetitors.map(c => c.domain).join('\n');
    
    navigator.clipboard.writeText(domains).then(() => {
      toast.success(`Скопировано доменов: ${selectedIds.length}`);
    }).catch(err => {
      console.error('Error copying:', err);
      toast.error('Ошибка копирования');
    });
  };

  const handleChangeField = async (field, value) => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи');
      return;
    }

    try {
      const promises = selectedIds.map(id => 
        api.updateCompetitor(id, field, value)
      );

      await Promise.all(promises);
      
      toast.success(`Обновлено записей: ${selectedIds.length}`);
      loadCompetitors();
      loadStats();
    } catch (error) {
      console.error('Error updating field:', error);
      toast.error('Ошибка при обновлении');
    }
  };

  const handleUnselectAll = () => {
    setSelectedIds([]);
  };

  // ✅ НОВАЯ ФУНКЦИЯ: Принять изменения (убрать выделение у новых школ)
  const handleAcceptChanges = async () => {
    if (!stats || stats.newPending === 0) {
      toast.warning('Нет необработанных школ');
      return;
    }

    try {
      const response = await api.acceptCompetitorsChanges();
      if (response.success) {
        toast.success(response.message || 'Изменения приняты');
        loadCompetitors();
        loadStats();
      } else {
        toast.error(response.error || 'Ошибка принятия изменений');
      }
    } catch (error) {
      console.error('Error accepting changes:', error);
      toast.error('Ошибка при принятии изменений');
    }
  };

  return (
    <div className="competitors-view">
      {/* Заголовок */}
      <div className="competitors-header">
        <div>
          <h2>Школы-конкуренты</h2>
        </div>
        <button className="btn btn-secondary" onClick={onClose}>
          Закрыть
        </button>
      </div>

      {/* Контент с правильной структурой */}
      <div className="competitors-content">
        {/* Кнопки действий */}
        <div className="competitors-actions action-buttons">
          <button 
            className="btn btn-purple" 
            onClick={() => setShowAddModal(true)}
          >
            Добавить новый сайт
          </button>
          <button 
            className="btn btn-dark-blue" 
            onClick={() => setShowFiltersModal(true)}
          >
            Применить фильтры
          </button>
          {/* ✅ НОВАЯ КНОПКА: Принять изменения */}
          <button 
              className="btn btn-green" 
              onClick={handleAcceptChanges}
              disabled={!stats || !stats.newPending || stats.newPending === 0}
            >
              Принять изменения {stats && stats.newPending > 0 && `(${stats.newPending})`}
            </button>
        </div>

        {/* Обертка для таблицы */}
        <div className="competitors-table-wrapper">
          <CompetitorsTable
            competitors={competitors}
            loading={loading}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onDataChange={handleDataChange}
          />
        </div>

        {/* ✅ ОБНОВЛЕНО: Массовые действия со статистикой справа (как на основной странице) */}
        <div className="bottom-actions">
          <div className="bulk-actions">
            <span>Массовые действия (выбрано: {selectedIds.length}):</span>
            <button 
              onClick={handleDelete}
              disabled={selectedIds.length === 0}
            >
              Удалить
            </button>
            <button 
              onClick={handleCopyDomain}
              disabled={selectedIds.length === 0}
            >
              Копир. домены
            </button>
            <button 
              onClick={() => setShowChangeFieldModal(true)}
              disabled={selectedIds.length === 0}
            >
              Изменить польз. значение
            </button>
            <button 
              onClick={handleUnselectAll}
              disabled={selectedIds.length === 0}
            >
              Снять выделение
            </button>
          </div>
          
          {/* ✅ НОВОЕ: Статистика справа */}
          <div className="stats">
            Всего: {stats?.total || 0} | 
            Школы: {stats?.schools || 0} | 
            Базы репетиторов: {stats?.tutor_bases || 0} | 
            Не школы: {stats?.not_schools || 0} | 
            Партнёры: {stats?.partners || 0}
            {stats && stats.newPending > 0 && (
              <span className="new-changes"> | Необработано: {stats.newPending}</span>
            )}
          </div>
        </div>
      </div>

      {/* Модальные окна */}
      <AddCompetitorModal
        show={showAddModal}
        onHide={() => setShowAddModal(false)}
        onAdd={handleAdd}
      />

      <ChangeFieldCompetitorModal
        show={showChangeFieldModal}
        onHide={() => setShowChangeFieldModal(false)}
        onSave={handleChangeField}
        selectedCount={selectedIds.length}
      />

      <ApplyFiltersModal
        show={showFiltersModal}
        onHide={() => setShowFiltersModal(false)}
      />
    </div>
  );
};

export default CompetitorsView;
