// ===== ПОЛНЫЙ ФАЙЛ App.jsx С ИСПРАВЛЕНИЯМИ =====
// Ниже полная версия файла для замены

import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import KeywordsTable from './components/KeywordsTable';
import SettingsModal from './components/Modals/SettingsModal';
import AddKeywordsModal from './components/Modals/AddKeywordsModal';
import AddNewOutputModal from './components/Modals/AddNewOutputModal';
import ApplySerpModal from './components/Modals/ApplySerpModal';
import SerpLogsModal from './components/Modals/SerpLogsModal';
import ApplyFiltersModal from './components/Modals/ApplyFiltersModal';
import ChangeFieldModal from './components/Modals/ChangeFieldModal';
import TrashModal from './components/Modals/TrashModal';
import SerpProgressModal from './components/Modals/SerpProgressModal';
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
    newChanges: 0
  });
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
  const [showTrash, setShowTrash] = useState(false);
  const [showSerpLogs, setShowSerpLogs] = useState(false);
  const [serpProgress, setSerpProgress] = useState({
    show: false, 
    current: 0, 
    total: 0, 
    currentKeyword: '' 
  });

  // Копирование в буфер обмена
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
    const initializeApp = async () => {
      console.log('🚀 Initializing app...');
      
      try {
        const response = await api.getSettings();
        if (response.success && response.settings.visible_columns) {
          setVisibleColumns(response.settings.visible_columns);
          console.log('✅ Column settings loaded');
        }
      } catch (error) {
        console.error('Error loading column settings:', error);
      }
      
      const loadedCampaigns = await loadCampaigns();
      
      if (loadedCampaigns && loadedCampaigns.length > 0) {
        console.log('📊 Loading stats for campaigns...');
        await loadAdGroupsStats(loadedCampaigns);
      }
    };
    
    initializeApp();
  }, []);
  
  useEffect(() => {
    const savedAdGroupId = localStorage.getItem('selectedAdGroupId');
    if (savedAdGroupId && campaigns.length > 0) {
      for (const campaign of campaigns) {
        const adGroup = campaign.adGroups.find(ag => ag.id === parseInt(savedAdGroupId));
        if (adGroup) {
          console.log(`📌 Restoring selected ad group: ${adGroup.name}`);
          setSelectedAdGroup(adGroup);
          break;
        }
      }
    }
  }, [campaigns]);
  
  useEffect(() => {
    if (selectedAdGroup) {
      console.log(`📋 Loading keywords for: ${selectedAdGroup.name}`);
      setSelectedKeywordIds([]);
      loadKeywords(selectedAdGroup.id);
    }
  }, [selectedAdGroup]);

  const handleSettingsChange = (newSettings) => {
    if (newSettings.visible_columns) {
      console.log('📊 Settings changed, updating columns');
      setVisibleColumns(newSettings.visible_columns);
    }
  };

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
        loadAdGroupsStats();
      }
    } catch (error) {
      toast.error('Ошибка принятия изменений');
    }
  };

  const loadCampaigns = async () => {
    try {
      console.log('🔄 Loading campaigns...');
      
      const response = await api.getCampaigns();
      
      if (response.success && response.data.length > 0) {
        setCampaigns(response.data);
        setSelectedCampaign(response.data[0]);
        console.log('✅ Campaigns loaded');
        return response.data;
      } else {
        console.error('❌ No campaigns found');
        toast.error('Нет доступных кампаний');
        setCampaigns([]);
        setSelectedCampaign(null);
        return [];
      }
    } catch (error) {
      console.error('❌ Error loading campaigns:', error);
      toast.error('Ошибка подключения к серверу');
      setCampaigns([]);
      setSelectedCampaign(null);
      return [];
    }
  };

  const loadKeywords = async (adGroupId) => {
    setLoading(true);
    try {
      const response = await api.getKeywords(adGroupId);
      if (response.success) {
        setKeywords(response.data);
        
        const newChangesCount = response.data.filter(kw => kw.is_new).length;
        
        setKeywordsStats({
          ...response.stats,
          newChanges: newChangesCount
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

    const confirmed = window.confirm(
      `Вы уверены, что хотите отклонить ${keywordsStats.newChanges} новых изменений?`
    );
    
    if (!confirmed) return;

    try {
      const response = await api.rejectChanges(selectedAdGroup.id);
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
        loadAdGroupsStats();
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
        await loadKeywords(selectedAdGroup.id);
        await loadAdGroupsStats();
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
            successMessage = `Скопировано ${response.copied.length} ключевых слов`;
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
            successMessage = `Скопированы данные ${response.copied_data.length} слов`;
          }
          
          const copySuccess = await copyToClipboard(textToCopy);
          
          if (copySuccess) {
            toast.success(successMessage);
          } else {
            toast.warning('Копирование не удалось');
          }
        }
      } else if (action === 'paste') {
        if (!copiedData) {
          toast.warning('Нет скопированных данных');
          return;
        }
        
        let pasteDataArray;
        if (copiedData.type === 'keywords') {
          pasteDataArray = copiedData.data;
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
        }
        
        const response = await api.pasteKeywords(
          selectedAdGroup.id,
          pasteDataArray,
          copiedData.type
        );
        if (response.success) {
          toast.success(response.message);
          await loadKeywords(selectedAdGroup.id);
          await loadAdGroupsStats();
        }
      } else if (action === 'change_field') {
        setShowChangeField(true);
      } else if (action === 'delete') {
        const confirmed = window.confirm(
          `Вы уверены, что хотите удалить ${selectedKeywordIds.length} слов?`
        );
        if (!confirmed) return;
        
        const response = await api.bulkAction(action, selectedKeywordIds);
        if (response.success) {
          toast.success(response.message);
          await loadKeywords(selectedAdGroup.id);
          await loadAdGroupsStats();
          setSelectedKeywordIds([]);
        }
      } else {
        const response = await api.bulkAction(action, selectedKeywordIds);
        if (response.success) {
          toast.success(response.message);
          await loadKeywords(selectedAdGroup.id);
        }
      }
    } catch (error) {
      console.error('Bulk action error:', error);
      toast.error('Ошибка выполнения действия');
    }
  };

  const loadAdGroupsStats = async (campaignsData = null) => {
    try {
      const campaignsToUse = campaignsData || campaigns;
      
      if (!campaignsToUse || campaignsToUse.length === 0) {
        return;
      }

      const adGroupsWithStats = await Promise.all(
        campaignsToUse[0]?.adGroups?.map(async (adGroup) => {
          try {
            const response = await api.getKeywords(adGroup.id);
            
            const newChangesCount = response.success 
              ? response.data.filter(kw => kw.is_new === true).length 
              : 0;
            
            const uniqueColors = response.success
              ? [...new Set(response.data
                  .filter(kw => kw.is_new === true && kw.batch_color)
                  .map(kw => kw.batch_color))]
              : [];
            
            return {
              ...adGroup,
              newChanges: newChangesCount,
              batchColors: uniqueColors,
              hasChanges: newChangesCount > 0
            };
          } catch (error) {
            return { 
              ...adGroup, 
              newChanges: 0, 
              batchColors: [],
              hasChanges: false 
            };
          }
        }) || []
      );

      const updatedCampaigns = campaignsToUse.map(campaign => ({
        ...campaign,
        adGroups: adGroupsWithStats
      }));
      
      setCampaigns(updatedCampaigns);
      
      if (selectedAdGroup) {
        const updatedSelectedGroup = adGroupsWithStats.find(
          ag => ag.id === selectedAdGroup.id
        );
        if (updatedSelectedGroup) {
          setSelectedAdGroup(updatedSelectedGroup);
        }
      }
      
      return updatedCampaigns;
      
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
        await loadKeywords(selectedAdGroup.id);
        await loadAdGroupsStats();
      } else {
        toast.error(response.error || 'Ошибка получения ключевых слов');
      }
    } catch (error) {
      console.error('Add new output error:', error);
      toast.error('Ошибка получения ключевых слов');
    }
  };

  // ИСПРАВЛЕННАЯ ФУНКЦИЯ
  const handleApplySerp = async (params) => {
      console.log('🎯 handleApplySerp called');
      
      try {
        const keywordIds = params.keyword_ids || selectedKeywordIds;
        
        console.log('   Keywords count:', keywordIds.length);
        
        // Показываем прогресс только для 2+ слов
        if (keywordIds.length > 1) {
          setSerpProgress({
            show: true,
            current: 0,
            total: keywordIds.length,
            currentKeyword: 'Подготовка...'
          });
        }
        
        try {
          const response = await api.applySerp({
            ...params,
            keyword_ids: keywordIds,
            onProgress: (current, total, keyword) => {
              console.log(`📊 Progress: ${current}/${total} - ${keyword}`);
              // Обновляем прогресс только если модалка показана
              if (keywordIds.length > 1) {
                setSerpProgress({
                  show: true,
                  current,
                  total,
                  currentKeyword: keyword || 'Обработка...'
                });
              }
            }
          });
          
          console.log('✅ SERP response:', response);
          
          // Скрываем прогресс
          setSerpProgress(prev => ({ ...prev, show: false }));
          
          if (response.success) {
            toast.success(response.message || 'SERP анализ завершен');
            
            if (response.warning) {
              toast.warning(response.warning);
            }
            
            if (response.errors && response.errors.length > 0) {
              response.errors.slice(0, 3).forEach(err => toast.warning(err));
            }
            
            // Перезагружаем ключевые слова
            if (selectedAdGroup) {
              await loadKeywords(selectedAdGroup.id);
            }
          } else {
            toast.error(response.error || 'Ошибка SERP анализа');
          }
          
        } catch (apiError) {
          console.error('❌ API Error:', apiError);
          setSerpProgress(prev => ({ ...prev, show: false }));
          
          let errorMessage = 'Ошибка применения SERP анализа';
          
          if (apiError.response) {
            console.error('   Response status:', apiError.response.status);
            console.error('   Response data:', apiError.response.data);
            
            errorMessage = apiError.response.data?.error 
              || apiError.response.data?.message
              || `Ошибка сервера (${apiError.response.status})`;
          } else if (apiError.request) {
            errorMessage = 'Нет ответа от сервера';
          } else {
            errorMessage = apiError.message || 'Неизвестная ошибка';
          }
          
          toast.error(errorMessage);
        }
        
      } catch (error) {
        console.error('❌ Unexpected error:', error);
        setSerpProgress(prev => ({ ...prev, show: false }));
        toast.error('Неожиданная ошибка: ' + error.message);
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
              className="btn btn-yellow" 
              onClick={() => setShowSerpLogs(true)}
            >
              📊 SERP Логи
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
              onClick={handleAcceptChanges}
              disabled={!selectedAdGroup || keywordsStats.newChanges === 0}
            >
              Принять изменения {keywordsStats.newChanges > 0 && `(${keywordsStats.newChanges})`}
            </button>
            
            <button 
              className="btn btn-red" 
              onClick={handleRejectChanges}
              disabled={!selectedAdGroup || keywordsStats.newChanges === 0}
            >
              Отклонить изменения {keywordsStats.newChanges > 0 && `(${keywordsStats.newChanges})`}
            </button>
            
            <button 
              className="btn btn-yellow" 
              onClick={() => setShowTrash(true)}
              disabled={!selectedAdGroup}
            >
              Корзина
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
              {keywordsStats.newChanges > 0 && ` | Новых: ${keywordsStats.newChanges}`}
            </div>
          </div>
        </div>
      </div>

      {/* Модальные окна */}
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
      
      {showSerpLogs && (
        <SerpLogsModal
          show={showSerpLogs}
          onHide={() => setShowSerpLogs(false)}
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
      
      <SerpProgressModal 
        show={serpProgress.show}
        current={serpProgress.current}
        total={serpProgress.total}
        currentKeyword={serpProgress.currentKeyword}
      />
      
      {showTrash && (
        <TrashModal
          show={showTrash}
          onHide={() => setShowTrash(false)}
          adGroupId={selectedAdGroup?.id}
          onRestore={() => {
            if (selectedAdGroup) {
              loadKeywords(selectedAdGroup.id);
              loadAdGroupsStats();
            }
          }}
        />
      )}
    </div>
  );
}

export default App;