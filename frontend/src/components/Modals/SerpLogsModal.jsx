import React, { useState, useEffect } from 'react';
import { Modal, Button, Alert, Table, Badge, Tabs, Tab, ButtonGroup, Row, Col, Card } from 'react-bootstrap';
import { FaSearch, FaClock, FaHistory, FaTimes } from 'react-icons/fa';
import api from '../../services/api';

const parseRawResponse = (log) => {
  if (!log.raw_response) return null;
  
  try {
    const rawResponse = typeof log.raw_response === 'string' 
      ? JSON.parse(log.raw_response) 
      : log.raw_response;
    
    if (rawResponse.tasks && rawResponse.tasks[0] && rawResponse.tasks[0].result) {
      return rawResponse.tasks[0].result[0].items || [];
    }
  } catch (e) {
    console.error('Error parsing raw_response:', e);
  }
  
  return null;
};

const SerpLogsModal = ({ show, onHide, selectedKeywordIds = null }) => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('list');
  const [selectedLog, setSelectedLog] = useState(null);
  const [isFiltered, setIsFiltered] = useState(false);
  const [historyMode, setHistoryMode] = useState('latest');
  
  // Новый state для вкладок в деталях
  const [detailsTab, setDetailsTab] = useState('full');

  useEffect(() => {
    if (show) {
      if (selectedKeywordIds && selectedKeywordIds.length > 0) {
        setIsFiltered(true);
        loadLogsForSelected('latest');
      } else {
        setIsFiltered(false);
        loadAllLogs();
      }
    }
  }, [show, selectedKeywordIds]);

  const loadAllLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('📊 Loading all SERP logs');
      const response = await api.getSerpLogs({ limit: 50 });
      
      if (response.success) {
        setLogs(response.logs || []);
        setFilteredLogs(response.logs || []);
        console.log(`📊 Loaded ${response.logs.length} logs`);
      } else {
        setError(response.error || 'Ошибка загрузки логов');
      }
    } catch (err) {
      console.error('Error loading SERP logs:', err);
      setError('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadLogsForSelected = async (mode) => {
    setLoading(true);
    setError(null);
    
    try {
      const keywordIdsStr = selectedKeywordIds.join(',');
      const latestOnly = mode === 'latest';
      
      console.log(`📊 Loading logs for selected keywords: ${keywordIdsStr}, mode: ${mode}`);
      
      const response = await api.getSerpLogs({
        keyword_ids: keywordIdsStr,
        latest_only: latestOnly,
        limit: latestOnly ? selectedKeywordIds.length : 200
      });
      
      if (response.success) {
        setLogs(response.logs || []);
        setFilteredLogs(response.logs || []);
        console.log(`📊 Loaded ${response.logs.length} logs for selected keywords (mode: ${mode})`);
      } else {
        setError(response.error || 'Ошибка загрузки логов');
      }
    } catch (err) {
      console.error('Error loading SERP logs:', err);
      setError('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryModeChange = (mode) => {
    setHistoryMode(mode);
    if (isFiltered && selectedKeywordIds && selectedKeywordIds.length > 0) {
      loadLogsForSelected(mode);
    }
  };

  const clearFilter = () => {
    setIsFiltered(false);
    setHistoryMode('latest');
    loadAllLogs();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
  };

  const renderLogsTable = () => {
    const displayLogs = filteredLogs;

    if (displayLogs.length === 0) {
      return (
        <Alert variant="info">
          {isFiltered ? 
            'Нет анализов для выбранных слов' : 
            'Нет данных SERP анализа'}
        </Alert>
      );
    }

    return (
      <Table striped hover size="sm">
        <thead>
          <tr>
            <th width="50">#</th>
            <th width="250">Ключевое слово</th>
            <th width="150">Дата</th>
            <th width="80" className="text-center">Реклама</th>
            <th width="80" className="text-center">Карты</th>
            <th width="100" className="text-center">Наш сайт</th>
            <th width="100" className="text-center">Школы</th>
            <th width="100">Интент</th>
            <th width="100" className="text-center">Позиции</th>
            <th width="80" className="text-right">Стоимость</th>
          </tr>
        </thead>
        <tbody>
          {displayLogs.map((log, idx) => (
            <tr 
              key={log.id}
              onClick={() => {
                setSelectedLog(log);
                setActiveTab('details');
                setDetailsTab('full'); // Сброс на первую вкладку
              }}
              style={{ cursor: 'pointer' }}
            >
              <td>{idx + 1}</td>
              <td>
                <strong>{log.keyword_text}</strong>
                <br />
                <small className="text-muted">ID: {log.keyword_id}</small>
              </td>
              <td><small>{formatDate(log.created_at)}</small></td>
              
              {/* ИСПРАВЛЕНО: Только зелёный/красный */}
              <td className="text-center">
                {log.analysis_result.has_ads ? (
                  <Badge bg="success">Да ({log.analysis_result.paid_count})</Badge>
                ) : (
                  <Badge bg="danger">Нет</Badge>
                )}
              </td>
              
              {/* ИСПРАВЛЕНО: Только зелёный/красный */}
              <td className="text-center">
                {log.analysis_result.has_google_maps ? (
                  <Badge bg="success">Да</Badge>
                ) : (
                  <Badge bg="danger">Нет</Badge>
                )}
              </td>
              
              <td className="text-center">
                {log.analysis_result.has_our_site ? (
                  <Badge bg="success">Да</Badge>
                ) : (
                  <Badge bg="danger">Нет</Badge>
                )}
              </td>
              
              {/* ИСПРАВЛЕНО: Только зелёный/красный */}
              <td className="text-center">
                {log.analysis_result.has_school_sites ? (
                  <Badge bg="success">
                    Да ({log.analysis_result.school_percentage.toFixed(0)}%)
                  </Badge>
                ) : (
                  <Badge bg="danger">Нет</Badge>
                )}
              </td>
              
              <td>
                <Badge bg={log.analysis_result.intent_type === 'Коммерческий' ? 'warning' : 'info'}>
                  {log.analysis_result.intent_type}
                </Badge>
              </td>
              
              <td className="text-center">
                {log.analysis_result.has_our_site ? (
                  <div>
                    <small>
                      <strong>Орг:</strong> {log.analysis_result.our_organic_position || 'N/A'}
                      <br />
                      <strong>Факт:</strong> {log.analysis_result.our_actual_position || 'N/A'}
                    </small>
                  </div>
                ) : (
                  <span className="text-muted">—</span>
                )}
              </td>
              
              <td className="text-right">
                <small>${log.cost.toFixed(4)}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  };

  const renderLogDetails = () => {
    if (!selectedLog) {
      return (
        <Alert variant="info">
          Выберите запись из списка для просмотра деталей
        </Alert>
      );
    }

    return (
      <div>
        <Card className="mb-3">
          <Card.Body>
            <h5>🔍 {selectedLog.keyword_text}</h5>
            <p className="text-muted mb-3">
              <small>
                <strong>Дата анализа:</strong> {formatDate(selectedLog.created_at)}
                <br />
                <strong>Стоимость:</strong> ${selectedLog.cost.toFixed(4)}
              </small>
            </p>

            <div className="mb-3">
              <h6>📊 Статистика:</h6>
              <div className="d-flex flex-wrap gap-2">
                <div>
                  <strong>Всего элементов:</strong> {(() => {
                    // Считаем из raw_response если есть
                    if (selectedLog.raw_response) {
                      try {
                        const raw = typeof selectedLog.raw_response === 'string' 
                          ? JSON.parse(selectedLog.raw_response) 
                          : selectedLog.raw_response;
                        return raw.tasks?.[0]?.result?.[0]?.items?.length || 0;
                      } catch (e) {
                        console.error('Error parsing raw_response:', e);
                      }
                    }
                    // Фолбэк: считаем из массивов
                    return (selectedLog.organic_results?.length || 0) + 
                           (selectedLog.paid_results?.length || 0) + 
                           (selectedLog.analysis_result?.maps_count || 0);
                  })()}
                </div>
                <div>
                  <strong>Органика:</strong> {selectedLog.organic_results?.length || 0}
                </div>
                <div>
                  <strong>Реклама:</strong> {selectedLog.paid_results?.length || 0}
                </div>
                <div>
                  <strong>Карты:</strong> {selectedLog.analysis_result?.maps_count || 0}
                </div>
              </div>
            </div>

            <div className="mb-3">
              <h6>🏷️ Флаги:</h6>
              <div className="d-flex flex-wrap gap-2">
                {/* ИСПРАВЛЕНО: Только зелёный/красный */}
                <Badge bg={selectedLog.analysis_result.has_ads ? 'success' : 'danger'}>
                  Реклама: {selectedLog.analysis_result.has_ads ? 'ДА' : 'НЕТ'}
                </Badge>
                
                <Badge bg={selectedLog.analysis_result.has_google_maps ? 'success' : 'danger'}>
                  Google Maps: {selectedLog.analysis_result.has_google_maps ? 'ДА' : 'НЕТ'}
                </Badge>
                
                <Badge bg={selectedLog.analysis_result.has_our_site ? 'success' : 'danger'}>
                  Наш сайт: {selectedLog.analysis_result.has_our_site ? 'ДА' : 'НЕТ'}
                </Badge>
                
                {selectedLog.analysis_result.has_our_site && (
                  <div className="ms-2">
                    <small>
                      Орг. позиция: <strong>{selectedLog.analysis_result.our_organic_position || 'N/A'}</strong>
                      {' / '}
                      Факт. позиция: <strong>{selectedLog.analysis_result.our_actual_position || 'N/A'}</strong>
                    </small>
                  </div>
                )}
                
                <Badge bg={selectedLog.analysis_result.has_school_sites ? 'success' : 'danger'}>
                  Сайты школ: {selectedLog.analysis_result.has_school_sites ? 
                    `ДА (${selectedLog.analysis_result.school_percentage.toFixed(0)}%)` : 
                    'НЕТ'
                  }
                </Badge>
                
                <Badge bg={selectedLog.analysis_result.intent_type === 'Коммерческий' ? 'warning' : 'info'}>
                  Интент: {selectedLog.analysis_result.intent_type}
                </Badge>
              </div>
            </div>

            <hr />

            {/* НОВОЕ: Вкладки для выдачи */}
            <Tabs 
              activeKey={detailsTab} 
              onSelect={(k) => setDetailsTab(k)} 
              className="mb-3"
            >
              {/* ВКЛАДКА 1: ПОЛНАЯ ВЫДАЧА */}
              <Tab eventKey="full" title="📋 Полная выдача">
                <Alert variant="info" className="mb-3">
                  <small>
                    Все элементы, которые появляются в выдаче Google (реклама, карты, органические результаты и т.д.)
                  </small>
                </Alert>
                
                {renderFullSerp(selectedLog)}
              </Tab>

              {/* ВКЛАДКА 2: ТОЛЬКО ОРГАНИКА */}
              <Tab eventKey="organic" title="🌐 Только органика">
                <Alert variant="info" className="mb-3">
                  <small>
                    Только обычные (органические) результаты поиска без рекламы и других элементов
                  </small>
                </Alert>
                
                {renderOrganicOnly(selectedLog)}
              </Tab>
            </Tabs>

          </Card.Body>
        </Card>
      </div>
    );
  };

// ИСПРАВЛЕННАЯ ФУНКЦИЯ: Полная выдача
const renderFullSerp = (log) => {
  // Собираем все элементы в один массив с типами
  const allItems = [];

  // ====== ДОБАВЛЯЕМ ВСЕ ЭЛЕМЕНТЫ ИЗ RAW RESPONSE ======
  // Парсим raw_response если он есть
  let rawItems = [];
  if (log.raw_response) {
    try {
      const rawResponse = typeof log.raw_response === 'string' 
        ? JSON.parse(log.raw_response) 
        : log.raw_response;
      
      if (rawResponse.tasks && rawResponse.tasks[0] && rawResponse.tasks[0].result) {
        rawItems = rawResponse.tasks[0].result[0].items || [];
      }
    } catch (e) {
      console.error('Error parsing raw_response:', e);
    }
  }

  // Если есть raw items — используем их (полная выдача)
  if (rawItems.length > 0) {
    rawItems.forEach((item, idx) => {
      const itemType = item.type || 'unknown';
      const rankAbsolute = item.rank_absolute || (idx + 1);
      
      // Определяем, является ли это нашим сайтом
      let isOurSite = false;
      if (itemType === 'organic' && log.analysis_result.has_our_site) {
        const organicPos = allItems.filter(i => i.type === 'organic').length + 1;
        isOurSite = organicPos === log.analysis_result.our_organic_position;
      }
      
      allItems.push({
        type: itemType,
        position: rankAbsolute,
        domain: item.domain || null,
        title: item.title || getItemTitle(item, itemType),
        url: item.url || null,
        isOurSite: isOurSite,
        rawItem: item // Сохраняем сырые данные для детальной информации
      });
    });
  } else {
    // Если нет raw_response — используем parsed_items (фолбэк)
    // Добавляем рекламу
    if (log.paid_results && log.paid_results.length > 0) {
      log.paid_results.forEach(item => {
        allItems.push({
          type: 'paid',
          position: item.actual_position || item.position,
          domain: item.domain,
          title: item.title,
          url: item.url
        });
      });
    }

    // Добавляем органические результаты
    if (log.organic_results && log.organic_results.length > 0) {
      log.organic_results.forEach(item => {
        allItems.push({
          type: 'organic',
          position: item.actual_position,
          domain: item.domain,
          title: item.title,
          url: item.url,
          isOurSite: log.analysis_result.has_our_site && 
                     item.organic_position === log.analysis_result.our_organic_position
        });
      });
    }

    // Добавляем карты из parsed_items
    if (log.parsed_items && log.parsed_items.maps) {
      log.parsed_items.maps.forEach(item => {
        allItems.push({
          type: 'map',
          position: item.rank_absolute || 999,
          title: item.title || 'Google Maps'
        });
      });
    }
  }

  // Сортируем по позиции
  allItems.sort((a, b) => a.position - b.position);

  if (allItems.length === 0) {
    return <Alert variant="warning">Нет данных о выдаче</Alert>;
  }

  return (
    <Table size="sm" striped hover>
      <thead>
        <tr>
          <th width="80">Позиция</th>
          <th width="150">Тип</th>
          <th width="200">Домен</th>
          <th>Заголовок</th>
        </tr>
      </thead>
      <tbody>
        {allItems.map((item, idx) => (
          <tr 
            key={idx}
            style={item.isOurSite ? {
              backgroundColor: '#d4edda',
              fontWeight: '500'
            } : {}}
          >
            <td className="text-center">
              <Badge bg="secondary">{item.position}</Badge>
            </td>
            <td>
              {getTypeBadge(item.type)}
            </td>
            <td>
              <strong>{item.domain || '—'}</strong>
              {item.isOurSite && 
                <Badge bg="success" className="ms-2">Наш сайт</Badge>
              }
            </td>
            <td>
              <small>{item.title}</small>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

// Вспомогательная функция для определения заголовка элемента
const getItemTitle = (item, type) => {
  if (item.title) return item.title;
  
  switch (type) {
    case 'people_also_ask':
      return 'Люди также спрашивают';
    case 'featured_snippet':
      return 'Избранный сниппет';
    case 'local_pack':
      return 'Локальные бизнесы'; // ← ИЗМЕНЕНО
    case 'map':
      return 'Google Maps';
    case 'shopping':
      return 'Покупки';
    case 'images':
      return 'Изображения';
    case 'video':
      return 'Видео';
    case 'knowledge_graph':
      return 'График знаний';
    case 'refinement_chips':
      return 'Уточнение поиска';
    case 'related_searches':
      return 'Похожие запросы'; // ← ДОБАВЛЕНО
    default:
      return `[${type}]`;
  }
};

// Вспомогательная функция для Badge типа
const getTypeBadge = (type) => {
  const badges = {
    'paid': <Badge bg="danger">💰 Реклама</Badge>,
    'organic': <Badge bg="primary">🌐 Органика</Badge>,
    'map': <Badge bg="info">🗺️ Google Maps</Badge>,
    'local_pack': <Badge bg="info">📍 Локальные бизнесы</Badge>, // ← ИЗМЕНЕНО
    'people_also_ask': <Badge bg="secondary">❓ Похожие вопросы</Badge>,
    'featured_snippet': <Badge bg="warning">⭐ Сниппет</Badge>,
    'shopping': <Badge bg="success">🛒 Покупки</Badge>,
    'images': <Badge bg="secondary">🖼️ Изображения</Badge>,
    'video': <Badge bg="danger">🎥 Видео</Badge>,
    'knowledge_graph': <Badge bg="dark">📚 График знаний</Badge>,
    'refinement_chips': <Badge bg="light" text="dark">🔍 Уточнение</Badge>,
    'related_searches': <Badge bg="light" text="dark">🔗 Похожие запросы</Badge> // ← ДОБАВЛЕНО
  };

  return badges[type] || <Badge bg="secondary">{type}</Badge>;
};

  // НОВАЯ ФУНКЦИЯ: Только органика
  const renderOrganicOnly = (log) => {
    if (!log.organic_results || log.organic_results.length === 0) {
      return <Alert variant="warning">Нет органических результатов</Alert>;
    }

    return (
      <Table size="sm" striped hover>
        <thead>
          <tr>
            <th width="80">Орг. поз.</th>
            <th width="80">Факт. поз.</th>
            <th width="200">Домен</th>
            <th>Заголовок</th>
          </tr>
        </thead>
        <tbody>
          {log.organic_results.map((item, idx) => {
            const isOurSite = log.analysis_result.has_our_site && 
                             item.organic_position === log.analysis_result.our_organic_position;
            
            return (
              <tr 
                key={idx}
                style={isOurSite ? {
                  backgroundColor: '#d4edda',
                  fontWeight: '500'
                } : {}}
              >
                <td className="text-center">
                  <Badge bg="secondary">{item.organic_position}</Badge>
                </td>
                <td className="text-center">
                  <Badge bg="primary">{item.actual_position}</Badge>
                </td>
                <td>
                  <strong>{item.domain}</strong>
                  {isOurSite && 
                    <Badge bg="success" className="ms-2">Наш сайт</Badge>
                  }
                </td>
                <td>
                  <small>{item.title}</small>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    );
  };

  return (
    <Modal show={show} onHide={onHide} size="xl">
      <Modal.Header closeButton className="bg-light">
        <Modal.Title>
          <FaSearch className="me-2" />
          SERP Анализ - История
          {isFiltered && (
            <Badge bg="primary" className="ms-3">
              Фильтр: {selectedKeywordIds.length} слов
            </Badge>
          )}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        {loading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Загрузка...</span>
            </div>
            <p className="mt-3">Загрузка данных...</p>
          </div>
        ) : error ? (
          <Alert variant="danger">
            <strong>Ошибка:</strong> {error}
          </Alert>
        ) : (
          <>
            {isFiltered && selectedKeywordIds.length > 0 && (
              <Alert variant="info" className="d-flex justify-content-between align-items-center">
                <div>
                  <strong>Фильтр активен:</strong> Показаны анализы для {selectedKeywordIds.length} выбранных слов
                  <div className="mt-2">
                    <ButtonGroup size="sm">
                      <Button 
                        variant={historyMode === 'latest' ? 'primary' : 'outline-primary'}
                        onClick={() => handleHistoryModeChange('latest')}
                      >
                        <FaClock className="me-1" />
                        Только последние
                      </Button>
                      <Button 
                        variant={historyMode === 'all' ? 'primary' : 'outline-primary'}
                        onClick={() => handleHistoryModeChange('all')}
                      >
                        <FaHistory className="me-1" />
                        Вся история
                      </Button>
                    </ButtonGroup>
                  </div>
                </div>
                <Button 
                  variant="outline-secondary" 
                  size="sm" 
                  onClick={clearFilter}
                >
                  <FaTimes className="me-1" />
                  Снять фильтр
                </Button>
              </Alert>
            )}
            
            <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">
              <Tab eventKey="list" title={`📋 Список анализов (${filteredLogs.length})`}>
                {renderLogsTable()}
              </Tab>
              <Tab eventKey="details" title="📊 Детали">
                {renderLogDetails()}
              </Tab>
            </Tabs>
          </>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button 
          variant="primary" 
          onClick={() => {
            if (isFiltered && selectedKeywordIds.length > 0) {
              loadLogsForSelected(historyMode);
            } else {
              loadAllLogs();
            }
          }} 
          disabled={loading}
        >
          🔄 Обновить
        </Button>
        <Button variant="secondary" onClick={onHide}>
          Закрыть
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default SerpLogsModal;