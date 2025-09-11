// src/components/Modals/SettingsModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Tab, Tabs, Alert, Row, Col } from 'react-bootstrap';
import api from '../../services/api';

const SettingsModal = ({ show, onHide }) => {
  const [activeTab, setActiveTab] = useState('database');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState({});
  const [currentDbInfo, setCurrentDbInfo] = useState(null);
  const [restarting, setRestarting] = useState(false);
  const [settings, setSettings] = useState({
    // Database settings
    db_host: 'localhost',
    db_port: '3306',
    db_name: 'keyword_lock',
    db_user: 'root',
    db_password: '',
    
    // DataForSeo API settings
    dataforseo_login: '',
    dataforseo_password: '',
    
    // Google Ads API settings (для будущего использования)
    google_ads_client_id: '',
    google_ads_client_secret: '',
    google_ads_refresh_token: '',
    google_ads_developer_token: '',
    google_ads_customer_id: '',
    
    // Display settings
    visible_columns: [
      'keyword', 'criterion_type', 'max_cpc', 'status', 'comment',
      'has_ads', 'has_school_sites', 'has_google_maps', 'has_our_site',
      'intent_type', 'recommendation', 'avg_monthly_searches',
      'three_month_change', 'yearly_change', 'competition',
      'competition_percent', 'min_top_of_page_bid', 'max_top_of_page_bid'
    ]
  });

  // Все доступные колонки
  const allColumns = [
    { key: 'keyword', label: 'Keyword' },
    { key: 'criterion_type', label: 'Criterion Type' },
    { key: 'max_cpc', label: 'Max CPC' },
    { key: 'max_cpm', label: 'Max CPM' },
    { key: 'max_cpv', label: 'Max CPV' },
    { key: 'first_page_bid', label: 'First page bid' },
    { key: 'top_of_page_bid', label: 'Top of page bid' },
    { key: 'first_position_bid', label: 'First position bid' },
    { key: 'quality_score', label: 'Quality score' },
    { key: 'landing_page_experience', label: 'Landing page experience' },
    { key: 'expected_ctr', label: 'Expected CTR' },
    { key: 'ad_relevance', label: 'Ad relevance' },
    { key: 'final_url', label: 'Final URL' },
    { key: 'final_mobile_url', label: 'Final mobile URL' },
    { key: 'tracking_template', label: 'Tracking template' },
    { key: 'final_url_suffix', label: 'Final URL suffix' },
    { key: 'custom_parameters', label: 'Custom parameters' },
    { key: 'status', label: 'Status' },
    { key: 'approval_status', label: 'Approval Status' },
    { key: 'comment', label: 'Comment' },
    { key: 'has_ads', label: 'Есть реклама?' },
    { key: 'has_school_sites', label: 'Есть сайты школ?' },
    { key: 'has_google_maps', label: 'Есть Google карты?' },
    { key: 'has_our_site', label: 'Есть наш сайт?' },
    { key: 'intent_type', label: 'Тип интента' },
    { key: 'recommendation', label: 'Рекомендация' },
    { key: 'avg_monthly_searches', label: 'Среднее число запросов в месяц' },
    { key: 'three_month_change', label: 'Изменение за три месяца' },
    { key: 'yearly_change', label: 'Изменение за год' },
    { key: 'competition', label: 'Конкуренция' },
    { key: 'competition_percent', label: 'Конкуренция, %' },
    { key: 'min_top_of_page_bid', label: 'Ставка для показа вверху стр. (мин.)' },
    { key: 'max_top_of_page_bid', label: 'Ставка для показа вверху стр. (макс.)' },
    { key: 'ad_impression_share', label: 'Ad impression share' },
    { key: 'organic_average_position', label: 'Organic average position' },
    { key: 'organic_impression_share', label: 'Organic impression share' },
    { key: 'labels', label: 'Labels' }
  ];

  // Загрузка настроек при открытии модального окна
  useEffect(() => {
  if (show) {
    loadSettings();
    loadCurrentDbInfo(); // Новая функция
  }
}, [show]);

  const loadSettings = async () => {
  setLoading(true);
  try {
    console.log('Loading settings from /api/settings/get');
    const response = await fetch('/api/settings/get');
    console.log('Settings response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Settings response data:', data);
    
    if (data.success && data.settings) {
      console.log('Updating settings state with:', data.settings);
      setSettings(prev => ({ 
        ...prev, 
        ...data.settings 
      }));
    } else {
      console.warn('No settings found or error:', data.error);
    }
  } catch (error) {
    console.error('Error loading settings:', error);
  } finally {
    setLoading(false);
  }
}
  
  const loadCurrentDbInfo = async () => {
  try {
    const response = await fetch('/api/settings/current-db');
    const data = await response.json();
    if (data.success) {
      setCurrentDbInfo(data.current_db);
    }
  } catch (error) {
    console.error('Error loading current DB info:', error);
  }
};

const handleSave = async () => {
  setSaving(true);
  try {
    const response = await api.saveSettings(settings);
    if (response.success) {
      if (response.requires_restart) {
        // Показываем диалог подтверждения
        const confirmed = window.confirm(response.restart_message);
        
        if (confirmed) {
          setRestarting(true);
          setSaving(false);
          
          // Отправляем запрос на перезапуск
          try {
            await fetch('/api/settings/restart', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' }
            });
            
            // Показываем уведомление о перезапуске
            alert('Перезапуск инициирован...\n\nСтраница перезагрузится через несколько секунд.');
            
            // Ждем и перезагружаем страницу
            setTimeout(() => {
              window.location.reload();
            }, 5000);
            
          } catch (error) {
            setRestarting(false);
            console.error('Restart error:', error);
            alert('Ошибка перезапуска. Перезапустите приложение вручную:\npython3 app.py');
          }
        } else {
          // Пользователь отказался от перезапуска
          alert('Настройки сохранены, но не применены.\nДля применения настроек БД требуется перезапуск.');
          onHide();
        }
      } else {
        // Обычное сохранение без перезапуска
        alert(response.message);
        onHide();
      }
    } else {
      alert('Ошибка сохранения настроек: ' + response.error);
    }
  } catch (error) {
    alert('Ошибка сохранения настроек: ' + error.message);
  } finally {
    if (!restarting) {
      setSaving(false);
    }
  }
};

const testConnection = async (type) => {
  setTestingConnection(true);
  try {
    let response;
    if (type === 'database') {
      response = await fetch('/api/settings/test-db', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: settings.db_host,
          port: settings.db_port,
          name: settings.db_name,
          user: settings.db_user,
          password: settings.db_password
        })
      });
      const data = await response.json();
      setConnectionStatus({
        ...connectionStatus,
        database: data.success ? 'success' : 'error',
        databaseMessage: data.message || 'Неизвестная ошибка'
      });
    } else if (type === 'dataforseo') {
      response = await fetch('/api/settings/test-dataforseo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          login: settings.dataforseo_login,
          password: settings.dataforseo_password
        })
      });
      const data = await response.json();
      setConnectionStatus({
        ...connectionStatus,
        dataforseo: data.success ? 'success' : 'error',
        dataforseMessage: data.message || 'Неизвестная ошибка'
      });
    }
  } catch (error) {
    console.error('Test connection error:', error);
    setConnectionStatus({
      ...connectionStatus,
      [type]: 'error',
      [`${type}Message`]: error.message
    });
  } finally {
    setTestingConnection(false);
  }
};

  const handleColumnToggle = (columnKey) => {
    setSettings(prev => ({
      ...prev,
      visible_columns: prev.visible_columns.includes(columnKey)
        ? prev.visible_columns.filter(col => col !== columnKey)
        : [...prev.visible_columns, columnKey]
    }));
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Настройки приложения</Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ maxHeight: '70vh', overflowY: 'auto' }}>
        {loading ? (
          <div className="text-center">Загрузка настроек...</div>
        ) : (
          <Tabs activeKey={activeTab} onSelect={setActiveTab} className="mb-3">
            
            {/* Вкладка База данных */}
            <Tab eventKey="database" title="База данных">
              <Form>
              {currentDbInfo && (
                  <Alert variant="info" className="mb-3">
                    <strong>Текущее подключение:</strong><br />
                    {currentDbInfo.host}:{currentDbInfo.port}/{currentDbInfo.name} (пользователь: {currentDbInfo.user})
                  </Alert>
                )}
                <Row>
                  <Col md={8}>
                    <Form.Group className="mb-3">
                      <Form.Label>Хост БД:</Form.Label>
                      <Form.Control
                        type="text"
                        value={settings.db_host}
                        onChange={(e) => setSettings(prev => ({ ...prev, db_host: e.target.value }))}
                        placeholder="localhost или IP адрес"
                      />
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>Порт:</Form.Label>
                      <Form.Control
                        type="number"
                        value={settings.db_port}
                        onChange={(e) => setSettings(prev => ({ ...prev, db_port: e.target.value }))}
                        placeholder="3306"
                      />
                    </Form.Group>
                  </Col>
                </Row>
                
                <Form.Group className="mb-3">
                  <Form.Label>Имя базы данных:</Form.Label>
                  <Form.Control
                    type="text"
                    value={settings.db_name}
                    onChange={(e) => setSettings(prev => ({ ...prev, db_name: e.target.value }))}
                    placeholder="keyword_lock"
                  />
                </Form.Group>
                
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Пользователь:</Form.Label>
                      <Form.Control
                        type="text"
                        value={settings.db_user}
                        onChange={(e) => setSettings(prev => ({ ...prev, db_user: e.target.value }))}
                        placeholder="root"
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Пароль:</Form.Label>
                      <Form.Control
                        type="password"
                        value={settings.db_password}
                        onChange={(e) => setSettings(prev => ({ ...prev, db_password: e.target.value }))}
                        placeholder="Пароль БД"
                      />
                    </Form.Group>
                  </Col>
                </Row>
                
                <Button 
                  variant="outline-primary" 
                  onClick={() => testConnection('database')}
                  disabled={testingConnection}
                >
                  {testingConnection ? 'Проверка...' : 'Проверить подключение'}
                </Button>
                
                {connectionStatus.database && (
                  <Alert 
                    variant={connectionStatus.database === 'success' ? 'success' : 'danger'} 
                    className="mt-2"
                  >
                    {connectionStatus.database === 'success' 
                      ? 'Подключение к БД успешно' 
                      : 'Ошибка подключения к БД'
                    }
                  </Alert>
                )}
              </Form>
            </Tab>

            {/* Вкладка DataForSeo API */}
            <Tab eventKey="dataforseo" title="DataForSeo API">
              <Form>
                <Alert variant="info">
                  <strong>DataForSeo API</strong><br />
                  Для получения данных о ключевых словах и SERP анализа
                </Alert>
                
                <Form.Group className="mb-3">
                  <Form.Label>Логин (email):</Form.Label>
                  <Form.Control
                    type="email"
                    value={settings.dataforseo_login}
                    onChange={(e) => setSettings(prev => ({ ...prev, dataforseo_login: e.target.value }))}
                    placeholder="your-email@example.com"
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Пароль:</Form.Label>
                  <Form.Control
                    type="password"
                    value={settings.dataforseo_password}
                    onChange={(e) => setSettings(prev => ({ ...prev, dataforseo_password: e.target.value }))}
                    placeholder="API пароль"
                  />
                  <Form.Text className="text-muted">
                    Пароль из личного кабинета DataForSeo
                  </Form.Text>
                </Form.Group>
                
                <Button 
                  variant="outline-primary" 
                  onClick={() => testConnection('dataforseo')}
                  disabled={testingConnection || !settings.dataforseo_login || !settings.dataforseo_password}
                >
                  {testingConnection ? 'Проверка...' : 'Проверить API и баланс'}
                </Button>
                
                {connectionStatus.dataforseo && (
                  <Alert 
                    variant={connectionStatus.dataforseo === 'success' ? 'success' : 'danger'} 
                    className="mt-2"
                  >
                    {connectionStatus.dataforseo === 'success' 
                      ? 'API работает, аккаунт активен' 
                      : 'Ошибка подключения к API'
                    }
                  </Alert>
                )}
              </Form>
            </Tab>

            {/* Вкладка Google Ads API */}
            <Tab eventKey="googleads" title="Google Ads API">
              <Form>
                <Alert variant="warning">
                  <strong>Google Ads API</strong><br />
                  В разработке. Будет использоваться для экспорта ключевых слов в рекламные кампании.
                </Alert>
                
                <Form.Group className="mb-3">
                  <Form.Label>Client ID:</Form.Label>
                  <Form.Control
                    type="text"
                    value={settings.google_ads_client_id}
                    onChange={(e) => setSettings(prev => ({ ...prev, google_ads_client_id: e.target.value }))}
                    placeholder="Google Ads Client ID"
                    disabled
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Client Secret:</Form.Label>
                  <Form.Control
                    type="password"
                    value={settings.google_ads_client_secret}
                    onChange={(e) => setSettings(prev => ({ ...prev, google_ads_client_secret: e.target.value }))}
                    placeholder="Google Ads Client Secret"
                    disabled
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Developer Token:</Form.Label>
                  <Form.Control
                    type="text"
                    value={settings.google_ads_developer_token}
                    onChange={(e) => setSettings(prev => ({ ...prev, google_ads_developer_token: e.target.value }))}
                    placeholder="Google Ads Developer Token"
                    disabled
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Customer ID:</Form.Label>
                  <Form.Control
                    type="text"
                    value={settings.google_ads_customer_id}
                    onChange={(e) => setSettings(prev => ({ ...prev, google_ads_customer_id: e.target.value }))}
                    placeholder="1234567890"
                    disabled
                  />
                </Form.Group>
              </Form>
            </Tab>

            {/* Вкладка Отображение */}
            <Tab eventKey="display" title="Отображение">
              <Form>
                <Form.Label>Выберите колонки для отображения в таблице:</Form.Label>
                <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #dee2e6', padding: '10px', borderRadius: '4px' }}>
                  {allColumns.map(column => (
                    <Form.Check
                      key={column.key}
                      type="checkbox"
                      id={`column-${column.key}`}
                      label={column.label}
                      checked={settings.visible_columns.includes(column.key)}
                      onChange={() => handleColumnToggle(column.key)}
                      className="mb-2"
                    />
                  ))}
                </div>
                <Form.Text className="text-muted mt-2">
                  Выбрано колонок: {settings.visible_columns.length} из {allColumns.length}
                </Form.Text>
              </Form>
            </Tab>
          </Tabs>
        )}
      </Modal.Body>
      <Modal.Footer>
  {restarting ? (
    <div className="d-flex align-items-center">
      <div className="spinner-border spinner-border-sm me-2" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      <span>Перезапуск приложения...</span>
    </div>
  ) : (
    <>
      <Button variant="secondary" onClick={onHide} disabled={saving}>
        Отмена
      </Button>
      <Button 
        variant="primary" 
        onClick={handleSave}
        disabled={saving || loading}
      >
        {saving ? 'Сохранение...' : 'Сохранить настройки'}
      </Button>
    </>
  )}
</Modal.Footer>
    </Modal>
  );
};

export default SettingsModal;