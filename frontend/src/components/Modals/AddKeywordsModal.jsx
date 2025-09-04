// src/components/Modals/AddKeywordsModal.jsx
import React, { useState } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

const AddKeywordsModal = ({ show, onHide, onAdd }) => {
  const [keywords, setKeywords] = useState('');

  const handleSubmit = () => {
    if (keywords.trim()) {
      onAdd(keywords);
      setKeywords('');
      onHide();
    }
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Добавить новые слова</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group>
            <Form.Label>Введите ключевые слова (через запятую или с новой строки):</Form.Label>
            <Form.Control
              as="textarea"
              rows={10}
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="уроки саксофона киев&#10;обучение на саксофоне&#10;саксофон научиться играть"
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Добавить
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddKeywordsModal;