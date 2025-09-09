// src/components/Modals/AddNewOutputModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Row, Col, Alert } from 'react-bootstrap';
// import api from '../../services/api'; // Временно закомментируем если не используется

const AddNewOutputModal = ({ show, onHide, onAdd, selectedKeywords }) => {
  // Дата по умолчанию - 6 месяцев назад
  const getDefaultDateFrom = () => {
    const date = new Date();
    date.setMonth(date.getMonth() - 6);
    return date.toISOString().split('T')[0];
  };

  const getDefaultDateTo = () => {
    return new Date().toISOString().split('T')[0];
  };

  const [params, setParams] = useState({
    seed_keywords: [],
    location_name: 'Ukraine',
    location_code: 2804,
    language_code: 'ru',
    limit: 700,
    search_partners: false,
    date_from: getDefaultDateFrom(),
    date_to: getDefaultDateTo(),
    include_seed_keyword: true,
    include_clickstream_data: false,
    include_serp_info: false,
    sort_by: 'relevance'
  });

  const [locations, setLocations] = useState([]);
  const [languages, setLanguages] = useState([]);
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState(0);

  // Загрузка списка локаций при открытии модального окна
  useEffect(() => {
    if (show) {
      loadLocations();
      loadLanguages();
    }
  }, [show]);

  // Если есть выбранные ключевые слова, добавляем их как seed
  useEffect(() => {
    if (selectedKeywords && selectedKeywords.length > 0) {
      setParams(prev => ({
        ...prev,
        seed_keywords: selectedKeywords.map(k => k.keyword)
      }));
    }
  }, [selectedKeywords, show]);

  // Расчет примерной стоимости
  useEffect(() => {
    // Базовая стоимость запроса Keywords for Keywords: $0.05
    let cost = 0.05;
    
    // Дополнительная стоимость за SERP info (примерно)
    if (params.include_serp_info) {
      cost += 0.02;
    }
    
    // Дополнительная стоимость за Clickstream data
    if (params.include_clickstream_data) {
      cost += 0.03;
    }
    
    setEstimatedCost(cost);
  }, [params.include_serp_info, params.include_clickstream_data]);

  const loadLocations = async () => {
    setLoadingLocations(true);
    try {
      // Здесь должен быть запрос к API для получения списка локаций
      // Пока используем статический список популярных стран
      const popularLocations = [
        { code: 2804, name: 'Ukraine', name_ru: 'Украина' },
        { code: 2840, name: 'United States', name_ru: 'США' },
        { code: 2643, name: 'Russia', name_ru: 'Россия' },
        { code: 2276, name: 'Germany', name_ru: 'Германия' },
        { code: 2826, name: 'United Kingdom', name_ru: 'Великобритания' },
        { code: 2250, name: 'France', name_ru: 'Франция' },
        { code: 2616, name: 'Poland', name_ru: 'Польша' },
        { code: 2724, name: 'Spain', name_ru: 'Испания' },
        { code: 2380, name: 'Italy', name_ru: 'Италия' },
        { code: 2124, name: 'Canada', name_ru: 'Канада' },
        { code: 2036, name: 'Australia', name_ru: 'Австралия' },
        { code: 2528, name: 'Netherlands', name_ru: 'Нидерланды' },
        { code: 2752, name: 'Sweden', name_ru: 'Швеция' },
        { code: 2756, name: 'Switzerland', name_ru: 'Швейцария' },
        { code: 2040, name: 'Austria', name_ru: 'Австрия' },
        { code: 2112, name: 'Belarus', name_ru: 'Беларусь' },
        { code: 2398, name: 'Kazakhstan', name_ru: 'Казахстан' },
        { code: 2792, name: 'Turkey', name_ru: 'Турция' },
        { code: 2376, name: 'Israel', name_ru: 'Израиль' },
        { code: 2784, name: 'United Arab Emirates', name_ru: 'ОАЭ' }
      ];
      setLocations(popularLocations);
    } catch (error) {
      console.error('Error loading locations:', error);
    } finally {
      setLoadingLocations(false);
    }
  };

  const loadLanguages = () => {
    // Список языков
    const languagesList = [
      { code: 'ru', name: 'Русский' },
      { code: 'uk', name: 'Украинский' },
      { code: 'en', name: 'Английский' },
      { code: 'de', name: 'Немецкий' },
      { code: 'fr', name: 'Французский' },
      { code: 'es', name: 'Испанский' },
      { code: 'it', name: 'Итальянский' },
      { code: 'pl', name: 'Польский' },
      { code: 'tr', name: 'Турецкий' },
      { code: 'ar', name: 'Арабский' },
      { code: 'he', name: 'Иврит' }
    ];
    setLanguages(languagesList);
  };

  const handleLocationChange = (locationName) => {
    const location = locations.find(l => l.name === locationName);
    if (location) {
      setParams(prev => ({
        ...prev,
        location_name: location.name,
        location_code: location.code
      }));
    }
  };

  const handleSubmit = () => {
    if (params.seed_keywords.length === 0) {
      alert('Добавьте хотя бы одно ключевое слово');
      return;
    }
    
    if (params.seed_keywords.length > 1000) {
      alert('Максимум 1000 ключевых слов за один запрос');
      return;
    }
    
    if (params.limit > 700) {
      alert('Максимальный лимит для live запроса - 700');
      return;
    }
    
    onAdd(params);
    onHide();
  };

  const handleKeywordsChange = (text) => {
    const keywords = text.split(/[,\n]/).map(k => k.trim()).filter(k => k);
    setParams(prev => ({ ...prev, seed_keywords: keywords }));
  };

  const sortByOptions = [
    { value: 'relevance', label: 'По релевантности' },
    { value: 'search_volume', label: 'По объему поиска' },
    { value: 'competition', label: 'По конкуренции' },
    { value: 'competition_index', label: 'По индексу конкуренции' },
    { value: 'cpc', label: 'По CPC' },
    { value: 'high_top_of_page_bid', label: 'По макс. ставке' },
    { value: 'low_top_of_page_bid', label: 'По мин. ставке' }
  ];

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          Добавить новую выдачу ($)
          <small className="text-muted ms-2">
            Примерная стоимость: ${estimatedCost.toFixed(3)}
          </small>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Alert variant="info">
            <strong>DataForSeo API:</strong> Keywords for Keywords Live
            <br />
            <small>Получение релевантных ключевых слов на основе seed-фраз</small>
          </Alert>

          <Form.Group className="mb-3">
            <Form.Label>
              Seed ключевые слова:
              <small className="text-muted ms-2">
                ({params.seed_keywords.length} / 1000)
              </small>
            </Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              value={params.seed_keywords.join('\n')}
              onChange={(e) => handleKeywordsChange(e.target.value)}
              placeholder="Введите ключевые слова для анализа (каждое с новой строки или через запятую)"
            />
            <Form.Text className="text-muted">
              Введите от 1 до 1000 ключевых слов для получения релевантной выдачи
            </Form.Text>
          </Form.Group>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Локация:</Form.Label>
                <Form.Select 
                  value={params.location_name}
                  onChange={(e) => handleLocationChange(e.target.value)}
                  disabled={loadingLocations}
                >
                  {locations.map(loc => (
                    <option key={loc.code} value={loc.name}>
                      {loc.name_ru || loc.name} ({loc.code})
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Язык:</Form.Label>
                <Form.Select 
                  value={params.language_code}
                  onChange={(e) => setParams(prev => ({ ...prev, language_code: e.target.value }))}
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Дата начала периода:</Form.Label>
                <Form.Control
                  type="date"
                  value={params.date_from}
                  onChange={(e) => setParams(prev => ({ ...prev, date_from: e.target.value }))}
                  max={params.date_to}
                />
                <Form.Text className="text-muted">
                  Для получения исторических данных
                </Form.Text>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Дата конца периода:</Form.Label>
                <Form.Control
                  type="date"
                  value={params.date_to}
                  onChange={(e) => setParams(prev => ({ ...prev, date_to: e.target.value }))}
                  min={params.date_from}
                  max={new Date().toISOString().split('T')[0]}
                />
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Лимит результатов:</Form.Label>
                <Form.Control
                  type="number"
                  value={params.limit}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    limit: Math.min(700, Math.max(1, parseInt(e.target.value) || 1))
                  }))}
                  min="1"
                  max="700"
                />
                <Form.Text className="text-muted">
                  Максимум 700 для live запроса
                </Form.Text>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Сортировка:</Form.Label>
                <Form.Select 
                  value={params.sort_by}
                  onChange={(e) => setParams(prev => ({ ...prev, sort_by: e.target.value }))}
                >
                  {sortByOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Включить партнеров поиска:</Form.Label>
                <Form.Select
                  value={params.search_partners ? 'true' : 'false'}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    search_partners: e.target.value === 'true' 
                  }))}
                >
                  <option value="false">Нет</option>
                  <option value="true">Да</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  Включить данные от партнеров Google Search
                </Form.Text>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Включить seed-слова в результат:</Form.Label>
                <Form.Select
                  value={params.include_seed_keyword ? 'true' : 'false'}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    include_seed_keyword: e.target.value === 'true' 
                  }))}
                >
                  <option value="true">Да</option>
                  <option value="false">Нет</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  Добавить исходные слова в выдачу
                </Form.Text>
              </Form.Group>
            </Col>
          </Row>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>
                  Включить SERP данные:
                  <span className="text-warning ms-1">($)</span>
                </Form.Label>
                <Form.Select
                  value={params.include_serp_info ? 'true' : 'false'}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    include_serp_info: e.target.value === 'true' 
                  }))}
                >
                  <option value="false">Нет</option>
                  <option value="true">Да (+$0.02)</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  Анализ выдачи для определения интента
                </Form.Text>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>
                  Включить Clickstream данные:
                  <span className="text-warning ms-1">($)</span>
                </Form.Label>
                <Form.Select
                  value={params.include_clickstream_data ? 'true' : 'false'}
                  onChange={(e) => setParams(prev => ({ 
                    ...prev, 
                    include_clickstream_data: e.target.value === 'true' 
                  }))}
                >
                  <option value="false">Нет</option>
                  <option value="true">Да (+$0.03)</option>
                </Form.Select>
                <Form.Text className="text-muted">
                  Дополнительная статистика кликов
                </Form.Text>
              </Form.Group>
            </Col>
          </Row>

          <Alert variant="warning">
            <strong>Внимание!</strong> Это платный запрос к DataForSeo API.
            <br />
            Примерная стоимость: <strong>${estimatedCost.toFixed(3)}</strong>
            <br />
            <small>
              Количество seed-слов: {params.seed_keywords.length} | 
              Лимит результатов: {params.limit}
            </small>
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
          disabled={params.seed_keywords.length === 0}
        >
          Получить выдачу (${estimatedCost.toFixed(3)})
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddNewOutputModal;