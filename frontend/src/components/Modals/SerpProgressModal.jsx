// frontend/src/components/Modals/SerpProgressModal.jsx
import React from 'react';
import { Modal, ProgressBar } from 'react-bootstrap';

const SerpProgressModal = ({ show, current, total, currentKeyword }) => {
  const progress = total > 0 ? (current / total) * 100 : 0;

  return (
    <Modal 
      show={show} 
      centered 
      backdrop="static" 
      keyboard={false}
      size="sm"
    >
      <Modal.Body className="text-center">
        <h5>🔍 SERP Анализ</h5>
        <div className="my-3">
          <div className="mb-2">
            <strong>{current}</strong> из <strong>{total}</strong> слов
          </div>
          <ProgressBar 
            now={progress} 
            label={`${Math.round(progress)}%`}
            animated 
            striped 
            variant="primary"
          />
        </div>
        {currentKeyword && (
          <div className="mt-3">
            <small className="text-muted">Анализируется:</small>
            <br />
            <strong>{currentKeyword}</strong>
          </div>
        )}
        <div className="mt-3">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default SerpProgressModal;