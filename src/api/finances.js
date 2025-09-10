import { apiClient } from './client';

export const financesApi = {
  getDetailedOverview: async (filters = {}, page = 1, pageSize = 50) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== 'all') {
        params.append(key, value);
      }
    });
    
    const response = await apiClient.get(`/api/finances/revenue/detailed_overview/?${params}`);
    return response.data;
  },

  getMonthlyChart: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== 'all') {
        params.append(key, value);
      }
    });
    
    const response = await apiClient.get(`/api/finances/revenue/monthly_revenue_chart/?${params}`);
    return response.data;
  },

  getPlatformChart: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== 'all') {
        params.append(key, value);
      }
    });
    
    const response = await apiClient.get(`/api/finances/revenue/platform_pie_chart/?${params}`);
    return response.data;
  },

  getFilterOptions: async () => {
    const response = await apiClient.get('/api/finances/revenue/filter_options/');
    return response.data;
  }
};