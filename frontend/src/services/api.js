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
      const { onProgress, ...requestParams } = params;
      
      // Если есть колбек прогресса и больше 10 слов, используем SSE
      if (onProgress && requestParams.keyword_ids.length >= 10) {
        return new Promise((resolve, reject) => {
          const eventSource = new EventSource(`${API_BASE_URL}/dataforseo/apply-serp-sse`);
          
          eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'progress') {
              onProgress(data.current, data.total, data.keyword);
            } else if (data.type === 'complete') {
              eventSource.close();
              resolve(data);
            } else if (data.type === 'error') {
              eventSource.close();
              reject(new Error(data.message));
            }
          };
          
          // Запускаем процесс
          axios.post(`${API_BASE_URL}/dataforseo/apply-serp`, requestParams)
            .catch(reject);
        });
      } else {
        // Обычный запрос для малого количества
        const response = await axios.post(`${API_BASE_URL}/dataforseo/apply-serp`, requestParams);
        return response.data;
      }
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
  },
  
  // Trash/Корзина методы
  getTrashKeywords: async (adGroupId) => {
    const response = await axios.get(`${API_BASE_URL}/keywords/trash/${adGroupId}`);
    return response.data;
  },

  restoreKeywords: async (keywordIds) => {
    const response = await axios.post(`${API_BASE_URL}/keywords/restore`, {
      keyword_ids: keywordIds
    });
    return response.data;
  },

  deleteKeywordsPermanently: async (keywordIds) => {
    const response = await axios.post(`${API_BASE_URL}/keywords/delete-permanently`, {
      keyword_ids: keywordIds
    });
    return response.data;
  },
  
  getCampaignSites: async () => {
    const response = await axios.get(`${API_BASE_URL}/settings/campaign-sites`);
    return response.data;
  },

  saveCampaignSites: async (campaigns) => {
    const response = await axios.post(`${API_BASE_URL}/settings/campaign-sites`, {
      campaigns: campaigns
    });
    return response.data;
  },

  getCampaignSite: async (campaignId) => {
    const response = await axios.get(`${API_BASE_URL}/settings/campaign-site/${campaignId}`);
    return response.data;
  },
  
  getCampaigns: async () => {
    const response = await axios.get(`${API_BASE_URL}/keywords/campaigns`);
    return response.data;
  }
};

export default api;