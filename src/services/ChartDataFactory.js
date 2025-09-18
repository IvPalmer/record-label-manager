/**
 * Chart Data Factory Service
 * 
 * Creates chart-ready data from raw API responses
 * Handles different chart types with consistent interfaces
 */

import { DataFilter, DataAggregator, PlatformColorManager } from './DataAggregationService.js';

export class ChartDataFactory {
  constructor(rawData = []) {
    this.rawData = rawData;
  }

  /**
   * Create pie chart data with top N + Others
   * @param {Object} options - Configuration options
   * @param {string} options.groupBy - Field to group by (e.g., 'platform', 'name')
   * @param {string} options.valueField - Field to sum for pie values (e.g., 'revenue', 'value')
   * @param {number} options.topN - Number of top items to show
   * @param {string[]} options.exclude - Platforms to exclude
   * @param {boolean} options.recalculatePercentages - Whether to recalculate percentages for filtered data
   */
  createPieChartData(options = {}) {
    const {
      groupBy = 'platform',
      valueField = 'revenue',
      topN = 10,
      exclude = [],
      recalculatePercentages = false
    } = options;

    // Filter out excluded platforms
    const filter = new DataFilter(this.rawData);
    const filteredData = exclude.length > 0 
      ? filter.byPlatform(exclude, true).getData()
      : this.rawData;

    // Group and aggregate data
    const aggregator = new DataAggregator(filteredData);
    const groupedData = aggregator.groupBy(groupBy, { [valueField]: 'sum' });

    // Get top N and create Others
    const sorted = groupedData.sort((a, b) => (b[valueField] || 0) - (a[valueField] || 0));
    const topItems = sorted.slice(0, topN);
    const remainingItems = sorted.slice(topN);
    
    let chartData = topItems.map(item => ({
      name: item[groupBy],
      value: item[valueField] || 0,
      [valueField]: item[valueField] || 0
    }));

    // Add Others if there are remaining items
    if (remainingItems.length > 0) {
      const othersTotal = remainingItems.reduce((sum, item) => sum + (item[valueField] || 0), 0);
      if (othersTotal > 0) {
        chartData.push({
          name: 'Others',
          value: othersTotal,
          [valueField]: othersTotal
        });
      }
    }

    // Calculate percentages
    const total = chartData.reduce((sum, item) => sum + (item.value || 0), 0);
    chartData = chartData.map(item => ({
      ...item,
      percentage: total > 0 ? Math.round((item.value / total * 100) * 10) / 10 : 0
    }));

    // Assign colors
    return PlatformColorManager.assignColors(chartData);
  }

  /**
   * Create line chart data with time series
   * @param {Object} options - Configuration options
   * @param {string} options.timeField - Field containing time data
   * @param {string[]} options.valueFields - Fields to create lines for
   * @param {string[]} options.exclude - Platforms to exclude
   * @param {number} options.topN - Number of top platforms to show (others aggregated)
   */
  createLineChartData(options = {}) {
    const {
      timeField = 'period',
      valueFields = ['revenue'],
      exclude = [],
      topN = null
    } = options;

    // If topN is specified, we need to aggregate others
    if (topN && valueFields.length === 1) {
      return this._createLineChartWithOthers(options);
    }

    // Filter out excluded platforms
    const filter = new DataFilter(this.rawData);
    const filteredData = exclude.length > 0 
      ? filter.byPlatform(exclude, true).getData()
      : this.rawData;

    // Group by time period
    const timeGroups = {};
    filteredData.forEach(item => {
      const timeKey = item[timeField];
      if (!timeGroups[timeKey]) {
        timeGroups[timeKey] = { [timeField]: timeKey };
      }
      
      // Add platform data to time period
      const platformKey = item.platform || item.name;
      if (platformKey && !exclude.includes(platformKey)) {
        valueFields.forEach(field => {
          if (!timeGroups[timeKey][platformKey]) {
            timeGroups[timeKey][platformKey] = 0;
          }
          timeGroups[timeKey][platformKey] += Number(item[field]) || 0;
        });
      }
    });

    return Object.values(timeGroups).sort((a, b) => 
      new Date(a[timeField]) - new Date(b[timeField])
    );
  }

