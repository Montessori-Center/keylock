// src/components/Sidebar.jsx
import React, { useState } from 'react';
import { FaChevronRight, FaChevronDown, FaBars } from 'react-icons/fa';

const Sidebar = ({ isOpen, onToggle, campaigns, selectedCampaign, selectedAdGroup, onSelectAdGroup }) => {
  const [expandedCampaigns, setExpandedCampaigns] = useState([1]); // По умолчанию развернута первая кампания

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
          {campaigns.map(campaign => (
            <div key={campaign.id} className="campaign-item">
              <div 
                className="campaign-header"
                onClick={() => toggleCampaign(campaign.id)}
              >
                {expandedCampaigns.includes(campaign.id) ? <FaChevronDown /> : <FaChevronRight />}
                <span className="campaign-name">{campaign.name}</span>
              </div>
              
              {expandedCampaigns.includes(campaign.id) && (
                  <div className="ad-groups">
                    {campaign.adGroups.map(adGroup => (
                      <div 
                        key={adGroup.id}
                        className={`ad-group-item ${selectedAdGroup?.id === adGroup.id ? 'active' : ''} ${adGroup.newChanges > 0 ? 'has-changes' : ''}`}
                        onClick={() => onSelectAdGroup(adGroup)}
                        title={adGroup.newChanges > 0 ? `${adGroup.newChanges} новых изменений` : ''}
                      >
                        <span className="ad-group-name">{adGroup.name}</span>
                        {adGroup.newChanges > 0 && (
                          <span className="changes-badge">{adGroup.newChanges}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Sidebar;

