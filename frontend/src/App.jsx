// frontend/src/App.jsx - ИСПРАВЛЕННАЯ ВЕРСИЯ
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
  const [visibleColumns, setVisibleColumns] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [selectedAdGroup, setSelectedAdGroup] = useState(null);
  const [keywords, setKeywords] = useState([]);
  const [keywordsStats, setKeywordsStats] = useState({ 
    total: 0, 
    commercial: 0, 
    duplicates: 0, 
    newChanges: 0 // ДОБАВЛЕНО: счетчик новых изменений
  });
  const [selectedKeywordIds, setSelectedKeywordIds] = useState([]);
  const [copiedData, setCopiedData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Modals - ИСПРАВЛЕНО: все модальные окна инициализированы
  const [showSettings, setShowSettings] = useState(false);
  const [showAddKeywords, setShowAddKeywords] = useState(false);
  const [showAddNewOutput, setShowAddNewOutput] = useState(false);
  const [showApplySerp, setShowApplySerp] = useState(false);
  const [showApplyFilters, setShowApplyFilters] = useState(false);
  const [showChangeField, setShowChangeField] = useState(false);

  // Максимально совместимая функция копирования
  const copyToClipboard = (text) => {
    return new Promise((resolve) => {
      const input = document.createElement('input');
      input.type = 'text';
      input.value = text;
      
      input.style.position = 'fixed';
      input.style.top = '10px';
      input.style.left = '10px';
      input.style.width = '1px';
      input.style.height = '1px';
      input.style.padding = '0';
      input.style.border = 'none';
      input.style.outline = 'none';
      input.style.boxShadow = 'none';
      input.style.background = 'transparent';
      input.style.fontSize = '16px';
      
      document.body.appendChild(input);
      
      setTimeout(() => {
        try {
          input.focus();
          input.select();
          
          if (input.setSelectionRange) {
            input.setSelectionRange(0, text.length);
          }
          
          const successful = document.execCommand('copy');
          document.body.removeChild(input);
          
          console.log('Copy attempt result:', successful);
          resolve(successful);
          
        } catch (err) {
          console.error('Copy error:', err);
          document.body.removeChild(input);
          resolve(false);
        }
      }, 100);
    });
  };
  
  useEffect(() => {
    loadColumnSettings();
  }, []);

  const loadColumnSettings = async () => {
    try {
      const response = await api.getSettings();
      if (response.success && response.settings.visible_columns) {
        setVisibleColumns(response.settings.visible_columns);
      }
    } catch (error) {
      console.error('Error loading column settings:', error);
    }
  };
  
  const handleSettingsChange = (newSettings) => {
    if (newSettings.visible_columns) {
      setVisibleColumns(newSettings.visible_columns);
    }
  };

  // ИСПРАВЛЕНО: обработчик принятия изменений теперь проверяет наличие изменений
  const handleAcceptChanges = async () => {
      if (!selectedAdGroup) {
        toast.warning('Выберите группу объявлений');
        return;
      }
    
      if (keywordsStats.newChanges === 0) {
        toast.info('Нет новых изменений для принятия');
        return;
      }
    
      try {
        const response = await api.acceptChanges(selectedAdGroup.id);
        if (response.success) {
          toast.success(response.message);
          loadKeywords(selectedAdGroup.id);
          loadAdGroupsStats(); // Обновляем статистику в сайдбаре
        }
      } catch (error) {
        toast.error('Ошибка принятия изменений');
      }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  useEffect(() => {
    const savedAdGroupId = localStorage.getItem('selectedAdGroupId');
    if (savedAdGroupId && campaigns.length > 0) {
      for (const campaign of campaigns) {
        const adGroup = campaign.adGroups.find(ag => ag.id === parseInt(savedAdGroupId));
        if (adGroup) {
          setSelectedAdGroup(adGroup);
          break;
        }
      }
    }
  }, [campaigns]);

  useEffect(() => {
    if (selectedAdGroup) {
      localStorage.setItem('selectedAdGroupId', selectedAdGroup.id.toString());
    }
  }, [selectedAdGroup]);

  useEffect(() => {
    if (selectedAdGroup) {
      setSelectedKeywordIds([]);
      loadKeywords(selectedAdGroup.id);
    }
  }, [selectedAdGroup]);

  const loadCampaigns = async () => {
  try {
    setCampaigns([
      {
        id: 1,
        name: 'montessori.ua',
        adGroups: [
          { id: 1, name: '001 Уроки фортепиано (RU)', newChanges: 0 },
          { id: 2, name: '002 Уроки вокала (RU)', newChanges: 0 },
          { id: 3, name: '003 Уроки классической гитары (RU)', newChanges: 0 },
          { id: 4, name: '004 Уроки электрогитары (RU)', newChanges: 0 },
          { id: 5, name: '005 Уроки бас-гитары (RU)', newChanges: 0 },
          { id: 6, name: '006 Уроки барабанов (RU)', newChanges: 0 },
          { id: 7, name: '007 Уроки скрипки (RU)', newChanges: 0 },
          { id: 8, name: '008 Уроки виолончели (RU)', newChanges: 0 },
          { id: 9, name: '009 Уроки саксофона (RU)', newChanges: 0 },
          { id: 10, name: '010 Уроки флейты (RU)', newChanges: 0 },
        ]
      }
    ]);
    setSelectedCampaign({ id: 1, name: 'montessori.ua' });
    
    // Загружаем статистику после установки кампаний
    setTimeout(() => loadAdGroupsStats(), 500);
    } catch (error) {
      toast.error('Ошибка загрузки кампаний');
    }
    };

  // ИСПРАВЛЕНО: loadKeywords теперь считает новые изменения
  const loadKeywords = async (adGroupId) => {
    setLoading(true);
    try {
      const response = await api.getKeywords(adGroupId);
      if (response.success) {
        setKeywords(response.data);
        
        // ИСПРАВЛЕНО: подсчитываем новые изменения
        const newChangesCount = response.data.filter(keyword => keyword.is_new).length;
        
        setKeywordsStats({
          ...response.stats,
          newChanges: newChangesCount // Добавляем счетчик новых изменений
        });
      }
    } catch (error) {
      toast.error('Ошибка загрузки ключевых слов');
    } finally {
      setLoading(false);
    }
  };
  
  const handleRejectChanges = async () => {
  if (!selectedAdGroup) {
    toast.warning('Выберите группу объявлений');
    return;
  }

  if (keywordsStats.newChanges === 0) {
    toast.info('Нет новых изменений для отклонения');
    return;
  }

  const confirmed = window.confirm(`Вы уверены, что хотите отклонить ${keywordsStats.newChanges} новых изменений? Новые ключевые слова будут удалены.`);
  
  if (!confirmed) return;

  try {
    const response = await api.rejectChanges(selectedAdGroup.id);
    if (response.success) {
      toast.success(response.message);
      loadKeywords(selectedAdGroup.id);
      loadAdGroupsStats(); // Обновляем статистику в сайдбаре
    }
  } catch (error) {
    toast.error('Ошибка отклонения изменений');
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
          
          let textToCopy = '';
          let successMessage = '';
          
          if (action === 'copy') {
            textToCopy = response.copied.join(', ');
            successMessage = `Скопировано ${response.copied.length} ключевых слов в буфер обмена`;
          } else {
            const rows = response.copied_data.map(item => [
              item.keyword || 'None',
              item.criterion_type || 'None',
              item.max_cpc || 'None',
              item.max_cpm || 'None',
              item.status || 'None',
              item.comment || 'None',
              item.has_ads ? 'true' : 'false',
              item.has_school_sites ? 'true' : 'false', 
              item.has_google_maps ? 'true' : 'false',
              item.has_our_site ? 'true' : 'false',
              item.intent_type || 'None',
              item.recommendation || 'None',
              item.avg_monthly_searches || 'None',
              item.three_month_change || 'None',
              item.yearly_change || 'None',
              item.competition || 'None',
              item.competition_percent || 'None',
              item.min_top_of_page_bid || 'None',
              item.max_top_of_page_bid || 'None',
              item.ad_impression_share || 'None',
              item.organic_average_position || 'None',
              item.organic_impression_share || 'None',
              item.labels || 'None'
            ].join(' '));
            
            textToCopy = rows.join(', ');
            successMessage = `Скопированы данные ${response.copied_data.length} ключевых слов в буфер обмена`;
          }
          
          const copySuccess = await copyToClipboard(textToCopy);
          
          if (copySuccess) {
            toast.success(successMessage);
          } else {
            toast.warning('Копирование не удалось. Данные в консоли для ручного копирования.');
            console.log('=== ДАННЫЕ ДЛЯ КОПИРОВАНИЯ ===');
            console.log(textToCopy);
            console.log('=== КОНЕЦ ДАННЫХ ===');
            
            if (textToCopy.length < 2000) {
              setTimeout(() => {
                window.prompt('Скопируйте данные:', textToCopy);
              }, 100);
            }
          }
        }
      } else if (action === 'paste') {
        if (!copiedData) {
          toast.warning('Нет скопированных данных');
          return;
        }
        
        console.log('=== PASTE DEBUG ===');
        console.log('copiedData:', copiedData);
        
        let pasteDataArray;
        if (copiedData.type === 'keywords') {
          pasteDataArray = copiedData.data;
          console.log('Keywords paste data:', pasteDataArray);
        } else if (copiedData.type === 'full_data') {
          pasteDataArray = copiedData.data.map(item => [
            item.keyword || 'None',
            item.criterion_type || 'None',
            item.max_cpc || 'None',
            item.max_cpm || 'None',
            item.status || 'None',
            item.comment || 'None',
            item.has_ads ? 'true' : 'false',
            item.has_school_sites ? 'true' : 'false', 
            item.has_google_maps ? 'true' : 'false',
            item.has_our_site ? 'true' : 'false',
            item.intent_type || 'None',
            item.recommendation || 'None',
            item.avg_monthly_searches || 'None',
            item.three_month_change || 'None',
            item.yearly_change || 'None',
            item.competition || 'None',
            item.competition_percent || 'None',
            item.min_top_of_page_bid || 'None',
            item.max_top_of_page_bid || 'None',
            item.ad_impression_share || 'None',
            item.organic_average_position || 'None',
            item.organic_impression_share || 'None',
            item.labels || 'None'
          ].join(' '));
          console.log('Full data paste array:', pasteDataArray);
        }
        
        console.log('Final paste data array:', pasteDataArray);
        console.log('Array length:', pasteDataArray?.length);
        console.log('=== END PASTE DEBUG ===');
        
        const response = await api.pasteKeywords(
          selectedAdGroup.id,
          pasteDataArray,
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
      console.error('Bulk action error:', error);
      toast.error(`Ошибка выполнения действия: ${error.message || 'Неизвестная ошибка'}`);
    }
  };
  
  const loadAdGroupsStats = async () => {
  try {
    // Получаем статистику новых изменений для каждой группы
    const adGroupsWithStats = await Promise.all(
      campaigns[0]?.adGroups.map(async (adGroup) => {
        try {
          const response = await api.getKeywords(adGroup.id);
          const newChangesCount = response.success 
            ? response.data.filter(keyword => keyword.is_new).length 
            : 0;
          return {
            ...adGroup,
            newChanges: newChangesCount
          };
        } catch (error) {
          console.error(`Error loading stats for ad group ${adGroup.id}:`, error);
          return { ...adGroup, newChanges: 0 };
        }
      }) || []
    );

    // Обновляем кампании с новой статистикой
    setCampaigns([{
      id: 1,
      name: 'montessori.ua',
      adGroups: adGroupsWithStats
    }]);
    } catch (error) {
      console.error('Error loading ad groups stats:', error);
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

  // ИСПРАВЛЕНО: handleAddNewOutput теперь правильно обрабатывает параметры
  const handleAddNewOutput = async (params) => {
    if (!selectedAdGroup) {
      toast.error('Выберите группу объявлений');
      return;
    }

    try {
      const response = await api.getNewKeywords({
        ...params,
        ad_group_id: selectedAdGroup.id
      });
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
      } else {
        toast.error(response.error || 'Ошибка получения новых ключевых слов');
      }
    } catch (error) {
      console.error('Add new output error:', error);
      toast.error('Ошибка получения новых ключевых слов: ' + (error.message || 'Неизвестная ошибка'));
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
          <button 
            className="btn btn-purple" 
            onClick={() => setShowAddKeywords(true)}
            disabled={!selectedAdGroup}
          >
            Добавить новые слова
          </button>
          <button 
            className="btn btn-pink" 
            onClick={() => setShowAddNewOutput(true)}
            disabled={!selectedAdGroup}
          >
            Добавить новую выдачу ($)
          </button>
          <button 
            className="btn btn-blue" 
            onClick={() => setShowApplySerp(true)}
            disabled={!selectedAdGroup || selectedKeywordIds.length === 0}
          >
            Применить SERP ($)
          </button>
          <button 
            className="btn btn-dark-blue" 
            onClick={() => setShowApplyFilters(true)}
            disabled={!selectedAdGroup}
          >
            Применить фильтры
          </button>
          <button 
            className="btn btn-green" 
            onClick={handleLoadFromDB}
            disabled={!selectedAdGroup}
          >
            Загрузить данные из БД
          </button>
          <button 
            className="btn btn-red" 
            onClick={handleSaveToDB}
            disabled={!selectedAdGroup}
          >
            Выгрузить данные в БД
          </button>
          
          <button 
            className="btn btn-orange" 
            onClick={handleAcceptChanges}
            disabled={!selectedAdGroup || keywordsStats.newChanges === 0}
            title={keywordsStats.newChanges > 0 
              ? `Принять ${keywordsStats.newChanges} новых изменений`
              : 'Нет новых изменений'
            }
          >
            Принять изменения {keywordsStats.newChanges > 0 && `(${keywordsStats.newChanges})`}
          </button>
          
          <button 
            className="btn" 
            style={{ backgroundColor: '#dc3545', color: 'white' }}
            onClick={handleRejectChanges}
            disabled={!selectedAdGroup || keywordsStats.newChanges === 0}
            title={keywordsStats.newChanges > 0 
              ? `Отклонить ${keywordsStats.newChanges} новых изменений`
              : 'Нет новых изменений'
            }
          >
            Отклонить изменения {keywordsStats.newChanges > 0 && `(${keywordsStats.newChanges})`}
          </button>
        </div>
          
          {selectedAdGroup ? (
            <KeywordsTable 
              keywords={keywords}
              loading={loading}
              selectedIds={selectedKeywordIds}
              onSelectionChange={setSelectedKeywordIds}
              onDataChange={(changes) => {
                console.log('Data changes:', changes);
              }}
              visibleColumns={visibleColumns}
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
              {/* ДОБАВЛЕНО: показываем новые изменения в статистике */}
              {keywordsStats.newChanges > 0 && ` | Новых: ${keywordsStats.newChanges}`}
            </div>
          </div>
        </div>
      </div>

      {/* ИСПРАВЛЕНО: все модальные окна правильно подключены */}
      <SettingsModal 
        show={showSettings} 
        onHide={() => setShowSettings(false)}
        onSettingsChange={handleSettingsChange}
      />
      
      {showAddKeywords && (
        <AddKeywordsModal
          show={showAddKeywords}
          onHide={() => setShowAddKeywords(false)}
          onAdd={handleAddKeywords}
        />
      )}
      
      {showAddNewOutput && (
        <AddNewOutputModal
          show={showAddNewOutput}
          onHide={() => setShowAddNewOutput(false)}
          onAdd={handleAddNewOutput}
          selectedKeywords={keywords.filter(k => selectedKeywordIds.includes(k.id))}
        />
      )}
      
      {showApplySerp && (
        <ApplySerpModal
          show={showApplySerp}
          onHide={() => setShowApplySerp(false)}
          onApply={handleApplySerp}
          selectedKeywords={keywords.filter(k => selectedKeywordIds.includes(k.id))}
        />
      )}
      
      {showApplyFilters && (
        <ApplyFiltersModal
          show={showApplyFilters}
          onHide={() => setShowApplyFilters(false)}
          keywords={keywords}
          onApply={(filteredIds) => {
            setSelectedKeywordIds(filteredIds);
            toast.success('Фильтры применены');
          }}
        />
      )}
      
      {showChangeField && (
        <ChangeFieldModal
          show={showChangeField}
          onHide={() => setShowChangeField(false)}
          onApply={handleChangeField}
        />
      )}
    </div>
  );
}

export default App;