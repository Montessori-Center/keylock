// frontend/src/App.jsx
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

  // Максимально совместимая функция копирования
  const copyToClipboard = (text) => {
    return new Promise((resolve) => {
      // Создаем input вместо textarea (лучше работает)
      const input = document.createElement('input');
      input.type = 'text';
      input.value = text;
      
      // Стили для скрытия но сохранения функциональности
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
      input.style.fontSize = '16px'; // Предотвращает зум на iOS
      
      document.body.appendChild(input);
      
      // Даем браузеру время добавить элемент
      setTimeout(() => {
        try {
          // Фокусируемся на элементе
          input.focus();
          input.select();
          
          // Дополнительный способ выделения для мобильных
          if (input.setSelectionRange) {
            input.setSelectionRange(0, text.length);
          }
          
          // Выполняем копирование
          const successful = document.execCommand('copy');
          
          // Убираем элемент
          document.body.removeChild(input);
          
          console.log('Copy attempt result:', successful);
          resolve(successful);
          
        } catch (err) {
          console.error('Copy error:', err);
          document.body.removeChild(input);
          resolve(false);
        }
      }, 100); // Небольшая задержка
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
  
  // Обновление колонок когда меняются настройки
  const handleSettingsChange = (newSettings) => {
    if (newSettings.visible_columns) {
      setVisibleColumns(newSettings.visible_columns);
    }
  };

  // Новый обработчик для принятия изменений
  const handleAcceptChanges = async () => {
    if (!selectedAdGroup) {
      toast.warning('Выберите группу объявлений');
      return;
    }

    try {
      const response = await api.acceptChanges(selectedAdGroup.id);
      if (response.success) {
        toast.success(response.message);
        loadKeywords(selectedAdGroup.id);
      }
    } catch (error) {
      toast.error('Ошибка принятия изменений');
    }
  };

  // Load campaigns on mount
  useEffect(() => {
    loadCampaigns();
  }, []);

  // Restore selected ad group from localStorage on mount
  useEffect(() => {
    const savedAdGroupId = localStorage.getItem('selectedAdGroupId');
    if (savedAdGroupId && campaigns.length > 0) {
      // Находим сохраненную группу среди всех кампаний
      for (const campaign of campaigns) {
        const adGroup = campaign.adGroups.find(ag => ag.id === parseInt(savedAdGroupId));
        if (adGroup) {
          setSelectedAdGroup(adGroup);
          break;
        }
      }
    }
  }, [campaigns]);

  // Save selected ad group to localStorage when it changes
  useEffect(() => {
    if (selectedAdGroup) {
      localStorage.setItem('selectedAdGroupId', selectedAdGroup.id.toString());
    }
  }, [selectedAdGroup]);

  // Load keywords when ad group changes
  useEffect(() => {
    if (selectedAdGroup) {
      // Сбрасываем выбор ключевых слов при смене группы
      setSelectedKeywordIds([]);
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
          // Сохраняем для внутренней вставки
          setCopiedData({
            type: action === 'copy' ? 'keywords' : 'full_data',
            data: action === 'copy' ? response.copied : response.copied_data
          });
          
          // Подготавливаем текст для копирования
          let textToCopy = '';
          let successMessage = '';
          
          if (action === 'copy') {
            // Копируем только ключевые слова через запятую
            textToCopy = response.copied.join(', ');
            successMessage = `Скопировано ${response.copied.length} ключевых слов в буфер обмена`;
          } else {
            // Копируем ВСЕ данные из БД, каждое слово - отдельная строка
            // Формат: поля через пробел, слова через запятую
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
            
            // Слова через запятую
            textToCopy = rows.join(', ');
            successMessage = `Скопированы данные ${response.copied_data.length} ключевых слов в буфер обмена`;
          }
          
          // Копируем в буфер обмена асинхронно
          const copySuccess = await copyToClipboard(textToCopy);
          
          if (copySuccess) {
            toast.success(successMessage);
          } else {
            // Показываем текст для ручного копирования
            toast.warning('Копирование не удалось. Данные в консоли для ручного копирования.');
            console.log('=== ДАННЫЕ ДЛЯ КОПИРОВАНИЯ ===');
            console.log(textToCopy);
            console.log('=== КОНЕЦ ДАННЫХ ===');
            
            // Пробуем показать prompt с данными
            if (textToCopy.length < 2000) { // Только для небольших данных
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
          // Для простых ключевых слов - уже массив строк
          pasteDataArray = copiedData.data;
          console.log('Keywords paste data:', pasteDataArray);
        } else if (copiedData.type === 'full_data') {
          // Для полных данных - преобразуем массив объектов в массив строк
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
            <button className="btn btn-orange" onClick={handleAcceptChanges}>
              Принять изменения
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
              visibleColumns={visibleColumns} // Передаем настройки колонок
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
      <SettingsModal 
        show={showSettings} 
        onHide={() => setShowSettings(false)}
        onSettingsChange={handleSettingsChange} // Новый пропс
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