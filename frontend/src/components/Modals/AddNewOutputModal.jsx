// src/components/Modals/AddNewOutputModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Row, Col } from 'react-bootstrap';

const AddNewOutputModal = ({ show, onHide, onAdd, selectedKeywords }) => {
  const [params, setParams] = useState({
    seed_keywords: [],
    location_code: 2804, // Ukraine
    language_code: 'ru',
    limit: 700,
    search_partners: false,
    sort_by: 'search_volume'
  });

  useEffect(() => {
    // Если есть выбранные ключевые слова, добавляем их как seed
    if (selectedKeywords && selectedKeywords.length > 0) {
      setParams(prev => ({
        ...prev,
        seed_keywords: selectedKeywords.map(k => k.keyword)
      }));
    }
  }, [selectedKeywords, show]);

  const handleSubmit = () => {
    if (params.seed_keywords.length === 0) {
      alert('Добавьте хотя бы одно ключевое слово');
      return;
    }
    onAdd(params);
    onHide();
  };

  const handleKeywordsChange = (text) => {
    const keywords = text.split(/[,\n]/).map(k => k.trim()).filter(k => k);
    setParams(prev => ({ ...prev, seed_keywords: keywords }));
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Добавить новую выдачу ($)</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Реперные ключевые слова:</Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              value={params.seed_keywords.join('\n')}
              onChange={(e) => handleKeywordsChange(e.target.value)}
              placeholder="Введите ключевые слова для анализа"
            />
          </Form.Group>

          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Локация:</Form.Label>
                <Form.Select 
                  value={params.location_code}
                  onChange={(e) => setParams(prev => ({ ...prev, location_code: parseInt(e.target.value) }))}
                >
                  <option value={2804}>Украина</option>
                  <option value={2840}>США</option>
                  <option value={2643}>Россия</option>
                  <option value={2276}>Германия</option>
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
                  <option value="ru">Русский</option>
                  <option value="uk">Украинский</option>
                  <option value="en">Английский</option>
                </Form.Select>
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
                  onChange={(e) => setParams(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
                  min="10"
                  max="700"
                />
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Сортировка:</Form.Label>
                <Form.Select 
                  value={params.sort_by}
                  onChange={(e) => setParams(prev => ({ ...prev, sort_by: e.target.value }))}
                >
                  <option value="search_volume">По объему поиска</option>
                  <option value="cpc">По CPC</option>
                  <option value="competition">По конкуренции</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Включить партнеров поиска"
              checked={params.search_partners}
              onChange={(e) => setParams(prev => ({ ...prev, search_partners: e.target.checked }))}
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Получить выдачу ($)
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddNewOutputModal;