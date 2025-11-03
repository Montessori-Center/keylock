// frontend/src/components/Modals/ManageCampaignsModal.jsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, ListGroup, Badge, InputGroup } from 'react-bootstrap';

const ManageCampaignsModal = ({ show, onHide, campaigns, onUpdate }) => {
  const [activeTab, setActiveTab] = useState('list'); // 'list', 'create', 'edit', 'delete'
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [selectedAdGroup, setSelectedAdGroup] = useState(null);
  const [formData, setFormData] = useState({
    type: 'campaign', // 'campaign' или 'adgroup'
    name: '',
    campaignId: ''
  });

  // Сброс формы при открытии модального окна
  useEffect(() => {
    if (show) {
      setActiveTab('list');
      setSelectedCampaign(null);
      setSelectedAdGroup(null);
      setFormData({
        type: 'campaign',
        name: '',
        campaignId: campaigns && campaigns.length > 0 ? campaigns[0].id : ''
      });
    }
  }, [show, campaigns]);

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      alert('Введите название');
      return;
    }

    if (formData.type === 'adgroup' && !formData.campaignId) {
      alert('Выберите родительскую кампанию');
      return;
    }

    await onUpdate({
      action: 'create',
      type: formData.type,
      name: formData.name.trim(),
      campaignId: formData.type === 'adgroup' ? parseInt(formData.campaignId) : null
    });

    // Сброс формы
    setFormData({
      type: 'campaign',
      name: '',
      campaignId: campaigns && campaigns.length > 0 ? campaigns[0].id : ''
    });
    setActiveTab('list');
  };

  const handleEdit = async () => {
    if (!formData.name.trim()) {
      alert('Введите новое название');
      return;
    }

    const target = selectedAdGroup || selectedCampaign;
    if (!target) {
      alert('Выберите объект для редактирования');
      return;
    }

    await onUpdate({
      action: 'edit',
      type: selectedAdGroup ? 'adgroup' : 'campaign',
      id: target.id,
      name: formData.name.trim()
    });

    setSelectedCampaign(null);
    setSelectedAdGroup(null);
    setFormData({ ...formData, name: '' });
    setActiveTab('list');
  };

  const handleDelete = async () => {
    const target = selectedAdGroup || selectedCampaign;
    if (!target) {
      alert('Выберите объект для удаления');
      return;
    }

    const type = selectedAdGroup ? 'группу объявлений' : 'кампанию';
    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить ${type} "${target.name}"?${
        !selectedAdGroup ? '\n\nВНИМАНИЕ: Будут удалены все группы объявлений и ключевые слова в этой кампании!' : ''
      }`
    );

    if (!confirmed) return;

    await onUpdate({
      action: 'delete',
      type: selectedAdGroup ? 'adgroup' : 'campaign',
      id: target.id
    });

    setSelectedCampaign(null);
    setSelectedAdGroup(null);
    setActiveTab('list');
  };

  const renderList = () => (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">Текущие кампании и группы</h5>
        <Button 
          variant="success" 
          size="sm"
          onClick={() => {
            setActiveTab('create');
            setFormData({ ...formData, type: 'campaign' });
          }}
        >
          + Создать
        </Button>
      </div>

      {campaigns.length === 0 ? (
        <div className="text-center text-muted py-4">
          <p>Нет созданных кампаний</p>
          <Button variant="primary" onClick={() => setActiveTab('create')}>
            Создать первую кампанию
          </Button>
        </div>
      ) : (
        <ListGroup style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {campaigns.map(campaign => (
            <div key={campaign.id}>
              <ListGroup.Item
                className="d-flex justify-content-between align-items-center"
                style={{ 
                  backgroundColor: selectedCampaign?.id === campaign.id ? '#e8f0fe' : 'white',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
                onClick={() => {
                  setSelectedCampaign(campaign);
                  setSelectedAdGroup(null);
                }}
              >
                <div>
                  <strong>📁 {campaign.name}</strong>
                  <Badge bg="secondary" className="ms-2">{campaign.status}</Badge>
                </div>
                <div>
                  <Button
                    variant="outline-primary"
                    size="sm"
                    className="me-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCampaign(campaign);
                      setSelectedAdGroup(null);
                      setFormData({ ...formData, name: campaign.name });
                      setActiveTab('edit');
                    }}
                  >
                    ✏️
                  </Button>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCampaign(campaign);
                      setSelectedAdGroup(null);
                      setActiveTab('delete');
                    }}
                  >
                    🗑️
                  </Button>
                </div>
              </ListGroup.Item>

              {campaign.adGroups && campaign.adGroups.map(adGroup => (
                <ListGroup.Item
                  key={adGroup.id}
                  className="d-flex justify-content-between align-items-center ps-5"
                  style={{ 
                    backgroundColor: selectedAdGroup?.id === adGroup.id ? '#e8f0fe' : '#f8f9fa',
                    cursor: 'pointer',
                    borderLeft: '3px solid #4285f4'
                  }}
                  onClick={() => {
                    setSelectedAdGroup(adGroup);
                    setSelectedCampaign(campaign);
                  }}
                >
                  <div>
                    <span>└─ {adGroup.name}</span>
                    <Badge bg="secondary" className="ms-2">{adGroup.status}</Badge>
                    {adGroup.hasChanges && (
                      <Badge bg="warning" className="ms-2">
                        {adGroup.newChanges} изм.
                      </Badge>
                    )}
                  </div>
                  <div>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      className="me-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAdGroup(adGroup);
                        setSelectedCampaign(campaign);
                        setFormData({ ...formData, name: adGroup.name });
                        setActiveTab('edit');
                      }}
                    >
                      ✏️
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAdGroup(adGroup);
                        setSelectedCampaign(campaign);
                        setActiveTab('delete');
                      }}
                    >
                      🗑️
                    </Button>
                  </div>
                </ListGroup.Item>
              ))}
            </div>
          ))}
        </ListGroup>
      )}
    </div>
  );

  const renderCreate = () => (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="mb-0">Создание нового объекта</h5>
        <Button variant="outline-secondary" size="sm" onClick={() => setActiveTab('list')}>
          ← Назад к списку
        </Button>
      </div>

      <Form>
        <Form.Group className="mb-3">
          <Form.Label>Тип объекта</Form.Label>
          <Form.Select 
            value={formData.type} 
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
          >
            <option value="campaign">Кампания</option>
            <option value="adgroup">Группа объявлений</option>
          </Form.Select>
        </Form.Group>

        {formData.type === 'adgroup' && (
          <Form.Group className="mb-3">
            <Form.Label>Родительская кампания</Form.Label>
            <Form.Select 
              value={formData.campaignId} 
              onChange={(e) => setFormData({ ...formData, campaignId: e.target.value })}
            >
              {campaigns.map(campaign => (
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
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder={formData.type === 'campaign' ? 'Название кампании' : 'Название группы объявлений'}
            autoFocus
          />
        </Form.Group>

        <div className="d-grid gap-2">
          <Button variant="success" onClick={handleCreate}>
            ✓ Создать
          </Button>
          <Button variant="outline-secondary" onClick={() => setActiveTab('list')}>
            Отмена
          </Button>
        </div>
      </Form>
    </div>
  );

  const renderEdit = () => {
    const target = selectedAdGroup || selectedCampaign;
    const type = selectedAdGroup ? 'группы объявлений' : 'кампании';

    return (
      <div>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">Редактирование {type}</h5>
          <Button variant="outline-secondary" size="sm" onClick={() => setActiveTab('list')}>
            ← Назад к списку
          </Button>
        </div>

        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Текущее название</Form.Label>
            <Form.Control
              type="text"
              value={target?.name || ''}
              disabled
              readOnly
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Новое название</Form.Label>
            <Form.Control
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Введите новое название"
              autoFocus
            />
          </Form.Group>

          <div className="d-grid gap-2">
            <Button variant="primary" onClick={handleEdit}>
              ✓ Сохранить изменения
            </Button>
            <Button variant="outline-secondary" onClick={() => setActiveTab('list')}>
              Отмена
            </Button>
          </div>
        </Form>
      </div>
    );
  };

  const renderDelete = () => {
    const target = selectedAdGroup || selectedCampaign;
    const type = selectedAdGroup ? 'группу объявлений' : 'кампанию';

    return (
      <div>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0 text-danger">Удаление {type}</h5>
          <Button variant="outline-secondary" size="sm" onClick={() => setActiveTab('list')}>
            ← Назад к списку
          </Button>
        </div>

        <div className="alert alert-danger">
          <h6>⚠️ Внимание!</h6>
          <p>Вы собираетесь удалить {type}: <strong>{target?.name}</strong></p>
          {!selectedAdGroup && (
            <p className="mb-0">
              <strong>Будут удалены все группы объявлений и ключевые слова в этой кампании!</strong>
            </p>
          )}
        </div>

        <div className="d-grid gap-2">
          <Button variant="danger" onClick={handleDelete}>
            🗑️ Да, удалить
          </Button>
          <Button variant="outline-secondary" onClick={() => setActiveTab('list')}>
            Отмена
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Управление кампаниями</Modal.Title>
      </Modal.Header>
      <Modal.Body style={{ minHeight: '400px' }}>
        {activeTab === 'list' && renderList()}
        {activeTab === 'create' && renderCreate()}
        {activeTab === 'edit' && renderEdit()}
        {activeTab === 'delete' && renderDelete()}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Закрыть
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ManageCampaignsModal;