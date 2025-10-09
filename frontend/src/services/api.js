// frontend/src/services/api.js - ИСПРАВЛЕНО: добавлена функция getSerpLogs
import axios from 'axios';

const API_BASE_URL = '/api';

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
    
    console.log('🚀 applySerp called with', requestParams.keyword_ids.length, 'keywords');
    
    try {
      const keywordsCount = requestParams.keyword_ids.length;
      
      // Для 1 слова - обычный запрос без SSE (быстро)
      if (keywordsCount === 1) {
        const response = await axios.post(`${API_BASE_URL}/dataforseo/apply-serp`, requestParams);
        console.log('📨 Response:', response.data);
        return response.data;
      }
      
      // Для 2+ слов - Task-версия с SSE
      const startResponse = await axios.post(`${API_BASE_URL}/dataforseo/apply-serp`, requestParams);
      
      console.log('📨 Start response:', startResponse.data);
      
      if (!startResponse.data.success) {
        throw new Error(startResponse.data.error || 'Failed to start SERP analysis');
      }
      
      if (startResponse.data.use_sse && startResponse.data.task_id) {
        return new Promise((resolve, reject) => {
          const task_id = startResponse.data.task_id;
          const sseUrl = `${API_BASE_URL}/dataforseo/apply-serp-sse?task_id=${task_id}`;
          
          console.log('🔄 Connecting to SSE:', sseUrl);
          
          const eventSource = new EventSource(sseUrl);
          let isResolved = false;
          
          const timeout = setTimeout(() => {
            if (!isResolved) {
              console.warn('⏱️ SSE timeout');
              eventSource.close();
              reject(new Error('SSE connection timeout'));
            }
          }, 300000);
          
          eventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              console.log('📡 SSE event:', data.type);
              
              if (data.type === 'progress') {
                if (onProgress) {
                  onProgress(data.current, data.total, data.keyword);
                }
              } else if (data.type === 'complete') {
                clearTimeout(timeout);
                eventSource.close();
                isResolved = true;
                resolve({
                  success: true,
                  message: data.message || 'SERP анализ завершен',
                  ...data.result
                });
              } else if (data.type === 'error') {
                clearTimeout(timeout);
                eventSource.close();
                isResolved = true;
                reject(new Error(data.message || 'SERP analysis failed'));
              }
            } catch (err) {
              console.error('❌ Error parsing SSE event:', err);
            }
          };
          
          eventSource.onerror = (error) => {
            console.error('❌ SSE connection error:', error);
            if (!isResolved) {
              clearTimeout(timeout);
              eventSource.close();
              isResolved = true;
              resolve({
                success: true,
                message: 'SERP анализ запущен (статус неизвестен)',
                warning: 'Не удалось отследить прогресс'
              });
            }
          };
        });
      } else {
        return startResponse.data;
      }
      
    } catch (error) {
      console.error('❌ applySerp error:', error);
      throw error;
    }
  },

  // SERP Logs - УЛУЧШЕННАЯ ФУНКЦИЯ с фильтрацией
  getSerpLogs: async (params = {}) => {
    try {
      const { limit = 50, keywordId = null, keywordIds = null, latestOnly = false } = params;
      
      let url = `${API_BASE_URL}/dataforseo/serp-logs?limit=${limit}`;
      
      if (keywordId) {
        url += `&keyword_id=${keywordId}`;
      }
      
      if (keywordIds && Array.isArray(keywordIds) && keywordIds.length > 0) {
        url += `&keyword_ids=${keywordIds.join(',')}`;
      }
      
      if (latestOnly) {
        url += `&latest_only=true`;
      }
      
      const response = await axios.get(url);
      return response.data;
    } catch (error) {
      console.error('❌ getSerpLogs error:', error);
      throw error;
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

  checkBalance: async () => {
    const response = await axios.get(`${API_BASE_URL}/dataforseo/check-balance`);
    return response.data;
  },
  
  restartApp: async () => {
    const response = await axios.post(`${API_BASE_URL}/settings/restart`);
    return response.data;
  },
  
  // Trash/Корзина
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
  
  // Campaign sites
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
  },
  
  // Получить список конкурентов
  getCompetitors: async () => {
    const response = await axios.get(`${API_BASE_URL}/competitors/list`);
    return response.data;
  },

  // Получить статистику конкурентов
  getCompetitorsStats: async () => {
    const response = await axios.get(`${API_BASE_URL}/competitors/stats`);
    return response.data;
  },

  // Добавить нового конкурента
  addCompetitor: async (competitorData) => {
    const response = await axios.post(`${API_BASE_URL}/competitors/add`, competitorData);
    return response.data;
  },

  // Обновить данные конкурента
  updateCompetitor: async (id, field, value) => {
    const response = await axios.post(`${API_BASE_URL}/competitors/update`, {
      id,
      field,
      value
    });
    return response.data;
  },

  // Удалить конкурентов
  deleteCompetitors: async (ids) => {
    const response = await axios.post(`${API_BASE_URL}/competitors/delete`, {
      ids
    });
    return response.data;
  },

  // Пересчитать конкурентность
  updateCompetitiveness: async () => {
    const response = await axios.post(`${API_BASE_URL}/competitors/update-competitiveness`);
    return response.data;
  }
};

export default api;