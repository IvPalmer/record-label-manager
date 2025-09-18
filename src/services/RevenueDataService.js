/**
 * Revenue Data Service
 * 
 * Handles all API communication for revenue data
 * Returns raw, unfiltered data from backend
 */

export class RevenueDataService {
  constructor(baseURL = 'http://127.0.0.1:8000/api/finances/revenue') {
    this.baseURL = baseURL;
  }

  /**
   * Fetch raw revenue events (all data, no filtering)
   */
  async fetchRawRevenueEvents() {
    try {
      const response = await fetch(`${this.baseURL}/detailed_overview/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error('Error fetching revenue events:', error);
      throw error;
    }
  }

  /**
   * Fetch raw data warehouse facts (DW layer)
   */
  async fetchDataWarehouseFacts() {
    try {
      // For now, we'll use the same endpoint but in the future this could be a separate DW endpoint
      const response = await fetch(`${this.baseURL}/detailed_overview/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      return result.data || [];
    } catch (error) {
      console.error('Error fetching DW facts:', error);
      throw error;
    }
  }

  /**
   * Fetch raw platform revenue data (all platforms, no aggregation)
   */
  async fetchPlatformRevenue() {
    try {
      const response = await fetch(`${this.baseURL}/platform_pie_chart/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching platform revenue:', error);
      throw error;
    }
  }

  /**
   * Fetch raw time series data (all platforms, no aggregation)
   */
  async fetchTimeSeriesRevenue() {
    try {
      const response = await fetch(`${this.baseURL}/monthly_revenue_chart/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching time series revenue:', error);
      throw error;
    }
  }

  /**
   * Fetch filter options (for dropdowns, etc.)
   */
  async fetchFilterOptions() {
    try {
      const response = await fetch(`${this.baseURL}/filter_options/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching filter options:', error);
      throw error;
    }
  }

  /**
   * Fetch all data needed for analytics dashboard
   */
  async fetchAllAnalyticsData() {
    try {
      const [
        revenueEvents,
        platformRevenue,
        timeSeriesRevenue,
        filterOptions
      ] = await Promise.all([
        this.fetchRawRevenueEvents(),
        this.fetchPlatformRevenue(),
        this.fetchTimeSeriesRevenue(),
        this.fetchFilterOptions()
      ]);

      return {
        revenueEvents,
        platformRevenue,
        timeSeriesRevenue,
        filterOptions
      };
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      throw error;
    }
  }
}

export default RevenueDataService;

