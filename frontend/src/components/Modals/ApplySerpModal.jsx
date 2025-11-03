// src/components/Modals/ApplySerpModal.jsx  
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Row, Col, Alert } from 'react-bootstrap';

const ApplySerpModal = ({ show, onHide, onApply, selectedKeywords }) => {
  const [params, setParams] = useState({
      keyword_ids: [],
      location_code: '',
      location_name: '',
      language_code: '',
      language_name: '',
      device: 'desktop',
      os: 'windows',
      depth: 20,
      calculate_rectangles: false,
      browser_screen_width: 1920,
      browser_screen_height: 1080,
      se_domain: '',
      skip_analyzed: true
    });

  // Список локаций загружается из БД
  const [locations, setLocations] = useState([]);
  const [languages, setLanguages] = useState([]);

  // Конфигурации устройств
  const deviceConfigs = {
    desktop: {
      os_options: ['windows', 'macos', 'linux'],
      default_width: 1920,
      default_height: 1080
    },
    mobile: {
      os_options: ['android', 'ios'],
      default_width: 360,
      default_height: 640
    },
    tablet: {
      os_options: ['android', 'ios'],
      default_width: 768,
      default_height: 1024
    }
  };
  
  // Загрузка данных при открытии модального окна
  useEffect(() => {
    if (show) {
      loadLocations();
      loadLanguages();
    }
  }, [show]);
  
  // Установка значений по умолчанию после загрузки данных
    useEffect(() => {
      if (locations.length > 0 && !params.location_code) {
        const defaultLocation = locations[0];
        setParams(prev => ({
          ...prev,
          location_code: defaultLocation.code,
          location_name: defaultLocation.name,
          se_domain: defaultLocation.se_domain
        }));
      }
    }, [locations, params.location_code]);
    
    useEffect(() => {
      if (languages.length > 0 && !params.language_code) {
        const defaultLanguage = languages[0];
        setParams(prev => ({
          ...prev,
          language_code: defaultLanguage.code,
          language_name: defaultLanguage.name
        }));
      }
    }, [languages, params.language_code]);

  const loadLocations = async () => {
    try {
      const response = await fetch('/api/dataforseo/locations');
      const data = await response.json();
      
      if (data.success && data.popular) {
        setLocations(data.popular);
      }
    } catch (error) {
      console.error('Error loading locations:', error);
    }
  };

  const loadLanguages = async () => {
    try {
      const response = await fetch('/api/dataforseo/languages');
      const data = await response.json();
      
      if (data.success && data.main) {
        const formattedLanguages = data.main.map(lang => ({
          code: lang.language_code,
          name: lang.language_name
        }));
        setLanguages(formattedLanguages);
      }
    } catch (error) {
      console.error('Error loading languages:', error);
    }
  };

  useEffect(() => {
    if (selectedKeywords && selectedKeywords.length > 0) {
      setParams(prev => ({
        ...prev,
        keyword_ids: selectedKeywords.map(k => k.id)
      }));
    }
  }, [selectedKeywords, show]);

  const handleLocationChange = (locationCode) => {
    const location = locations.find(l => l.code === parseInt(locationCode));
    if (location) {
      setParams(prev => ({
        ...prev,
        location_code: location.code,
        location_name: location.name,
        se_domain: location.se_domain
      }));
    }
  };

  const handleLanguageChange = (languageCode) => {
    const language = languages.find(l => l.code === languageCode);
    if (language) {
      setParams(prev => ({
        ...prev,
        language_code: language.code,
        language_name: language.name
      }));
    }
  };

  const handleDeviceChange = (device) => {
    const config = deviceConfigs[device];
    setParams(prev => ({
      ...prev,
      device: device,
      os: config.os_options[0],
      browser_screen_width: config.default_width,
      browser_screen_height: config.default_height
    }));
  };

  const handleSubmit = () => {
    if (params.keyword_ids.length === 0) {
      alert('Выберите ключевые слова для анализа');
      return;
    }
    
    console.log('Отправляем SERP параметры:', params);
    onApply(params);
    onHide();
  };

  const calculateCost = () => {
    // Базовая стоимость за 1 ключевое слово
    const baseCost = 0.006; // $0.006 за SERP advanced
    const keywordsCount = params.keyword_ids.length;
    const depthMultiplier = params.depth <= 20 ? 1 : params.depth <= 50 ? 1.5 : 2;
    return (baseCost * keywordsCount * depthMultiplier).toFixed(4);
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton className="bg-primary text-white">
        <Modal.Title>
          🔍 SERP анализ выдачи Google
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Alert variant="info">
            <strong>Выбрано ключевых слов: {params.keyword_ids.length}</strong>
            <br />
            <small>Будет проанализирована выдача Google для каждого ключевого слова</small>
          </Alert>
          
          <Row className="mb-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>📍 Локация:</Form.Label>
                <Form.Select 
                  value={params.location_code}
                  onChange={(e) => handleLocationChange(e.target.value)}
                >
                  {locations.map(loc => (
                    <option key={loc.code} value={loc.code}>
                      {loc.name} ({loc.se_domain})
                    </option>
                  ))}
                </Form.Select>
                <Form.Text className="text-muted">
                  Страна для анализа выдачи
                </Form.Text>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group>
                <Form.Label>🌐 Язык интерфейса:</Form.Label>
                <Form.Select 
                  value={params.language_code}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </Form.Select>
                <Form.Text className="text-muted">
                  Язык интерфейса Google
                </Form.Text>
              </Form.Group>
            </Col>
          </Row>

          <Row className="mb-3">
            <Col md={4}>
              <Form.Group>
                <Form.Label>💻 Устройство:</Form.Label>
                <Form.Select 
                  value={params.device}
                  onChange={(e) => handleDeviceChange(e.target.value)}
                >
                  <option value="desktop">Desktop</option>
                  <option value="mobile">Mobile</option>
                  <option value="tablet">Tablet</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={4}>
              <Form.Group>
                <Form.Label>⚙️ ОС:</Form.Label>
                <Form.Select 
                  value={params.os}
                  onChange={(e) => setParams(prev => ({ ...prev, os: e.target.value }))}
                >
                  {deviceConfigs[params.device].os_options.map(os => (
                    <option key={os} value={os}>
                      {os.charAt(0).toUpperCase() + os.slice(1)}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={4}>
              <Form.Group>
                <Form.Label>📊 Глубина выдачи:</Form.Label>
                <Form.Control
                  type="number"
                  value={params.depth}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    depth: Math.min(700, Math.max(1, parseInt(e.target.value) || 10))
                  }))}
                  min="10"
                  max="700"
                />
                <Form.Text className="text-muted">
                  Количество результатов
                </Form.Text>
              </Form.Group>
            </Col>
          </Row>

          <Row className="mb-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>📐 Ширина экрана (px):</Form.Label>
                <Form.Control
                  type="number"
                  value={params.browser_screen_width}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    browser_screen_width: parseInt(e.target.value) || 1920
                  }))}
                  min="320"
                  max="3840"
                />
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group>
                <Form.Label>📏 Высота экрана (px):</Form.Label>
                <Form.Control
                  type="number"
                  value={params.browser_screen_height}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    browser_screen_height: parseInt(e.target.value) || 1080
                  }))}
                  min="240"
                  max="2160"
                />
              </Form.Group>
            </Col>
          </Row>

          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Пропускать проанализированные ключевые слова"
              checked={params.skip_analyzed}
              onChange={(e) => setParams(prev => ({ 
                ...prev, 
                skip_analyzed: e.target.checked 
              }))}
            />
            <Form.Text className="text-muted">
              Слова с уже выполненным SERP-анализом будут пропущены (не войдут в запрос к API)
            </Form.Text>
          </Form.Group>
          
          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Вычислять координаты элементов (calculate_rectangles)"
              checked={params.calculate_rectangles}
              onChange={(e) => setParams(prev => ({ 
                ...prev, 
                calculate_rectangles: e.target.checked 
              }))}
            />
            <Form.Text className="text-muted">
              Добавляет информацию о позиции элементов на странице
            </Form.Text>
          </Form.Group>

          <Alert variant="warning">
            <strong>💰 Стоимость операции:</strong>
            <br />
            • Ключевых слов: {params.keyword_ids.length}
            <br />
            • Глубина: {params.depth} результатов
            <br />
            • Примерная стоимость: <strong>${calculateCost()}</strong>
            <br />
            <small className="text-muted">
              Тариф: $0.006 за SERP advanced (до 20 результатов)
            </small>
          </Alert>

          <Alert variant="info">
            <strong>ℹ️ Что будет проанализировано:</strong>
            <ul className="mb-0">
              <li>✅ Наличие рекламных блоков (Google Ads)</li>
              <li>✅ Наличие Google Maps в выдаче</li>
              <li>✅ Присутствие вашего сайта в ТОП-{params.depth}</li>
              <li>✅ Присутствие сайтов конкурентов</li>
              <li>✅ Определение коммерческого интента</li>
            </ul>
          </Alert>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button 
          variant="primary" 
          onClick={handleSubmit}
          disabled={params.keyword_ids.length === 0}
        >
          🚀 Запустить анализ (${calculateCost()})
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ApplySerpModal;