// frontend/src/components/Modals/ChangeFieldCompetitorModal.jsx
import React, { useState } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';

const ChangeFieldCompetitorModal = ({ show, onHide, onSave, selectedCount }) => {
  const [field, setField] = useState('org_type');
  const [value, setValue] = useState('Школа');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!value && field !== 'notes') {
      setError('Пожалуйста, введите значение');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onSave(field, value);
      handleClose();
    } catch (err) {
      setError(err.message || 'Ошибка при сохранении');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setField('org_type');
    setValue('Школа');
    setError('');
    onHide();
  };

  const renderValueInput = () => {
    switch (field) {
      case 'org_type':
        return (
          <Form.Select
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={loading}
          >
            <option value="Школа">Школа</option>
            <option value="База репетиторов">База репетиторов</option>
            <option value="Не школа">Не школа</option>
            <option value="Партнёр">Партнёр</option>
          </Form.Select>
        );
      case 'notes':
        return (
          <Form.Control
            as="textarea"
            rows={3}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Введите заметки"
            disabled={loading}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Modal show={show} onHide={handleClose} size="md">
      <Modal.Header closeButton>
        <Modal.Title>Изменить пользовательское значение</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Alert variant="info">
          Выбрано записей: <strong>{selectedCount}</strong>
        </Alert>

        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Поле для изменения</Form.Label>
            <Form.Select
              value={field}
              onChange={(e) => {
                setField(e.target.value);
                // Сбрасываем значение при смене поля
                if (e.target.value === 'org_type') {
                  setValue('Школа');
                } else {
                  setValue('');
                }
              }}
              disabled={loading}
            >
              <option value="org_type">Тип организации</option>
              <option value="notes">Заметки</option>
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Новое значение</Form.Label>
            {renderValueInput()}
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Сохранение...' : 'Применить'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ChangeFieldCompetitorModal;