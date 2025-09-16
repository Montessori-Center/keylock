// frontend/src/services/api.js
import axios from 'axios';

// Используем относительный путь - все запросы пойдут через прокси
const API_BASE_URL = '/api';

console.log('API Base URL:', API_BASE_URL);

const api = {
  // Keywords
  getKeywords: async (adGroupId) => {
    const response = await axios.get(`${API_BASE_URL}/keywords/list/${adGroupId}`);
    return response.data;
  },

  addKeywords: async (adGroupId, keywords) => {
    const response = await axios.post(`${API_BASE_URL}/keywords/add`, {
      ad_group_id: adGroupId,
      keywords: keywords
    });
    return response.data;
  },
  
  acceptChanges: async (adGroupId) => {
    const response = await axios.post(`${API_BASE_URL}/keywords/accept-changes`, {
      ad_group_id: adGroupId
    });
    return response.data;
  },
  
  rejectChanges: async (adGroupId) => {
      const response = await axios.post(`${API_BASE_URL}/keywords/reject-changes`, {
        ad_group_id: adGroupId
      });
      return response.data;
    },

  bulkAction: async (action, keywordIds, field = null, value = null) => {
    const data = {
      action: action,
      keyword_ids: keywordIds
    };
    
    if (field && value !== null) {
      data.field = field;
      data.value = value;
    }
    
    const response = await axios.post(`${API_BASE_URL}/keywords/bulk-action`, data);
    return response.data;
  },

  pasteKeywords: async (adGroupId, pasteData, pasteType) => {
    const response = await axios.post(`${API_BASE_URL}/keywords/paste`, {
      ad_group_id: adGroupId,
      paste_data: pasteData,
      paste_type: pasteType
    });
    return response.data;
  },

  // DataForSeo
  getNewKeywords: async (params) => {
    const response = await axios.post(`${API_BASE_URL}/dataforseo/get-keywords`, params);
    return response.data;
  },

  applySerp: async (params) => {
    const response = await axios.post(`${API_BASE_URL}/dataforseo/apply-serp`, params);
    return response.data;
  },

  // Settings
  getSettings: async () => {
    const response = await axios.get(`${API_BASE_URL}/settings/get`);
    return response.data;
  },

  saveSettings: async (settings) => {
    const response = await axios.post(`${API_BASE_URL}/settings/save`, settings);
    return response.data;
  },

  // Check balance
  checkBalance: async () => {
    const response = await axios.get(`${API_BASE_URL}/dataforseo/check-balance`);
    return response.data;
  },
  
  restartApp: async () => {
    const response = await axios.post(`${API_BASE_URL}/settings/restart`);
    return response.data;
  }
};

export default api;