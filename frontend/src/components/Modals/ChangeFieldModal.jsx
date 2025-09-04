// src/components/Modals/ChangeFieldModal.jsx
import React, { useState } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

const ChangeFieldModal = ({ show, onHide, onApply }) => {
  const [field, setField] = useState('');
  const [value, setValue] = useState('');

  const fields = [
    { value: 'criterion_type', label: 'Criterion Type', type: 'select', 
      options: ['Phrase', 'Broad', 'Exact'] },
    { value: 'status', label: 'Status', type: 'select',
      options: ['Enabled', 'Paused'] },
    { value: 'max_cpc', label: 'Max CPC', type: 'number' },
    { value: 'comment', label: 'Comment', type: 'text' },
    { value: 'intent_type', label: 'Тип интента', type: 'select',
      options: ['Коммерческий', 'Информационный', 'Навигационный', 'Транзакционный'] },
    { value: 'recommendation', label: 'Рекомендация', type: 'select',
      options: ['Использовать', 'Тестировать', 'Пауза', 'Не использовать', 'Минусовать'] }
  ];

  const selectedField = fields.find(f => f.value === field);

  const handleSubmit = () => {
    if (field && value !== '') {
      onApply(field, value);
      setField('');
      setValue('');
      onHide();
    }
  };

  const handleClose = () => {
    setField('');
    setValue('');
    onHide();
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Изменить пользовательское значение</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Выберите поле:</Form.Label>
            <Form.Select value={field} onChange={(e) => {
              setField(e.target.value);
              setValue(''); // Сбрасываем значение при смене поля
            }}>
              <option value="">-- Выберите поле --</option>
              {fields.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </Form.Select>
          </Form.Group>

          {field && (
            <Form.Group className="mb-3">
              <Form.Label>Новое значение:</Form.Label>
              {selectedField.type === 'select' ? (
                <Form.Select value={value} onChange={(e) => setValue(e.target.value)}>
                  <option value="">-- Выберите значение --</option>
                  {selectedField.options.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </Form.Select>
              ) : selectedField.type === 'number' ? (
                <Form.Control
                  type="number"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="Введите числовое значение"
                  step="0.01"
                  min="0"
                />
              ) : (
                <Form.Control
                  type="text"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  placeholder="Введите новое значение"
                />
              )}
            </Form.Group>
          )}

          {field === 'recommendation' && value && (
            <div className="alert alert-info">
              <strong>{value}:</strong>
              {value === 'Использовать' && ' Ключевое слово будет активно использоваться'}
              {value === 'Тестировать' && ' Ключевое слово будет в тестовом режиме'}
              {value === 'Пауза' && ' Ключевое слово будет приостановлено'}
              {value === 'Не использовать' && ' Ключевое слово не будет использоваться'}
              {value === 'Минусовать' && ' Ключевое слово будет добавлено в минус-слова'}
            </div>
          )}
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={!field || value === ''}>
          Применить
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ChangeFieldModal;