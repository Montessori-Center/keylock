// src/components/Modals/ApplyFiltersModal.jsx
import React from 'react';
import { Modal, Button } from 'react-bootstrap';

export const ApplyFiltersModal = ({ show, onHide }) => (
  <Modal show={show} onHide={onHide} size="lg">
    <Modal.Header closeButton>
      <Modal.Title>Применить фильтры</Modal.Title>
    </Modal.Header>
    <Modal.Body>
      <p>Функционал фильтров будет добавлен позже</p>
    </Modal.Body>
    <Modal.Footer>
      <Button variant="secondary" onClick={onHide}>Закрыть</Button>
    </Modal.Footer>
  </Modal>
);

export const SettingsModal = ({ show, onHide }) => (
  <Modal show={show} onHide={onHide} size="lg">
    <Modal.Header closeButton>
      <Modal.Title>Настройки</Modal.Title>
    </Modal.Header>
    <Modal.Body>
      <p>Настройки подключения к БД, API и выбор полей будут добавлены позже</p>
    </Modal.Body>
    <Modal.Footer>
      <Button variant="secondary" onClick={onHide}>Закрыть</Button>
    </Modal.Footer>
  </Modal>
);

export default ApplyFiltersModal;