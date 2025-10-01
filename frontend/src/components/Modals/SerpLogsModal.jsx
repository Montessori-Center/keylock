// frontend/src/components/Modals/SerpLogsModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Table, Badge, Alert, Tabs, Tab, Card } from 'react-bootstrap';
import { FaSearch, FaCheckCircle, FaTimesCircle, FaMapMarkerAlt, FaDollarSign } from 'react-icons/fa';

const SerpLogsModal = ({ show, onHide, keywordId = null }) => {
  const [logs, setLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('list');

  useEffect(() => {
    if (show) {
      loadLogs();
    }
  }, [show, keywordId]);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = keywordId 
        ? `/api/dataforseo/serp-logs?keyword_id=${keywordId}`
        : '/api/dataforseo/serp-logs?limit=20';
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setLogs(data.logs || []);
      } else {
        setError(data.error || 'Ошибка загрузки логов');
      }
    } catch (err) {
      console.error('Error loading logs:', err);
      setError('Ошибка подключения к серверу');
    } finally {
      setLoading(false);
    }
  };

  const loadLogDetails = async (logId) => {
    try {
      const response = await fetch(`/api/dataforseo/serp-logs/${logId}`);
      const data = await response.json();
      
      if (data.success) {
        setSelectedLog(data.report);
        setActiveTab('details');
      }
    } catch (err) {
      console.error('Error loading log details:', err);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('ru-RU');
  };

  const renderLogsTable = () => (
    <div className="table-responsive">
      <Table striped hover size="sm">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Ключевое слово</th>
            <th>Результаты</th>
            <th>Флаги</th>
            <th>Интент</th>
            <th>Стоимость</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{formatDate(log.created_at)}</td>
              <td><strong>{log.keyword}</strong></td>
              <td>
                <small>
                  Органика: {log.summary.organic}<br/>
                  Реклама: {log.summary.paid}<br/>
                  Карты: {log.summary.maps}
                </small>
              </td>
              <td>
                {log.flags.has_ads && <Badge bg="warning" className="me-1">Реклама</Badge>}
                {log.flags.has_maps && <Badge bg="info" className="me-1">Карты</Badge>}
                {log.flags.has_our_site && <Badge bg="success" className="me-1">Наш сайт</Badge>}
                {log.flags.has_school_sites && <Badge bg="danger" className="me-1">Школы</Badge>}
              </td>
              <td>
                <Badge bg={log.intent === 'Коммерческий' ? 'success' : 'secondary'}>
                  {log.intent}
                </Badge>
                {log.school_percentage > 0 && (
                  <small className="d-block">{log.school_percentage.toFixed(1)}% школ</small>
                )}
              </td>
              <td>${log.cost.toFixed(4)}</td>
              <td>
                <Button 
                  size="sm" 
                  variant="outline-primary"
                  onClick={() => loadLogDetails(log.id)}
                >
                  Детали
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </div>
  );

  const renderLogDetails = () => {
    if (!selectedLog) return null;

    return (
      <div>
        <Card className="mb-3">
          <Card.Header className="bg-primary text-white">
            <h5>{selectedLog.keyword}</h5>
            <small>{formatDate(selectedLog.created_at)}</small>
          </Card.Header>
          <Card.Body>
            <div className="row">
              <div className="col-md-6">
                <h6>📋 Параметры запроса:</h6>
                <ul className="list-unstyled">
                  <li>📍 Локация: {selectedLog.parameters.location_code}</li>
                  <li>🌐 Язык: {selectedLog.parameters.language_code}</li>
                  <li>💻 Устройство: {selectedLog.parameters.device}</li>
                  <li>📊 Глубина: ТОП-{selectedLog.parameters.depth}</li>
                </ul>
              </div>
              <div className="col-md-6">
                <h6>✅ Результаты анализа:</h6>
                <ul className="list-unstyled">
                  <li>
                    {selectedLog.analysis_result.has_ads ? 
                      <FaCheckCircle className="text-success" /> : 
                      <FaTimesCircle className="text-danger" />
                    } Реклама
                  </li>
                  <li>
                    {selectedLog.analysis_result.has_maps ? 
                      <FaCheckCircle className="text-success" /> : 
                      <FaTimesCircle className="text-danger" />
                    } Google Maps
                  </li>
                  <li>
                    {selectedLog.analysis_result.has_our_site ? 
                      <FaCheckCircle className="text-success" /> : 
                      <FaTimesCircle className="text-danger" />
                    } Наш сайт
                  </li>
                  <li>
                    {selectedLog.analysis_result.has_school_sites ? 
                      <FaCheckCircle className="text-success" /> : 
                      <FaTimesCircle className="text-danger" />
                    } Сайты школ ({selectedLog.analysis_result.school_percentage.toFixed(1)}%)
                  </li>
                  <li>
                    <strong>Интент:</strong> 
                    <Badge bg={selectedLog.analysis_result.intent_type === 'Коммерческий' ? 'success' : 'info'} className="ms-2">
                      {selectedLog.analysis_result.intent_type}
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
                  <th width="50">#</th>
                  <th width="200">Домен</th>
                  <th>Заголовок</th>
                </tr>
              </thead>
              <tbody>
                {selectedLog.organic_results && selectedLog.organic_results.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.position}</td>
                    <td>
                      <strong>{item.domain}</strong>
                      {item.domain === 'montessori.ua' && 
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
                      <th>#</th>
                      <th>Домен</th>
                      <th>Заголовок</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedLog.paid_results.map((item, idx) => (
                      <tr key={idx}>
                        <td>{item.position}</td>
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
                💵 Стоимость анализа: ${selectedLog.cost.toFixed(4)}
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
          <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">
            <Tab eventKey="list" title={`📋 Список анализов (${logs.length})`}>
              {logs.length === 0 ? (
                <Alert variant="info">
                  <strong>Нет данных SERP анализа</strong>
                  <br />
                  Выполните SERP анализ для ключевых слов, чтобы увидеть результаты здесь.
                </Alert>
              ) : (
                renderLogsTable()
              )}
            </Tab>
            <Tab eventKey="details" title="📊 Детали">
              {selectedLog ? renderLogDetails() : (
                <Alert variant="info">
                  Выберите анализ из списка для просмотра деталей
                </Alert>
              )}
            </Tab>
          </Tabs>
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