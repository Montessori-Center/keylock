// frontend/src/components/Modals/SerpLogsModal.jsx - УЛУЧШЕННАЯ ВЕРСИЯ
import React, { useState, useEffect } from 'react';
import { Modal, Button, Table, Badge, Alert, Tabs, Tab, Card, ButtonGroup } from 'react-bootstrap';
import { FaSearch, FaCheckCircle, FaTimesCircle, FaMapMarkerAlt, FaDollarSign, FaTimes, FaClock, FaHistory } from 'react-icons/fa';
import api from '../../services/api';

const SerpLogsModal = ({ show, onHide, selectedKeywordIds = [] }) => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('list');
  const [isFiltered, setIsFiltered] = useState(false);
  const [historyMode, setHistoryMode] = useState('latest'); // 'latest' или 'all'

  useEffect(() => {
    if (show) {
      // Автоматически применяем фильтр если есть выбранные слова
      if (selectedKeywordIds && selectedKeywordIds.length > 0) {
        setIsFiltered(true);
        setHistoryMode('latest'); // По умолчанию показываем последние
        loadLogsForSelected('latest');
      } else {
        loadAllLogs();
      }
    }
  }, [show]);

  const loadAllLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getSerpLogs({ limit: 50 });
      
      if (response.success) {
        setLogs(response.logs || []);
        setFilteredLogs(response.logs || []);
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

  const loadLogsForSelected = async (mode = 'latest') => {
    if (!selectedKeywordIds || selectedKeywordIds.length === 0) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.getSerpLogs({
        keywordIds: selectedKeywordIds,
        latestOnly: mode === 'latest',
        limit: mode === 'all' ? 200 : 50
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
              
              {/* Реклама */}
              <td className="text-center">
                {log.analysis_result.has_ads ? (
                  <Badge bg="danger">Да ({log.analysis_result.paid_count})</Badge>
                ) : (
                  <Badge bg="secondary">Нет</Badge>
                )}
              </td>
              
              {/* Карты */}
              <td className="text-center">
                {log.analysis_result.has_google_maps ? (
                  <Badge bg="info">
                    <FaMapMarkerAlt /> Да
                  </Badge>
                ) : (
                  <Badge bg="secondary">Нет</Badge>
                )}
              </td>
              
              {/* Наш сайт */}
              <td className="text-center">
                {log.analysis_result.has_our_site ? (
                  <Badge bg="success">
                    <FaCheckCircle /> Да
                  </Badge>
                ) : (
                  <Badge bg="danger">
                    <FaTimesCircle /> Нет
                  </Badge>
                )}
              </td>
              
              {/* Школы */}
              <td className="text-center">
                {log.analysis_result.has_school_sites ? (
                  <Badge bg="warning">
                    Да ({log.analysis_result.school_percentage.toFixed(0)}%)
                  </Badge>
                ) : (
                  <Badge bg="secondary">Нет</Badge>
                )}
              </td>
              
              {/* Интент */}
              <td>
                <Badge bg={log.analysis_result.intent_type === 'Коммерческий' ? 'success' : 'info'}>
                  {log.analysis_result.intent_type}
                </Badge>
              </td>
              
              {/* ИСПРАВЛЕНО: Позиции */}
              <td className="text-center">
                {log.analysis_result.has_our_site ? (
                  <div>
                    <small>
                      Орг: <strong>{log.analysis_result.our_organic_position || 'N/A'}</strong>
                      <br />
                      Факт: <strong>{log.analysis_result.our_actual_position || 'N/A'}</strong>
                    </small>
                  </div>
                ) : (
                  <small className="text-muted">—</small>
                )}
              </td>
              
              {/* Стоимость */}
              <td className="text-right">
                <small>
                  <FaDollarSign />
                  {log.cost.toFixed(4)}
                </small>
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
          Выберите анализ из списка для просмотра деталей
        </Alert>
      );
    }

    const isCommercial = selectedLog.analysis_result.intent_type === 'Коммерческий';

    return (
      <div>
        <Card className="mb-3">
          <Card.Header className="bg-primary text-white">
            <h5 className="mb-0">
              <FaSearch className="me-2" />
              {selectedLog.keyword_text}
            </h5>
          </Card.Header>
          <Card.Body>
            <div className="row">
              <div className="col-md-6">
                <h6>Основная информация:</h6>
                <ul className="list-unstyled">
                  <li>
                    <strong>Дата анализа:</strong> {formatDate(selectedLog.created_at)}
                  </li>
                  <li>
                    <strong>Интент:</strong>{' '}
                    <Badge bg={isCommercial ? 'success' : 'info'} className="ms-2">
                      {selectedLog.analysis_result.intent_type}
                    </Badge>
                  </li>
                  <li>
                    <strong>Стоимость:</strong> ${selectedLog.cost.toFixed(4)}
                  </li>
                </ul>
              </div>
              <div className="col-md-6">
                <h6>Флаги:</h6>
                <ul className="list-unstyled">
                  <li>
                    <strong>Реклама:</strong>{' '}
                    <Badge bg={selectedLog.analysis_result.has_ads ? 'danger' : 'secondary'}>
                      {selectedLog.analysis_result.has_ads ? `Да (${selectedLog.analysis_result.paid_count})` : 'Нет'}
                    </Badge>
                  </li>
                  <li>
                    <strong>Google Maps:</strong>{' '}
                    <Badge bg={selectedLog.analysis_result.has_google_maps ? 'info' : 'secondary'}>
                      {selectedLog.analysis_result.has_google_maps ? 'Да' : 'Нет'}
                    </Badge>
                  </li>
                  <li>
                    <strong>Наш сайт:</strong>{' '}
                    <Badge bg={selectedLog.analysis_result.has_our_site ? 'success' : 'danger'}>
                      {selectedLog.analysis_result.has_our_site ? 'Да' : 'Нет'}
                    </Badge>
                    {selectedLog.analysis_result.has_our_site && (
                      <div className="mt-2">
                        <small>
                          Органическая позиция: <strong>{selectedLog.analysis_result.our_organic_position || 'N/A'}</strong>
                          <br />
                          Фактическая позиция: <strong>{selectedLog.analysis_result.our_actual_position || 'N/A'}</strong>
                        </small>
                      </div>
                    )}
                  </li>
                  <li>
                    <strong>Сайты школ:</strong>{' '}
                    <Badge bg={selectedLog.analysis_result.has_school_sites ? 'warning' : 'secondary'}>
                      {selectedLog.analysis_result.has_school_sites ? 
                        `Да (${selectedLog.analysis_result.school_percentage.toFixed(0)}%)` : 
                        'Нет'
                      }
                    </Badge>
                  </li>
                </ul>
              </div>
            </div>

            <hr />

            <h6>🌐 Органическая выдача:</h6>
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
                {selectedLog.organic_results && selectedLog.organic_results.length > 0 ? (
                  selectedLog.organic_results.map((item, idx) => {
                    // Проверяем, является ли это нашим сайтом
                    const isOurSite = selectedLog.analysis_result.has_our_site && 
                                     item.organic_position === selectedLog.analysis_result.our_organic_position;
                    
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
                  })
                ) : (
                  <tr>
                    <td colSpan="4" className="text-center text-muted">
                      Нет органических результатов
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>

            {selectedLog.paid_results && selectedLog.paid_results.length > 0 && (
              <>
                <hr />
                <h6>💰 Рекламные блоки:</h6>
                <Table size="sm" striped>
                  <thead>
                    <tr>
                      <th width="80">Позиция</th>
                      <th>Домен</th>
                      <th>Заголовок</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedLog.paid_results.map((item, idx) => (
                      <tr key={idx}>
                        <td className="text-center">
                          <Badge bg="danger">{item.position}</Badge>
                        </td>
                        <td>{item.domain}</td>
                        <td><small>{item.title}</small></td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </>
            )}
          </Card.Body>
        </Card>
      </div>
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