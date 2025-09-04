// src/components/Modals/ApplySerpModal.jsx  
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Row, Col } from 'react-bootstrap';

const ApplySerpModal = ({ show, onHide, onApply, selectedKeywords }) => {
  const [params, setParams] = useState({
    keyword_ids: [],
    location_code: 2804,
    language_code: 'ru',
    device: 'desktop',
    os: 'windows',
    depth: 10
  });

  useEffect(() => {
    if (selectedKeywords && selectedKeywords.length > 0) {
      setParams(prev => ({
        ...prev,
        keyword_ids: selectedKeywords.map(k => k.id)
      }));
    }
  }, [selectedKeywords, show]);

  const handleSubmit = () => {
    if (params.keyword_ids.length === 0) {
      alert('Выберите ключевые слова для анализа');
      return;
    }
    onApply(params);
    onHide();
  };

  return (
    <Modal show={show} onHide={onHide}>
      <Modal.Header closeButton>
        <Modal.Title>Применить SERP анализ ($)</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <p>Выбрано ключевых слов: <strong>{params.keyword_ids.length}</strong></p>
          
          <Row>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>Устройство:</Form.Label>
                <Form.Select 
                  value={params.device}
                  onChange={(e) => setParams(prev => ({ ...prev, device: e.target.value }))}
                >
                  <option value="desktop">Desktop</option>
                  <option value="mobile">Mobile</option>
                </Form.Select>
              </Form.Group>
            </Col>
            <Col md={6}>
              <Form.Group className="mb-3">
                <Form.Label>ОС:</Form.Label>
                <Form.Select 
                  value={params.os}
                  onChange={(e) => setParams(prev => ({ ...prev, os: e.target.value }))}
                >
                  <option value="windows">Windows</option>
                  <option value="macos">MacOS</option>
                  <option value="android">Android</option>
                  <option value="ios">iOS</option>
                </Form.Select>
              </Form.Group>
            </Col>
          </Row>

          <Form.Group className="mb-3">
            <Form.Label>Глубина выдачи:</Form.Label>
            <Form.Control
              type="number"
              value={params.depth}
              onChange={(e) => setParams(prev => ({ ...prev, depth: parseInt(e.target.value) }))}
              min="10"
              max="100"
            />
          </Form.Group>

          <div className="alert alert-info">
            <strong>Внимание!</strong> SERP анализ будет выполнен для каждого выбранного ключевого слова.
            Это платная операция.
          </div>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Применить SERP ($)
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ApplySerpModal;