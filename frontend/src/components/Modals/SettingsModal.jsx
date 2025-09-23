// src/components/Modals/SettingsModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Tab, Tabs, Alert, Row, Col } from 'react-bootstrap';
import api from '../../services/api';

const SettingsModal = ({ show, onHide, onSettingsChange }) => {
  const [activeTab, setActiveTab] = useState('database');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState({});
  const [currentDbInfo, setCurrentDbInfo] = useState(null);
  const [restarting, setRestarting] = useState(false);
  const [campaignSites, setCampaignSites] = useState([]);
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
    loadCurrentDbInfo();
    loadCampaignSites();
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
    // 1. Сохраняем основные настройки
    const response = await api.saveSettings(settings);
    
    // 2. Сохраняем сайты кампаний (если мы на вкладке Бизнес или всегда)
    try {
      await saveCampaignSites();
    } catch (siteError) {
      console.error('Error saving campaign sites:', siteError);
      // Продолжаем даже если не удалось сохранить сайты
    }
    
    if (response.success) {
      // Применяем настройки перед закрытием
      if (onSettingsChange) {
        onSettingsChange(settings);
      }
      
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
        alert(response.message || 'Настройки успешно сохранены!');
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

const handleSiteUrlChange = (campaignId, newUrl) => {
  setCampaignSites(prev => 
    prev.map(campaign => 
      campaign.id === campaignId 
        ? { ...campaign, site_url: newUrl }
        : campaign
    )
  );
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
    const newVisibleColumns = settings.visible_columns.includes(columnKey)
      ? settings.visible_columns.filter(col => col !== columnKey)
      : [...settings.visible_columns, columnKey];
    
    const newSettings = {
      ...settings,
      visible_columns: newVisibleColumns
    };
    
    setSettings(newSettings);
    
    // Мгновенно применяем изменения
    if (onSettingsChange) {
      onSettingsChange({ visible_columns: newVisibleColumns });
    }
};

// 3. Добавьте функцию загрузки сайтов кампаний:
const loadCampaignSites = async () => {
  try {
    const response = await fetch('/api/settings/campaign-sites');
    const data = await response.json();
    
    if (data.success) {
      setCampaignSites(data.campaigns);
    }
  } catch (error) {
    console.error('Error loading campaign sites:', error);
  }
};

// 4. Добавьте функцию сохранения сайтов:
const saveCampaignSites = async () => {
  try {
    const response = await fetch('/api/settings/campaign-sites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaigns: campaignSites })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('✅ Campaign sites saved successfully');
      return true;
    } else {
      console.error('❌ Error saving campaign sites:', data.error);
      // Не показываем alert здесь, чтобы не прерывать основной процесс сохранения
      return false;
    }
  } catch (error) {
    console.error('❌ Network error saving campaign sites:', error);
    // Не показываем alert здесь, чтобы не прерывать основной процесс сохранения
    return false;
  }
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
      Для получения данных о ключевых словах и SERP анализа.
      <br />
      <small>
        API документация: <a href="https://docs.dataforseo.com/" target="_blank" rel="noopener noreferrer">
          https://docs.dataforseo.com/
        </a>
      </small>
    </Alert>
    
    <Form.Group className="mb-3">
      <Form.Label>Логин (email):</Form.Label>
      <Form.Control
        type="email"
        value={settings.dataforseo_login}
        onChange={(e) => setSettings(prev => ({ ...prev, dataforseo_login: e.target.value }))}
        placeholder="your-email@example.com"
      />
      <Form.Text className="text-muted">
        Email от аккаунта DataForSeo
      </Form.Text>
    </Form.Group>
    
    <Form.Group className="mb-3">
      <Form.Label>Пароль API:</Form.Label>
      <Form.Control
        type="password"
        value={settings.dataforseo_password}
        onChange={(e) => setSettings(prev => ({ ...prev, dataforseo_password: e.target.value }))}
        placeholder="API пароль"
        autoComplete="new-password"
      />
      <Form.Text className="text-muted">
        API пароль из личного кабинета DataForSeo (не пароль от аккаунта!)
      </Form.Text>
    </Form.Group>
    
    <div className="d-flex gap-2 mb-3">
      <Button 
        variant="outline-primary" 
        onClick={() => testConnection('dataforseo')}
        disabled={testingConnection || !settings.dataforseo_login || !settings.dataforseo_password}
      >
        {testingConnection ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status"></span>
            Проверка...
          </>
        ) : 'Проверить API и баланс'}
      </Button>
      
      {connectionStatus.dataforseo === 'success' && (
        <Button 
          variant="outline-success" 
          size="sm"
          onClick={() => window.open('https://app.dataforseo.com/', '_blank')}
        >
          Открыть кабинет DataForSeo
        </Button>
      )}
    </div>
    
    {connectionStatus.dataforseo && (
      <Alert 
        variant={connectionStatus.dataforseo === 'success' ? 'success' : 'danger'} 
        className="mb-3"
      >
        <strong>
          {connectionStatus.dataforseo === 'success' ? '✅ Подключение успешно' : '❌ Ошибка подключения'}
        </strong>
        <br />
        {connectionStatus.dataforseMessage || 'Неизвестная ошибка'}
        
        {connectionStatus.dataforseo === 'success' && (
          <div className="mt-2">
            <small>
              💡 <strong>Совет:</strong> Проверяйте баланс перед выполнением платных запросов
            </small>
          </div>
        )}
      </Alert>
    )}
    
    <Alert variant="warning">
      <strong>💰 Внимание:</strong> DataForSeo API - платный сервис
      <br />
      <small>
        • Keywords for Keywords Live: ~$0.05 за запрос<br />
        • SERP анализ: ~$0.01 за ключевое слово<br />
        • Проверяйте баланс перед массовыми операциями
      </small>
    </Alert>
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

<Tab eventKey="display" title="Отображение">
    <Form>
      <Form.Label>Выберите колонки для отображения в таблице:</Form.Label>
      
      <div className="mb-3">
        <Button 
          size="sm" 
          variant="outline-primary" 
          className="me-2"
          onClick={() => {
            const allKeys = allColumns.map(c => c.key);
            setSettings(prev => ({ ...prev, visible_columns: allKeys }));
            if (onSettingsChange) {
              onSettingsChange({ visible_columns: allKeys });
            }
          }}
        >
          Выбрать все
        </Button>
        <Button 
          size="sm" 
          variant="outline-secondary"
          onClick={() => {
            setSettings(prev => ({ ...prev, visible_columns: [] }));
            if (onSettingsChange) {
              onSettingsChange({ visible_columns: [] });
            }
          }}
        >
          Снять все
        </Button>
      </div>
      
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
        <br />
        <small>Изменения применяются сразу, но сохраняются только после нажатия "Сохранить настройки"</small>
      </Form.Text>
    </Form>
  </Tab>
  <Tab eventKey="business" title="Бизнес">
  <Form>
    <Alert variant="info">
      <strong>Настройки сайтов кампаний</strong><br />
      Укажите URL сайта для каждой кампании. Этот URL будет использоваться для определения присутствия вашего сайта в SERP выдаче.
    </Alert>
    
    <Form.Label className="mb-3">Сайты кампаний:</Form.Label>
    
    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
      {campaignSites.length > 0 ? (
        campaignSites.map(campaign => (
          <Row key={campaign.id} className="mb-3 align-items-center">
            <Col md={4}>
              <Form.Label className="mb-0">
                <strong>{campaign.name}</strong>
              </Form.Label>
            </Col>
            <Col md={8}>
              <Form.Control
                type="url"
                value={campaign.site_url || ''}
                onChange={(e) => handleSiteUrlChange(campaign.id, e.target.value)}
                placeholder="https://example.com"
              />
              <Form.Text className="text-muted">
                {campaign.domain && (
                  <small>Домен: {campaign.domain}</small>
                )}
              </Form.Text>
            </Col>
          </Row>
        ))
      ) : (
        <div className="text-center py-3 text-muted">
          Нет доступных кампаний
        </div>
      )}
    </div>
    
    <Alert variant="warning" className="mt-3">
      <small>
        <strong>Важно:</strong> После изменения URL сайта необходимо выполнить SERP анализ заново, чтобы обновить поле "Есть наш сайт?" для ключевых слов.
      </small>
    </Alert>
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