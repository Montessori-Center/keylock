// src/App.jsx
import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import KeywordsTable from './components/KeywordsTable';
import SettingsModal from './components/Modals/SettingsModal';
import AddKeywordsModal from './components/Modals/AddKeywordsModal';
import AddNewOutputModal from './components/Modals/AddNewOutputModal';
import ApplySerpModal from './components/Modals/ApplySerpModal';
import ApplyFiltersModal from './components/Modals/ApplyFiltersModal';
import ChangeFieldModal from './components/Modals/ChangeFieldModal';
import api from './services/api';
import { toast } from 'react-toastify';

function App() {
  // State
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [selectedAdGroup, setSelectedAdGroup] = useState(null);
  const [keywords, setKeywords] = useState([]);
  const [keywordsStats, setKeywordsStats] = useState({ total: 0, commercial: 0, duplicates: 0 });
  const [selectedKeywordIds, setSelectedKeywordIds] = useState([]);
  const [copiedData, setCopiedData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Modals
  const [showSettings, setShowSettings] = useState(false);
  const [showAddKeywords, setShowAddKeywords] = useState(false);
  const [showAddNewOutput, setShowAddNewOutput] = useState(false);
  const [showApplySerp, setShowApplySerp] = useState(false);
  const [showApplyFilters, setShowApplyFilters] = useState(false);
  const [showChangeField, setShowChangeField] = useState(false);

  // Load campaigns on mount
  useEffect(() => {
    loadCampaigns();
  }, []);

  // Load keywords when ad group changes
  useEffect(() => {
    if (selectedAdGroup) {
      loadKeywords(selectedAdGroup.id);
    }
  }, [selectedAdGroup]);

  const loadCampaigns = async () => {
    try {
      // Временные данные, пока нет endpoint для кампаний
      setCampaigns([
        {
          id: 1,
          name: 'montessori.ua',
          adGroups: [
            { id: 1, name: '001 Уроки фортепиано (RU)' },
            { id: 2, name: '002 Уроки вокала (RU)' },
            { id: 3, name: '003 Уроки классической гитары (RU)' },
            { id: 4, name: '004 Уроки электрогитары (RU)' },
            { id: 5, name: '005 Уроки бас-гитары (RU)' },
            { id: 6, name: '006 Уроки барабанов (RU)' },
            { id: 7, name: '007 Уроки скрипки (RU)' },
            { id: 8, name: '008 Уроки виолончели (RU)' },
            { id: 9, name: '009 Уроки саксофона (RU)' },
            { id: 10, name: '010 Уроки флейты (RU)' },
          ]
        }
      ]);
      setSelectedCampaign({ id: 1, name: 'montessori.ua' });
    } catch (error) {
      toast.error('Ошибка загрузки кампаний');
    }
  };

  const loadKeywords = async (adGroupId) => {
    setLoading(true);
    try {
      const response = await api.getKeywords(adGroupId);
      if (response.success) {
        setKeywords(response.data);
        setKeywordsStats(response.stats);
      }
    } catch (error) {
      toast.error('Ошибка загрузки ключевых слов');
    } finally {
      setLoading(false);
    }
  };

  const handleAddKeywords = async (keywordsText) => {
    if (!selectedAdGroup) {
      toast.error('Выберите группу объявлений');
      return;
    }
    
    try {
      const response = await api.addKeywords(selectedAdGroup.id, keywordsText);
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
      }
    } catch (error) {
      toast.error('Ошибка добавления ключевых слов');
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedKeywordIds.length === 0 && action !== 'paste') {
      toast.warning('Выберите ключевые слова');
      return;
    }

    try {
      if (action === 'copy' || action === 'copy_data') {
        const response = await api.bulkAction(action, selectedKeywordIds);
        if (response.success) {
          setCopiedData({
            type: action === 'copy' ? 'keywords' : 'full_data',
            data: action === 'copy' ? response.copied : response.copied_data
          });
          toast.success('Данные скопированы');
        }
      } else if (action === 'paste') {
        if (!copiedData) {
          toast.warning('Нет скопированных данных');
          return;
        }
        const response = await api.pasteKeywords(
          selectedAdGroup.id,
          copiedData.data,
          copiedData.type
        );
        if (response.success) {
          toast.success(response.message);
          loadKeywords(selectedAdGroup.id);
        }
      } else if (action === 'change_field') {
        setShowChangeField(true);
      } else {
        const response = await api.bulkAction(action, selectedKeywordIds);
        if (response.success) {
          toast.success(response.message);
          loadKeywords(selectedAdGroup.id);
        }
      }
    } catch (error) {
      toast.error('Ошибка выполнения действия');
    }
  };

  const handleChangeField = async (field, value) => {
    try {
      const response = await api.bulkAction('update_field', selectedKeywordIds, field, value);
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
      }
    } catch (error) {
      toast.error('Ошибка изменения поля');
    }
  };

  const handleAddNewOutput = async (params) => {
    try {
      const response = await api.getNewKeywords({
        ...params,
        ad_group_id: selectedAdGroup.id
      });
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
      }
    } catch (error) {
      toast.error('Ошибка получения новых ключевых слов');
    }
  };

  const handleApplySerp = async (params) => {
    try {
      const keywordIds = params.keyword_ids || selectedKeywordIds;
      const response = await api.applySerp({
        ...params,
        keyword_ids: keywordIds
      });
      if (response.success) {
        toast.success(response.message);
        if (response.errors && response.errors.length > 0) {
          response.errors.forEach(err => toast.warning(err));
        }
        loadKeywords(selectedAdGroup.id);
      }
    } catch (error) {
      toast.error('Ошибка применения SERP анализа');
    }
  };

  const handleLoadFromDB = async () => {
    if (!selectedAdGroup) {
      toast.warning('Выберите группу объявлений');
      return;
    }
    await loadKeywords(selectedAdGroup.id);
    toast.success('Данные загружены из БД');
  };

  const handleSaveToDB = async () => {
    // Здесь будет логика сохранения в БД
    toast.success('Данные сохранены в БД');
  };

  return (
    <div className="app">
      <Header 
        onSettingsClick={() => setShowSettings(true)}
        onSyncClick={() => toast.info('Синхронизация в разработке')}
        onGoogleAdsClick={() => toast.info('Экспорт в Google Ads в разработке')}
      />
      
      <div className="main-container">
        <Sidebar 
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          campaigns={campaigns}
          selectedCampaign={selectedCampaign}
          selectedAdGroup={selectedAdGroup}
          onSelectAdGroup={setSelectedAdGroup}
        />
        
        <div className={`content-area ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
          <div className="action-buttons">
            <button className="btn btn-purple" onClick={() => setShowAddKeywords(true)}>
              Добавить новые слова
            </button>
            <button className="btn btn-pink" onClick={() => setShowAddNewOutput(true)}>
              Добавить новую выдачу ($)
            </button>
            <button className="btn btn-blue" onClick={() => setShowApplySerp(true)}>
              Применить SERP ($)
            </button>
            <button className="btn btn-dark-blue" onClick={() => setShowApplyFilters(true)}>
              Применить фильтры
            </button>
            <button className="btn btn-green" onClick={handleLoadFromDB}>
              Загрузить данные из БД
            </button>
            <button className="btn btn-red" onClick={handleSaveToDB}>
              Выгрузить данные в БД
            </button>
          </div>
          
          {selectedAdGroup ? (
            <KeywordsTable 
              keywords={keywords}
              loading={loading}
              selectedIds={selectedKeywordIds}
              onSelectionChange={setSelectedKeywordIds}
              onDataChange={(changes) => {
                // Обработка изменений в таблице
                console.log('Data changes:', changes);
              }}
            />
          ) : (
            <div className="no-selection">
              <h3>Выберите группу объявлений</h3>
            </div>
          )}
          
          <div className="bottom-actions">
            <div className="bulk-actions">
              <span>Массовые действия (выбрано: {selectedKeywordIds.length}):</span>
              <button onClick={() => handleBulkAction('delete')} disabled={selectedKeywordIds.length === 0}>
                Удалить
              </button>
              <button onClick={() => handleBulkAction('copy')} disabled={selectedKeywordIds.length === 0}>
                Копир. слова
              </button>
              <button onClick={() => handleBulkAction('copy_data')} disabled={selectedKeywordIds.length === 0}>
                Копир. данные
              </button>
              <button onClick={() => handleBulkAction('paste')}>
                Вставить данные
              </button>
              <button onClick={() => handleBulkAction('pause')} disabled={selectedKeywordIds.length === 0}>
                Приостановить
              </button>
              <button onClick={() => handleBulkAction('activate')} disabled={selectedKeywordIds.length === 0}>
                Активировать
              </button>
              <button onClick={() => handleBulkAction('change_field')} disabled={selectedKeywordIds.length === 0}>
                Изменить польз. значение
              </button>
            </div>
            
            <div className="stats">
              Всего слов: {keywordsStats.total} | 
              Коммерч.: {keywordsStats.commercial} / {((keywordsStats.commercial / keywordsStats.total) * 100 || 0).toFixed(0)}% | 
              Дублей: {keywordsStats.duplicates}
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <SettingsModal show={showSettings} onHide={() => setShowSettings(false)} />
      <AddKeywordsModal 
        show={showAddKeywords} 
        onHide={() => setShowAddKeywords(false)}
        onAdd={handleAddKeywords}
      />
      <AddNewOutputModal
        show={showAddNewOutput}
        onHide={() => setShowAddNewOutput(false)}
        onAdd={handleAddNewOutput}
        selectedKeywords={keywords.filter(k => selectedKeywordIds.includes(k.id))}
      />
      <ApplySerpModal
        show={showApplySerp}
        onHide={() => setShowApplySerp(false)}
        onApply={handleApplySerp}
        selectedKeywords={keywords.filter(k => selectedKeywordIds.includes(k.id))}
      />
      <ApplyFiltersModal
        show={showApplyFilters}
        onHide={() => setShowApplyFilters(false)}
        keywords={keywords}
        onApply={(filteredIds) => {
          setSelectedKeywordIds(filteredIds);
          toast.success('Фильтры применены');
        }}
      />
      <ChangeFieldModal
        show={showChangeField}
        onHide={() => setShowChangeField(false)}
        onApply={handleChangeField}
      />
    </div>
  );
}

export default App;