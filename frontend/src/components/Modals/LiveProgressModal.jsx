import React, { useState, useEffect } from 'react';
import { Modal, ProgressBar } from 'react-bootstrap';

const LiveProgressModal = ({ show, keyword }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!show) {
      setProgress(0);
      return;
    }

    // ✅ Анимация прогресса от 0 до 90% за ~3 секунды
    // Последние 10% устанавливаются при завершении запроса
    const startTime = Date.now();
    const duration = 3000; // 3 секунды
    const targetProgress = 90; // Дойдем до 90%, последние 10% при завершении

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const currentProgress = Math.min((elapsed / duration) * targetProgress, targetProgress);
      
      setProgress(currentProgress);
      
      if (currentProgress >= targetProgress) {
        clearInterval(interval);
      }
    }, 50); // Обновляем каждые 50ms для плавности

    return () => clearInterval(interval);
  }, [show]);

  // Определяем текст статуса в зависимости от прогресса
  const getStatusText = () => {
    if (progress < 20) return '⏳ Подготовка запроса...';
    if (progress < 40) return '📡 Подключение к DataForSeo...';
    if (progress < 60) return '🌐 Получение данных из Google...';
    if (progress < 80) return '🔬 Анализ SERP результатов...';
    if (progress < 90) return '💾 Обработка данных...';
    return '✅ Завершение...';
  };

  return (
    <Modal 
      show={show} 
      centered 
      backdrop="static" 
      keyboard={false}
      size="sm"
      className="live-progress-modal"
    >
      <Modal.Body className="text-center py-4">
        <h5 className="mb-3">
          <span className="text-success">🔍</span> SERP Анализ (LIVE)
        </h5>
        
        <div className="my-4">
          {keyword && (
            <div className="mb-3">
              <small className="text-muted">Анализируется:</small>
              <br />
              <strong className="text-primary">{keyword}</strong>
            </div>
          )}
          
          <ProgressBar 
            now={progress} 
            label={`${Math.round(progress)}%`}
            animated 
            striped 
            variant="success"
            style={{ height: '25px', fontSize: '14px' }}
          />
        </div>
        
        <div className="mt-4">
          <div className="spinner-border text-success mb-2" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
          <div>
            <small className="text-muted">
              {getStatusText()}
            </small>
          </div>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default LiveProgressModal;