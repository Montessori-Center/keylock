import React, { useState } from 'react';
import { FaChevronRight, FaChevronDown, FaBars } from 'react-icons/fa';

const Sidebar = ({ isOpen, onToggle, campaigns, selectedCampaign, selectedAdGroup, onSelectAdGroup }) => {
  const [expandedCampaigns, setExpandedCampaigns] = useState([1]);

  const toggleCampaign = (campaignId) => {
    setExpandedCampaigns(prev => 
      prev.includes(campaignId) 
        ? prev.filter(id => id !== campaignId)
        : [...prev, campaignId]
    );
  };

  return (
    <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <button className="sidebar-toggle" onClick={onToggle}>
        <FaBars />
      </button>
      
      {isOpen && (
        <div className="sidebar-content">
          <h5>Кампании</h5>
          {campaigns && campaigns.length > 0 ? campaigns.map(campaign => (
            <div key={campaign.id} className="campaign-item">
              <div 
                className="campaign-header"
                onClick={() => toggleCampaign(campaign.id)}
              >
                {expandedCampaigns.includes(campaign.id) ? <FaChevronDown /> : <FaChevronRight />}
                <span className="campaign-name">{campaign.name}</span>
              </div>
              
              {expandedCampaigns.includes(campaign.id) && campaign.adGroups && (
                <div className="ad-groups">
                  {campaign.adGroups.map(adGroup => {
                    // Определяем классы для группы
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
            <div className="no-campaigns">Нет кампаний</div>
          )}
        </div>
      )}
    </div>
  );
};

export default Sidebar;