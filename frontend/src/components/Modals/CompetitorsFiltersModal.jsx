// frontend/src/components/Modals/CompetitorsFiltersModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

const CompetitorsFiltersModal = ({ show, onHide, competitors, onApply }) => {
  const [filters, setFilters] = useState({
    onlyUnprocessed: false
  });

  // Сброс фильтров при открытии
  useEffect(() => {
    if (show) {
      setFilters({
        onlyUnprocessed: false
      });
    }
  }, [show]);

  const handleApply = () => {
    let filtered = [...competitors];

    // Фильтр: только необработанные сайты (is_new = true)
    if (filters.onlyUnprocessed) {
      filtered = filtered.filter(c => c.is_new === true);
    }

    const filteredIds = filtered.map(c => c.id);
    onApply(filteredIds);
    onHide();
  };

  const handleReset = () => {
    setFilters({
      onlyUnprocessed: false
    });
    onApply(competitors.map(c => c.id)); // Выбрать все
    onHide();
  };

  return (
    <Modal show={show} onHide={onHide} size="md">
      <Modal.Header closeButton>
        <Modal.Title>Фильтры конкурентов</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              id="filter-unprocessed"
              label="Только необработанные сайты"
              checked={filters.onlyUnprocessed}
              onChange={(e) => setFilters({ ...filters, onlyUnprocessed: e.target.checked })}
            />
            <Form.Text className="text-muted">
              Показывать только сайты с флагом "новый" (необработанные)
            </Form.Text>
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="outline-secondary" onClick={handleReset}>
          Сбросить фильтры
        </Button>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleApply}>
          Применить
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CompetitorsFiltersModal;