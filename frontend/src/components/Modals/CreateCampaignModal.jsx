// frontend/src/components/Modals/CreateCampaignModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

const CreateCampaignModal = ({ show, onHide, onSubmit, campaigns }) => {
  const [objectType, setObjectType] = useState('campaign'); // 'campaign' или 'adgroup'
  const [name, setName] = useState('');
  const [parentCampaignId, setParentCampaignId] = useState('');

  // Сброс формы при открытии модального окна
  useEffect(() => {
    if (show) {
      setObjectType('campaign');
      setName('');
      setParentCampaignId(campaigns && campaigns.length > 0 ? campaigns[0].id : '');
    }
  }, [show, campaigns]);

  const handleSubmit = () => {
    if (!name.trim()) {
      alert('Введите название');
      return;
    }

    if (objectType === 'adgroup' && !parentCampaignId) {
      alert('Выберите родительскую кампанию');
      return;
    }

    onSubmit({
      type: objectType,
      name: name.trim(),
      parentCampaignId: objectType === 'adgroup' ? parseInt(parentCampaignId) : null
    });

    // Закрываем модальное окно
    onHide();
  };

  return (
    <Modal show={show} onHide={onHide} size="md">
      <Modal.Header closeButton>
        <Modal.Title>Создать новый объект</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Тип объекта</Form.Label>
            <Form.Select 
              value={objectType} 
              onChange={(e) => setObjectType(e.target.value)}
            >
              <option value="campaign">Кампания</option>
              <option value="adgroup">Группа объявлений</option>
            </Form.Select>
          </Form.Group>

          {objectType === 'adgroup' && (
            <Form.Group className="mb-3">
              <Form.Label>Родительская кампания</Form.Label>
              <Form.Select 
                value={parentCampaignId} 
                onChange={(e) => setParentCampaignId(e.target.value)}
              >
                {campaigns && campaigns.map(campaign => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          )}

          <Form.Group className="mb-3">
            <Form.Label>Название</Form.Label>
            <Form.Control
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={objectType === 'campaign' ? 'Название кампании' : 'Название группы объявлений'}
              autoFocus
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Отмена
        </Button>
        <Button variant="primary" onClick={handleSubmit}>
          Создать
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateCampaignModal;