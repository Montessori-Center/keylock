// frontend/src/components/Modals/AddCompetitorModal.jsx
import React, { useState } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';

const AddCompetitorModal = ({ show, onHide, onAdd }) => {
  const [domain, setDomain] = useState('');
  const [orgType, setOrgType] = useState('Школа');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    // Валидация
    if (!domain.trim()) {
      setError('Пожалуйста, введите домен');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onAdd({
        domain: domain.trim(),
        org_type: orgType,
        notes: notes.trim()
      });

      // Очищаем форму и закрываем модал
      setDomain('');
      setOrgType('Школа');
      setNotes('');
      onHide();
    } catch (err) {
      setError(err.message || 'Ошибка при добавлении конкурента');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setDomain('');
    setOrgType('Школа');
    setNotes('');
    setError('');
    onHide();
  };

  return (
    <Modal show={show} onHide={handleClose} size="md">
      <Modal.Header closeButton>
        <Modal.Title>Добавить новый сайт</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Домен *</Form.Label>
            <Form.Control
              type="text"
              placeholder="example.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={loading}
            />
            <Form.Text className="text-muted">
              Укажите домен без http:// и www. Например: musicschool.com.ua
            </Form.Text>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Тип организации</Form.Label>
            <Form.Select
              value={orgType}
              onChange={(e) => setOrgType(e.target.value)}
              disabled={loading}
            >
              <option value="Школа">Школа</option>
              <option value="База репетиторов">База репетиторов</option>
              <option value="Не школа">Не школа</option>
              <option value="Партнёр">Партнёр</option>
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Заметки</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Дополнительная информация о конкуренте"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={loading}
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Добавление...' : 'Добавить'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddCompetitorModal;