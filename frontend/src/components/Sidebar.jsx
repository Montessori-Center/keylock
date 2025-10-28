// frontend/src/components/Sidebar.jsx - ВОССТАНОВЛЕННАЯ ВЕРСИЯ
import React, { useState, useEffect } from 'react';
import { FaChevronRight, FaChevronDown, FaBars } from 'react-icons/fa';
import api from '../services/api';

const Sidebar = ({ 
  isOpen, 
  onToggle, 
  campaigns, 
  selectedCampaign, 
  selectedAdGroup, 
  onSelectAdGroup,
  onOpenCompetitors,
  onCreateClick
}) => {
  const [expandedCampaigns, setExpandedCampaigns] = useState([1]);
  const [competitorsPending, setCompetitorsPending] = useState(0);

  const toggleCampaign = (campaignId) => {
      setExpandedCampaigns(prev => 
        prev.includes(campaignId) 
          ? prev.filter(id => id !== campaignId)  // Если уже открыта - закрываем
          : [campaignId]  // ✅ ИСПРАВЛЕНО: открываем только эту, закрывая остальные
      );
    };

  // Загрузка статистики конкурентов для badge
  useEffect(() => {
    const loadCompetitorsStats = async () => {
      try {
        const response = await api.getCompetitorsStats();
        if (response.success && response.stats) {
          setCompetitorsPending(response.stats.newPending || 0);
        }
      } catch (error) {
        console.error('Error loading competitors stats:', error);
      }
    };

    loadCompetitorsStats();
    
    // Обновление каждые 30 секунд
    const interval = setInterval(loadCompetitorsStats, 30000);
    return () => clearInterval(interval);
  }, []);
  
  // Автоматическое раскрытие кампании с выбранной группой
    useEffect(() => {
      if (selectedAdGroup && campaigns.length > 0) {
        // Находим кампанию, которой принадлежит выбранная группа
        const parentCampaign = campaigns.find(campaign => 
          (campaign.adGroups || campaign.ad_groups)?.some(ag => ag.id === selectedAdGroup.id)
        );
        
        if (parentCampaign && !expandedCampaigns.includes(parentCampaign.id)) {
          setExpandedCampaigns([parentCampaign.id]);
        }
      }
    }, [selectedAdGroup, campaigns]);

  return (
      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <button className="sidebar-toggle" onClick={onToggle}>
          <FaBars />
        </button>
        
        {isOpen && (
          <div className="sidebar-content">
            {/* Верхняя часть с прокруткой */}
            <div className="sidebar-scrollable">
              {/* Кнопка "Школы-конкуренты" с badge */}
              <button 
                className="competitors-btn" 
                onClick={() => {
                    localStorage.setItem('showCompetitors', 'true');
                    onOpenCompetitors();
                  }}
                style={{ position: 'relative' }}
              >
                Школы-конкуренты
                {competitorsPending > 0 && (
                  <span className="competitors-badge">{competitorsPending}</span>
                )}
              </button>
    
              <div style={{ borderTop: '1px solid #dadce0', margin: '10px 0' }}></div>
    
              <h5>Кампании</h5>
              {campaigns && campaigns.length > 0 ? campaigns.map(campaign => (
                <div key={campaign.id} className="campaign-item">
                  <div 
                    className="campaign-header"
                    onClick={() => toggleCampaign(campaign.id)}
                  >
                    {expandedCampaigns.includes(campaign.id) ? 
                      <FaChevronDown /> : 
                      <FaChevronRight />
                    }
                    <span className="campaign-name">{campaign.name}</span>
                  </div>
                  
                  {expandedCampaigns.includes(campaign.id) && (campaign.adGroups || campaign.ad_groups) && (
                    <div className="ad-groups">
                      {(campaign.adGroups || campaign.ad_groups).map(adGroup => {
                        const isActive = selectedAdGroup?.id === adGroup.id;
                        const hasChanges = adGroup.hasChanges || adGroup.newChanges > 0;
                        
                        const className = `ad-group-item ${isActive ? 'active' : ''} ${hasChanges ? 'has-changes' : ''}`;
                        
                        return (
                          <div 
                            key={adGroup.id}
                            className={className}
                            onClick={() => onSelectAdGroup(adGroup)}
                            title={hasChanges ? `${adGroup.newChanges} новых изменений` : ''}
                          >
                            <span className={`ad-group-name ${hasChanges ? 'bold-text' : ''}`}>
                              {adGroup.name}
                            </span>
                            
                            {hasChanges && (
                              <div className="changes-indicator">
                                <span className="changes-badge">{adGroup.newChanges}</span>
                                
                                {adGroup.batchColors && adGroup.batchColors.length > 0 && (
                                  <div className="batch-colors-indicator">
                                    {adGroup.batchColors.slice(0, 3).map((color, index) => (
                                      <span 
                                        key={index}
                                        className="batch-color-dot"
                                        style={{ backgroundColor: color }}
                                        title={`Партия ${index + 1}`}
                                      />
                                    ))}
                                    {adGroup.batchColors.length > 3 && (
                                      <span className="more-colors">+{adGroup.batchColors.length - 3}</span>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )) : (
                <div style={{ padding: '10px', color: '#5f6368', fontSize: '13px' }}>
                  Кампании не найдены
                </div>
              )}
            </div>
            
            {/* Кнопка "Создать" прибита к низу */}
            <div className="sidebar-footer">
              <button 
                className="create-btn" 
                onClick={onCreateClick}
              >
                + Создать
              </button>
            </div>
          </div>
        )}
      </div>
    );
};

export default Sidebar;