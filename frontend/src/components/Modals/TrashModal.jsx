// frontend/src/components/Modals/TrashModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Table, Alert, Badge } from 'react-bootstrap';
import { FaTrashRestore, FaTrash, FaClock } from 'react-icons/fa';
import api from '../../services/api';

const TrashModal = ({ show, onHide, adGroupId, onRestore }) => {
  const [trashKeywords, setTrashKeywords] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoDeleteDays, setAutoDeleteDays] = useState(30);

  useEffect(() => {
    if (show && adGroupId) {
      loadTrashKeywords();
    }
  }, [show, adGroupId]);

  const loadTrashKeywords = async () => {
    setLoading(true);
    try {
      const response = await api.getTrashKeywords(adGroupId);
      if (response.success) {
        setTrashKeywords(response.data);
        setAutoDeleteDays(response.auto_delete_days);
      }
    } catch (error) {
      console.error('Error loading trash:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(trashKeywords.map(k => k.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectKeyword = (id, checked) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter(sid => sid !== id));
    }
  };

  const handleRestore = async () => {
    if (selectedIds.length === 0) {
      alert('Выберите ключевые слова для восстановления');
      return;
    }

    try {
      const response = await api.restoreKeywords(selectedIds);
      if (response.success) {
        alert(response.message);
        loadTrashKeywords();
        setSelectedIds([]);
        if (onRestore) onRestore();
      }
    } catch (error) {
      alert('Ошибка восстановления: ' + error.message);
    }
  };

  const handleDeletePermanently = async () => {
    if (selectedIds.length === 0) {
      alert('Выберите ключевые слова для удаления');
      return;
    }

    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить навсегда ${selectedIds.length} ключевых слов?\n\nЭто действие необратимо!`
    );

    if (!confirmed) return;

    try {
      const response = await api.deleteKeywordsPermanently(selectedIds);
      if (response.success) {
        alert(response.message);
        loadTrashKeywords();
        setSelectedIds([]);
      }
    } catch (error) {
      alert('Ошибка удаления: ' + error.message);
    }
  };

  const getDaysRemainingBadge = (days) => {
    if (days <= 3) {
      return <Badge bg="danger">{days}д</Badge>;
    } else if (days <= 7) {
      return <Badge bg="warning">{days}д</Badge>;
    } else {
      return <Badge bg="secondary">{days}д</Badge>;
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU');
  };

  return (
    <Modal show={show} onHide={onHide} size="xl">
      <Modal.Header closeButton className="bg-warning bg-opacity-10">
        <Modal.Title>
          <FaTrash className="me-2" />
          Корзина удаленных ключевых слов
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {loading ? (
          <div className="text-center py-5">Загрузка...</div>
        ) : (
          <>
            <Alert variant="info">
              <FaClock className="me-2" />
              Удаленные ключевые слова хранятся <strong>{autoDeleteDays} дней</strong>, 
              после чего удаляются автоматически.
              <br />
              <small>Вы можете восстановить их в любой момент до автоматического удаления.</small>
            </Alert>

            {trashKeywords.length === 0 ? (
              <div className="text-center py-5 text-muted">
                <FaTrash size={48} className="mb-3 opacity-25" />
                <p>Корзина пуста</p>
              </div>
            ) : (
              <>
                <div className="mb-3 d-flex justify-content-between align-items-center">
                  <div>
                    <Form.Check
                      type="checkbox"
                      label={`Выбрать все (${trashKeywords.length})`}
                      checked={selectedIds.length === trashKeywords.length && trashKeywords.length > 0}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </div>
                  <div>
                    <span className="text-muted">Выбрано: {selectedIds.length}</span>
                  </div>
                </div>

                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <Table striped hover size="sm">
                    <thead className="sticky-top bg-white">
                      <tr>
                        <th width="40"></th>
                        <th>Ключевое слово</th>
                        <th>Тип</th>
                        <th>Max CPC</th>
                        <th>Интент</th>
                        <th>Запросов</th>
                        <th>Удалено</th>
                        <th>Осталось</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trashKeywords.map(keyword => (
                        <tr key={keyword.id}>
                          <td>
                            <Form.Check
                              type="checkbox"
                              checked={selectedIds.includes(keyword.id)}
                              onChange={(e) => handleSelectKeyword(keyword.id, e.target.checked)}
                            />
                          </td>
                          <td>{keyword.keyword}</td>
                          <td>{keyword.criterion_type}</td>
                          <td>{keyword.max_cpc || '-'}</td>
                          <td>{keyword.intent_type || '-'}</td>
                          <td>{keyword.avg_monthly_searches || '-'}</td>
                          <td>{formatDate(keyword.deleted_at)}</td>
                          <td>{getDaysRemainingBadge(keyword.days_remaining)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </div>

                <Alert variant="warning" className="mt-3 mb-0">
                  <small>
                    <strong>Внимание:</strong> Ключевые слова с меткой 
                    <Badge bg="danger" className="mx-1">3д</Badge> или меньше 
                    будут удалены в ближайшие дни!
                  </small>
                </Alert>
              </>
            )}
          </>
        )}
      </Modal.Body>
      <Modal.Footer>
        <div className="d-flex justify-content-between w-100">
          <div>
            {selectedIds.length > 0 && (
              <Button 
                variant="danger" 
                onClick={handleDeletePermanently}
                disabled={loading}
              >
                <FaTrash className="me-2" />
                Удалить навсегда ({selectedIds.length})
              </Button>
            )}
          </div>
          <div>
            <Button variant="secondary" onClick={onHide} className="me-2">
              Закрыть
            </Button>
            {selectedIds.length > 0 && (
              <Button 
                variant="success" 
                onClick={handleRestore}
                disabled={loading}
              >
                <FaTrashRestore className="me-2" />
                Восстановить ({selectedIds.length})
              </Button>
            )}
          </div>
        </div>
      </Modal.Footer>
    </Modal>
  );
};

export default TrashModal;