  /**
   * Create line chart data with top N platforms + Others aggregation
   */
  _createLineChartWithOthers(options) {
    const {
      timeField = 'period',
      valueFields = ['revenue'],
      exclude = [],
      topN = 5
    } = options;

    // First, calculate which are the top N platforms overall
    const aggregator = new DataAggregator(this.rawData);
    const platformTotals = aggregator.groupBy('platform', { [valueFields[0]]: 'sum' });
    const topPlatforms = aggregator.getTopN(topN, valueFields[0], false)
      .map(item => item.platform)
      .filter(platform => !exclude.includes(platform));

    // Now process time series data
    const timeGroups = {};
    this.rawData.forEach(item => {
      const timeKey = item[timeField];
      const platformKey = item.platform || item.name;
      
      if (!timeGroups[timeKey]) {
        timeGroups[timeKey] = { [timeField]: timeKey };
        topPlatforms.forEach(platform => {
          timeGroups[timeKey][platform] = 0;
        });
        timeGroups[timeKey]['Others'] = 0;
      }

      if (platformKey && !exclude.includes(platformKey)) {
        const value = Number(item[valueFields[0]]) || 0;
        if (topPlatforms.includes(platformKey)) {
          timeGroups[timeKey][platformKey] += value;
        } else {
          timeGroups[timeKey]['Others'] += value;
        }
      }
    });

    return Object.values(timeGroups).sort((a, b) => 
      new Date(a[timeField]) - new Date(b[timeField])
    );
  }

  /**
   * Create KPI summary data
   * @param {Object} options - Configuration options
   */
  createKPISummary(options = {}) {
    const {
      revenueField = 'revenue',
      quantityField = 'quantity',
      artistField = 'artist_name',
      trackField = 'track_title'
    } = options;

    const aggregator = new DataAggregator(this.rawData);
    const totals = aggregator.getTotals([revenueField, quantityField]);

    // Get unique counts
    const uniqueArtists = new Set(this.rawData.map(item => item[artistField]).filter(Boolean)).size;
    const uniqueTracks = new Set(this.rawData.map(item => item[trackField]).filter(Boolean)).size;

    // Get top performer
    const topArtist = aggregator.groupBy(artistField, { [revenueField]: 'sum' })[0];

    return {
      totalRevenue: totals[revenueField] || 0,
      totalQuantity: totals[quantityField] || 0,
      totalTransactions: this.rawData.length,
      uniqueArtists,
      uniqueTracks,
      averagePerTransaction: this.rawData.length > 0 ? (totals[revenueField] || 0) / this.rawData.length : 0,
      topArtist: {
        name: topArtist?.[artistField] || 'N/A',
        revenue: topArtist?.[revenueField] || 0
      }
    };
  }

  /**
   * Create monthly overview table data
   * @param {Object} options - Configuration options
   */
  createMonthlyOverview(options = {}) {
    const {
      timeField = 'occurred_at',
      revenueField = 'revenue_base',
      quantityField = 'quantity'
    } = options;

    // Group by month
    const monthGroups = {};
    this.rawData.forEach(item => {
      const date = new Date(item[timeField]);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!monthGroups[monthKey]) {
        monthGroups[monthKey] = {
          month: monthKey,
          date: new Date(date.getFullYear(), date.getMonth(), 1),
          items: []
        };
      }
      monthGroups[monthKey].items.push(item);
    });

    // Calculate aggregations for each month
    return Object.values(monthGroups).map(monthData => {
      const aggregator = new DataAggregator(monthData.items);
      const totals = aggregator.getTotals([revenueField, quantityField]);
      
      // Calculate downloads vs streams
      const downloads = monthData.items
        .filter(item => item.platform === 'Bandcamp' || (item.store && item.store.toLowerCase().includes('beatport')))
        .reduce((sum, item) => sum + (Number(item[quantityField]) || 0), 0);
      
      const streams = totals[quantityField] - downloads;

      // Get top platforms for this month
      const platformAgg = aggregator.groupBy('platform', { [revenueField]: 'sum' });
      const topPlatforms = platformAgg
        .sort((a, b) => (b[revenueField] || 0) - (a[revenueField] || 0))
        .slice(0, 3);

      return {
        month: monthData.month,
        month_name: monthData.date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
        total_revenue: totals[revenueField] || 0,
        total_transactions: monthData.items.length,
        total_downloads: downloads,
        total_streams: streams,
        unique_artists: new Set(monthData.items.map(item => item.artist_name).filter(Boolean)).size,
        unique_tracks: new Set(monthData.items.map(item => item.track_title).filter(Boolean)).size,
        top_platforms: topPlatforms.map(platform => ({
          name: platform.platform,
          revenue: platform[revenueField],
          percentage: totals[revenueField] > 0 ? Math.round((platform[revenueField] / totals[revenueField] * 100) * 10) / 10 : 0
        }))
      };
    }).sort((a, b) => new Date(b.month) - new Date(a.month));
  }
}

export default ChartDataFactory;

