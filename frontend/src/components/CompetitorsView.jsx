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
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [showChangeFieldModal, setShowChangeFieldModal] = useState(false);
  const [showFiltersModal, setShowFiltersModal] = useState(false);

  useEffect(() => {
    console.log('🚀 CompetitorsView mounted');
    loadCompetitors();
    loadStats();
  }, []);

  const loadCompetitors = async () => {
    setLoading(true);
    try {
      console.log('📞 Calling api.getCompetitors()...');
      const response = await api.getCompetitors();
      console.log('✅ Response:', response);
      
      if (response.success) {
        setCompetitors(response.competitors || []);
        toast.success(`Загружено: ${response.competitors?.length || 0}`);
      } else {
        toast.error('Ошибка загрузки');
      }
    } catch (error) {
      console.error('❌ Error:', error);
      console.error('❌ URL:', error.config?.url);
      toast.error(`Ошибка: ${error.message}`);
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
      console.error('❌ Stats error:', error);
    }
  };

  const handleAdd = async (competitorData) => {
    const response = await api.addCompetitor(competitorData);
    if (response.success) {
      toast.success('Добавлено');
      loadCompetitors();
      loadStats();
    } else {
      throw new Error(response.error || 'Ошибка');
    }
  };

  const handleDataChange = async (id, field, value) => {
    const response = await api.updateCompetitor(id, field, value);
    if (response.success) {
      toast.success('Обновлено');
      loadCompetitors();
    }
  };

  const handleDelete = async () => {
    if (!selectedIds.length) return;
    if (!window.confirm(`Удалить ${selectedIds.length}?`)) return;
    
    const response = await api.deleteCompetitors(selectedIds);
    if (response.success) {
      toast.success(response.message);
      setSelectedIds([]);
      loadCompetitors();
      loadStats();
    }
  };

  const handleCopyDomain = () => {
    if (!selectedIds.length) return;
    const selected = competitors.filter(c => selectedIds.includes(c.id));
    const domains = selected.map(c => c.domain).join('\n');
    navigator.clipboard.writeText(domains);
    toast.success(`Скопировано: ${selectedIds.length}`);
  };

  const handleChangeField = async (field, value) => {
    if (!selectedIds.length) return;
    await Promise.all(selectedIds.map(id => api.updateCompetitor(id, field, value)));
    toast.success(`Обновлено: ${selectedIds.length}`);
    loadCompetitors();
  };

  return (
    <div className="competitors-view">
      <div className="competitors-header">
        <div>
          <h2>Школы-конкуренты</h2>
          {stats && (
            <div className="competitors-stats">
              <div className="stat-item">
                <span className="stat-label">Всего</span>
                <span className="stat-value">{stats.total || 0}</span>
              </div>
            </div>
          )}
        </div>
        <button className="btn btn-secondary" onClick={onClose}>Закрыть</button>
      </div>

      <div style={{ padding: '20px' }}>
        <div className="action-buttons">
          <button className="btn btn-purple" onClick={() => setShowAddModal(true)}>
            Добавить новый сайт
          </button>
        </div>

        <CompetitorsTable
          competitors={competitors}
          loading={loading}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
          onDataChange={handleDataChange}
        />

        <div className="competitors-bulk-actions">
          <button className="btn btn-red" onClick={handleDelete} disabled={!selectedIds.length}>
            Удалить ({selectedIds.length})
          </button>
          <button className="btn btn-blue" onClick={handleCopyDomain} disabled={!selectedIds.length}>
            Копировать
          </button>
          <button className="btn btn-green" onClick={() => setShowChangeFieldModal(true)} disabled={!selectedIds.length}>
            Изменить
          </button>
          <button className="btn btn-dark-blue" onClick={() => setSelectedIds([])} disabled={!selectedIds.length}>
            Снять
          </button>
        </div>
      </div>

      <AddCompetitorModal show={showAddModal} onHide={() => setShowAddModal(false)} onAdd={handleAdd} />
      <ChangeFieldCompetitorModal show={showChangeFieldModal} onHide={() => setShowChangeFieldModal(false)} onSave={handleChangeField} selectedCount={selectedIds.length} />
      <ApplyFiltersModal show={showFiltersModal} onHide={() => setShowFiltersModal(false)} />
    </div>
  );
};

export default CompetitorsView;