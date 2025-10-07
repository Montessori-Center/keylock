// frontend/src/components/Modals/SerpLogsModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Table, Badge, Alert, Tabs, Tab, Card } from 'react-bootstrap';
import { FaSearch, FaCheckCircle, FaTimesCircle, FaMapMarkerAlt, FaDollarSign, FaTimes } from 'react-icons/fa';
import api from '../../services/api';

const SerpLogsModal = ({ show, onHide, selectedKeywordIds = [] }) => {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('list');
  const [isFiltered, setIsFiltered] = useState(false);

  useEffect(() => {
    if (show) {
      loadLogs();
      
      // Автоматически применяем фильтр если есть выбранные слова
      if (selectedKeywordIds && selectedKeywordIds.length > 0) {
        setIsFiltered(true);
      }
    }
  }, [show]);

  // Применяем фильтр когда загружаются логи или меняется выбор
  useEffect(() => {
    applyFilter();
  }, [logs, isFiltered, selectedKeywordIds]);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getSerpLogs();
      
      if (response.success) {
        setLogs(response.logs || []);
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

  const applyFilter = () => {
    if (isFiltered && selectedKeywordIds && selectedKeywordIds.length > 0) {
      // Фильтруем логи по выбранным keyword_id
      const filtered = logs.filter(log => selectedKeywordIds.includes(log.keyword_id));
      setFilteredLogs(filtered);
      console.log(`🔍 Filtered logs: ${filtered.length} из ${logs.length}`);
    } else {
      // Показываем все логи
      setFilteredLogs(logs);
    }
  };

  const clearFilter = () => {
    setIsFiltered(false);
  };

  const renderLogsTable = () => {
    const displayLogs = filteredLogs;

    if (displayLogs.length === 0) {
      return (
        <Alert variant="info">
          {isFiltered ? 
            'Нет SERP анализов для выбранных ключевых слов' : 
            'Нет данных SERP анализа'
          }
        </Alert>
      );
    }

    return (
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        <Table striped hover size="sm">
          <thead className="sticky-top bg-white">
            <tr>
              <th width="50">#</th>
              <th>Ключевое слово</th>
              <th>Дата</th>
              <th width="80">Реклама</th>
              <th width="80">Карты</th>
              <th width="100">Наш сайт</th>
              <th width="120">Позиции</th>
              <th width="120">Интент</th>
              <th width="80">Стоимость</th>
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
                  {isFiltered && selectedKeywordIds.includes(log.keyword_id) && (
                    <Badge bg="primary" className="ms-1">Выбрано</Badge>
                  )}
                </td>
                <td>{new Date(log.created_at).toLocaleString('ru-RU')}</td>
                <td className="text-center">
                  {log.analysis_result?.has_ads ? 
                    <FaCheckCircle className="text-danger" /> : 
                    <FaTimesCircle className="text-muted" />
                  }
                </td>
                <td className="text-center">
                  {log.analysis_result?.has_google_maps ? 
                    <FaMapMarkerAlt className="text-primary" /> : 
                    <FaTimesCircle className="text-muted" />
                  }
                </td>
                <td className="text-center">
                  {log.analysis_result?.has_our_site ? 
                    <Badge bg="success">Есть</Badge> : 
                    <Badge bg="secondary">Нет</Badge>
                  }
                </td>
                <td>
                  {log.analysis_result?.has_our_site ? (
                    <small>
                      Орг: <strong>{log.analysis_result.our_organic_position || 'N/A'}</strong>
                      <br />
                      Факт: <strong>{log.analysis_result.our_actual_position || 'N/A'}</strong>
                    </small>
                  ) : (
                    <small className="text-muted">-</small>
                  )}
                </td>
                <td>
                  <Badge bg={log.analysis_result?.intent_type === 'Коммерческий' ? 'success' : 'info'}>
                    {log.analysis_result?.intent_type || 'N/A'}
                  </Badge>
                </td>
                <td className="text-end">
                  <small>${log.cost?.toFixed(4)}</small>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
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

    return (
      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
        <Card className="mb-3">
          <Card.Body>
            <h5>📊 Результаты анализа</h5>
            <div className="mb-3">
              <strong>Ключевое слово:</strong> {selectedLog.keyword_text}
              <br />
              <strong>Дата анализа:</strong> {new Date(selectedLog.created_at).toLocaleString('ru-RU')}
            </div>

            <div className="mb-3">
              <h6>🎯 Основные показатели:</h6>
              <ul>
                <li>
                  {selectedLog.analysis_result.has_ads ? 
                    <FaCheckCircle className="text-danger" /> : 
                    <FaTimesCircle className="text-muted" />
                  } Реклама ({selectedLog.analysis_result.paid_count || 0})
                </li>
                <li>
                  {selectedLog.analysis_result.has_google_maps ? 
                    <FaMapMarkerAlt className="text-primary" /> : 
                    <FaTimesCircle className="text-muted" />
                  } Google Maps
                </li>
                <li>
                  {selectedLog.analysis_result.has_our_site ? 
                    <FaCheckCircle className="text-success" /> : 
                    <FaTimesCircle className="text-danger" />
                  } Наш сайт
                  {selectedLog.analysis_result.has_our_site && (
                    <span className="ms-2">
                      <Badge bg="info">Орг: {selectedLog.analysis_result.our_organic_position}</Badge>
                      {' '}
                      <Badge bg="primary">Факт: {selectedLog.analysis_result.our_actual_position}</Badge>
                    </span>
                  )}
                </li>
                <li>
                  {selectedLog.analysis_result.has_school_sites ? 
                    <FaCheckCircle className="text-warning" /> : 
                    <FaTimesCircle className="text-muted" />
                  } Сайты школ ({selectedLog.analysis_result.school_percentage?.toFixed(1)}%)
                </li>
                <li>
                  <strong>Интент:</strong> 
                  <Badge bg={selectedLog.analysis_result.intent_type === 'Коммерческий' ? 'success' : 'info'} className="ms-2">
                    {selectedLog.analysis_result.intent_type}
                  </Badge>
                </li>
              </ul>
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
                {selectedLog.organic_results && selectedLog.organic_results.map((item, idx) => (
                  <tr key={idx}>
                    <td className="text-center">
                      <Badge bg="secondary">{item.organic_position}</Badge>
                    </td>
                    <td className="text-center">
                      <Badge bg="primary">{item.actual_position}</Badge>
                    </td>
                    <td>
                      <strong>{item.domain}</strong>
                      {item.domain === selectedLog.our_domain && 
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

            <div className="mt-3 text-end">
              <small className="text-muted">
                💵 Стоимость анализа: ${selectedLog.cost?.toFixed(4)}
              </small>
            </div>
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
                <span>
                  <strong>Фильтр активен:</strong> Показаны только анализы для {selectedKeywordIds.length} выбранных слов
                </span>
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
        <Button variant="primary" onClick={loadLogs} disabled={loading}>
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