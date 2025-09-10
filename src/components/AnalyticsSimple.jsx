import React, { useState, useEffect } from 'react';
import { financesApi } from '../api/finances';
import styles from './AnalyticsOverview.module.css';

const AnalyticsSimple = () => {
  const [data, setData] = useState([]);
  const [allYears, setAllYears] = useState([]);
  const [filters, setFilters] = useState({
    year: 'all',
    artist: '',
    track: ''
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (allYears.length > 0) {
      loadRevenueData();
    }
  }, [filters]);

  const loadInitialData = async () => {
    try {
      const filterOptions = await financesApi.getFilterOptions();
      setAllYears(filterOptions.years || []);
    } catch (error) {
      console.error('Failed to load filter options:', error);
      setAllYears([{ value: '2024', label: '2024' }]);
    }
  };

  const loadRevenueData = async () => {
    try {
      setLoading(true);
      const result = await financesApi.getDetailedOverview(filters, 1, 100);
      setData(result.data || []);
    } catch (error) {
      console.error('Failed to load revenue data:', error);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return `€${parseFloat(amount).toFixed(2)}`;
  };

  if (loading) {
    return <div className={styles.container}>Loading real data...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.filtersSection}>
        <h3>Filters</h3>
        <div className={styles.filtersGrid}>
          <select 
            value={filters.year}
            onChange={(e) => setFilters({...filters, year: e.target.value})}
            className={styles.filter}
          >
            <option value="all">All Years</option>
            {allYears.map(yearObj => (
              <option key={yearObj.value} value={yearObj.value}>
                {yearObj.label}
              </option>
            ))}
          </select>

          <input
            type="text"
            placeholder="Artist Name"
            value={filters.artist}
            onChange={(e) => setFilters({...filters, artist: e.target.value})}
            className={styles.filter}
          />

          <input
            type="text"
            placeholder="Track Name"
            value={filters.track}
            onChange={(e) => setFilters({...filters, track: e.target.value})}
            className={styles.filter}
          />

          <button 
            onClick={() => setFilters({ year: 'all', artist: '', track: '' })}
            className={styles.clearFiltersBtn}
          >
            Clear All
          </button>
        </div>
      </div>

      <div className={styles.tableSection}>
        <div className={styles.tableHeader}>
          <h3>Revenue Overview</h3>
          <div>Showing {data.length} records</div>
        </div>

        <div className={styles.tableContainer}>
          <table className={styles.detailedTable}>
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Year</th>
                <th>Q</th>
                <th>Month</th>
                <th>Date</th>
                <th>Catalog</th>
                <th>Release Name</th>
                <th>Track Artist</th>
                <th>Track Name</th>
                <th>ISRC</th>
                <th>Platform</th>
                <th>Downloads</th>
                <th>Streams</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.id}>
                  <td>{row.vendor}</td>
                  <td>{row.year}</td>
                  <td>{row.quarter}</td>
                  <td>{row.month}</td>
                  <td>{row.date}</td>
                  <td>{row.catalog_number}</td>
                  <td>{row.release_name}</td>
                  <td>{row.track_artist}</td>
                  <td>{row.track_name}</td>
                  <td>{row.isrc}</td>
                  <td>{row.platform}</td>
                  <td>{row.downloads}</td>
                  <td>{row.streams.toLocaleString()}</td>
                  <td>{formatCurrency(row.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={styles.summarySection}>
        <h3>Summary</h3>
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <h4>Total Revenue</h4>
            <div className={styles.summaryValue}>
              {formatCurrency(data.reduce((sum, item) => sum + parseFloat(item.revenue || 0), 0))}
            </div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Records Shown</h4>
            <div className={styles.summaryValue}>{data.length}</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Artists</h4>
            <div className={styles.summaryValue}>
              {[...new Set(data.map(item => item.track_artist))].length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsSimple;
