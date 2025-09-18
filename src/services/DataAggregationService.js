/**
 * Data Aggregation Service
 * 
 * Handles all data filtering, aggregation, and transformation for charts
 * Follows OOP principles for clean, reusable code
 */

export class DataFilter {
  constructor(data = []) {
    this.data = data;
  }

  /**
   * Filter by platform(s)
   * @param {string|string[]} platforms - Platform name(s) to include/exclude
   * @param {boolean} exclude - Whether to exclude the platforms
   */
  byPlatform(platforms, exclude = false) {
    const platformArray = Array.isArray(platforms) ? platforms : [platforms];
    const filtered = this.data.filter(item => {
      const match = platformArray.some(platform => 
        item.platform?.toLowerCase() === platform.toLowerCase() ||
        item.name?.toLowerCase() === platform.toLowerCase()
      );
      return exclude ? !match : match;
    });
    return new DataFilter(filtered);
  }

  /**
   * Filter by date range
   * @param {Date|string} startDate 
   * @param {Date|string} endDate 
   */
  byDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const filtered = this.data.filter(item => {
      const itemDate = new Date(item.occurred_at || item.date || item.period);
      return itemDate >= start && itemDate <= end;
    });
    return new DataFilter(filtered);
  }

  /**
   * Filter by year
   * @param {number} year 
   */
  byYear(year) {
    const filtered = this.data.filter(item => {
      const itemDate = new Date(item.occurred_at || item.date || item.period);
      return itemDate.getFullYear() === year;
    });
    return new DataFilter(filtered);
  }

  /**
   * Get the filtered data
   */
  getData() {
    return this.data;
  }
}

export class DataAggregator {
  constructor(data = []) {
    this.data = data;
  }

  /**
   * Group data by a field and aggregate values
   * @param {string} groupBy - Field to group by
   * @param {Object} aggregations - Aggregation functions { field: 'sum'|'count'|'avg'|'max'|'min' }
   */
  groupBy(groupBy, aggregations = {}) {
    const groups = {};
    
    this.data.forEach(item => {
      const key = item[groupBy];
      if (!groups[key]) {
        groups[key] = { [groupBy]: key, _items: [] };
      }
      groups[key]._items.push(item);
    });

    // Apply aggregations
    Object.values(groups).forEach(group => {
      Object.entries(aggregations).forEach(([field, aggType]) => {
        const values = group._items.map(item => Number(item[field]) || 0);
        
        switch (aggType) {
          case 'sum':
            group[field] = values.reduce((sum, val) => sum + val, 0);
            break;
          case 'count':
            group[field] = values.length;
            break;
          case 'avg':
            group[field] = values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
            break;
          case 'max':
            group[field] = Math.max(...values);
            break;
          case 'min':
            group[field] = Math.min(...values);
            break;
          default:
            group[field] = values[0]; // First value as fallback
        }
      });
      delete group._items; // Clean up
    });

    return Object.values(groups);
  }

  /**
   * Get top N items by a field value
   * @param {number} n - Number of top items
   * @param {string} field - Field to sort by
   * @param {boolean} ascending - Sort order
   */
  getTopN(n, field, ascending = false) {
    const sorted = [...this.data].sort((a, b) => {
      const aVal = Number(a[field]) || 0;
      const bVal = Number(b[field]) || 0;
      return ascending ? aVal - bVal : bVal - aVal;
    });
    return sorted.slice(0, n);
  }

  /**
   * Calculate totals for specified fields
   * @param {string[]} fields - Fields to calculate totals for
   */
  getTotals(fields) {
    return fields.reduce((totals, field) => {
      totals[field] = this.data.reduce((sum, item) => sum + (Number(item[field]) || 0), 0);
      return totals;
    }, {});
  }
}

export class PlatformColorManager {
  static colors = {
    'Spotify': '#1DB954',           // Spotify green
    'Apple Music': '#C0C0C0',       // Apple Music silver
    'YouTube': '#FF0000',           // YouTube red
    'YouTube Music': '#B71C1C',     // Darker red for YouTube Music
    'TikTok': '#FF6B00',           // TikTok orange
    'Beatport': '#01FF95',         // Beatport bright green
    'Amazon Music': '#FF9F00',      // Amazon orange
    'Bandcamp': '#408294',         // Bandcamp teal
    'Deezer': '#A238FF',           // Deezer purple
    'Tidal': '#000000',            // Tidal black
    'SoundCloud': '#FF5500',       // SoundCloud orange
    'Traxsource': '#FF6B35',       // Traxsource orange-red
    'Juno Download': '#4ECDC4',    // Juno teal
    'Qobuz': '#5A67D8',           // Qobuz blue
    'Shazam': '#0066FF',          // Shazam blue
    'Instagram': '#E4405F',        // Instagram pink
    'Facebook': '#1877F2',         // Facebook blue
    'Others': '#9CA3AF'            // Gray for others
  };

  static getColor(platformName) {
    return this.colors[platformName] || '#9CA3AF';
  }

  static assignColors(data, nameField = 'name') {
    return data.map(item => ({
      ...item,
      color: this.getColor(item[nameField])
    }));
  }
}

