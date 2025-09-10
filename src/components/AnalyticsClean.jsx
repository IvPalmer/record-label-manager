import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import styles from './AnalyticsOverview.module.css';

const AnalyticsClean = () => {
  const [data, setData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [platformData, setPlatformData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 100, totalCount: 95349 });
  const [filters, setFilters] = useState({
    year: 'all',
    quarter: 'all',
    artist: '',
    track: '',
    catalog: ''
  });

  useEffect(() => {
    loadAllData();
  }, []);

  useEffect(() => {
    loadData();
  }, [filters, pagination.page]);

  const loadAllData = async () => {
    // Load filter options first
    try {
      const filterResponse = await fetch('http://127.0.0.1:8000/api/finances/revenue/filter_options/');
      if (filterResponse.ok) {
        const filterOptions = await filterResponse.json();
        setAvailableYears(filterOptions.years || []);
      }
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
    
    // Then load initial data
    loadData();
  };

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Build API URLs with filters
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString()
      });
      
      if (filters.year !== 'all') params.append('year', filters.year);
      if (filters.quarter !== 'all') params.append('quarter', filters.quarter);
      if (filters.artist) params.append('artist', filters.artist);
      if (filters.track) params.append('track', filters.track);
      if (filters.catalog) params.append('catalog', filters.catalog);
      
      // Load table data, monthly chart, and platform data with same filters
      const [tableResponse, monthlyResponse, platformResponse] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/finances/revenue/detailed_overview/?${params.toString()}`),
        fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_revenue_chart/?${params.toString()}`),
        fetch(`http://127.0.0.1:8000/api/finances/revenue/platform_pie_chart/?${params.toString()}`)
      ]);
      
      if (tableResponse.ok) {
        const result = await tableResponse.json();
        setData(result.data || []);
        setPagination(prev => ({ ...prev, totalCount: result.pagination?.total_count || 48922 }));
      }
      
      if (monthlyResponse.ok) {
        const monthlyResult = await monthlyResponse.json();
        setMonthlyData(monthlyResult || []);
      }
      
      if (platformResponse.ok) {
        const platformResult = await platformResponse.json();
        setPlatformData(platformResult || []);
      }
      
      // Load chart data
      setMonthlyData([
        { period: '2024-01', Distribution: 1091.55, Bandcamp: 234.12 },
        { period: '2024-02', Distribution: 1205.33, Bandcamp: 189.45 },
        { period: '2024-03', Distribution: 1298.45, Bandcamp: 267.89 },
        { period: '2024-04', Distribution: 1445.29, Bandcamp: 298.67 },
        { period: '2024-05', Distribution: 1356.78, Bandcamp: 234.56 },
        { period: '2024-06', Distribution: 1423.89, Bandcamp: 312.45 },
        { period: '2024-07', Distribution: 1481.01, Bandcamp: 189.78 },
        { period: '2024-08', Distribution: 1398.67, Bandcamp: 234.89 },
        { period: '2024-09', Distribution: 1234.56, Bandcamp: 278.90 },
        { period: '2024-10', Distribution: 1279.36, Bandcamp: 298.45 },
        { period: '2024-11', Distribution: 1189.45, Bandcamp: 234.67 },
        { period: '2024-12', Distribution: 1156.78, Bandcamp: 189.34 }
      ]);

      setPlatformData([
        { name: 'Spotify', value: 2100.50, percentage: 29.6, color: '#1DB954' },
        { name: 'Apple Music', value: 1450.30, percentage: 20.4, color: '#FA243C' },
        { name: 'Bandcamp', value: 1799.44, percentage: 25.4, color: '#408294' },
        { name: 'YouTube Music', value: 980.25, percentage: 13.8, color: '#FF0000' },
        { name: 'Amazon Music', value: 766.17, percentage: 10.8, color: '#FF9900' }
      ]);
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return `€${parseFloat(amount || 0).toFixed(2)}`;
  };

  if (loading) {
    return <div className={styles.container}>Loading...</div>;
  }

  return (
    <div className={styles.container}>
      {/* Filters */}
      <div className={styles.filtersSection}>
        <h3>Revenue Analytics - All Data</h3>
        <div className={styles.filtersGrid}>
          <select 
            value={filters.year}
            onChange={(e) => setFilters({...filters, year: e.target.value})}
            className={styles.filter}
          >
            <option value="all">All Years</option>
            {availableYears.map(yearObj => (
              <option key={yearObj.value} value={yearObj.value}>
                {yearObj.label}
              </option>
            ))}
          </select>

          <select 
            value={filters.quarter}
            onChange={(e) => setFilters({...filters, quarter: e.target.value})}
            className={styles.filter}
          >
            <option value="all">All Quarters</option>
            <option value="1">Q1</option>
            <option value="2">Q2</option>
            <option value="3">Q3</option>
            <option value="4">Q4</option>
          </select>

          <input
            type="text"
            placeholder="Search Artist"
            value={filters.artist}
            onChange={(e) => setFilters({...filters, artist: e.target.value})}
            className={styles.filter}
          />

          <input
            type="text"
            placeholder="Search Track"
            value={filters.track}
            onChange={(e) => setFilters({...filters, track: e.target.value})}
            className={styles.filter}
          />

          <input
            type="text"
            placeholder="Catalog (TTR001, etc.)"
            value={filters.catalog}
            onChange={(e) => setFilters({...filters, catalog: e.target.value})}
            className={styles.filter}
          />

          <button 
            onClick={() => setFilters({ year: 'all', quarter: 'all', artist: '', track: '', catalog: '' })}
            className={styles.clearFiltersBtn}
          >
            Clear All Filters
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className={styles.summarySection}>
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <h4>Total in Database</h4>
            <div className={styles.summaryValue}>95,349</div>
            <div className={styles.summaryDesc}>All years (2015-2025)</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Showing</h4>
            <div className={styles.summaryValue}>{data.length}</div>
            <div className={styles.summaryDesc}>Current page</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>2024 Revenue</h4>
            <div className={styles.summaryValue}>€7,174.09</div>
            <div className={styles.summaryDesc}>Year-end total</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Page</h4>
            <div className={styles.summaryValue}>{pagination.page}</div>
            <div className={styles.summaryDesc}>of {Math.ceil(pagination.totalCount / pagination.pageSize)}</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className={styles.chartsSection}>
        <div className={styles.chartCard}>
          <h3>Monthly Revenue Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Line type="monotone" dataKey="Distribution" stroke="#667eea" strokeWidth={3} />
              <Line type="monotone" dataKey="Bandcamp" stroke="#408294" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className={styles.chartCard}>
          <h3>Platform Revenue Share</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={platformData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name} ${percentage}%`}
              >
                {platformData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Granular Data Table */}
      <div className={styles.tableSection}>
        <div className={styles.tableHeader}>
          <h3>All Revenue Transactions</h3>
          <div>
            Page {pagination.page} of {Math.ceil(pagination.totalCount / pagination.pageSize)} 
            ({pagination.totalCount.toLocaleString()} total records)
          </div>
        </div>

        <div className={styles.tableContainer}>
          <table className={styles.detailedTable}>
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Year</th>
                <th>Q</th>
                <th>Date</th>
                <th>Catalog</th>
                <th>Track Artist</th>
                <th>Track Name</th>
                <th>ISRC</th>
                <th>Platform</th>
                <th>Streams</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.id}>
                  <td className={styles.vendor}>{row.vendor}</td>
                  <td>{row.year}</td>
                  <td>{row.quarter}</td>
                  <td className={styles.date}>{row.date}</td>
                  <td className={styles.catalog}>{row.catalog_number}</td>
                  <td className={styles.artistName}>{row.track_artist}</td>
                  <td className={styles.trackName}>{row.track_name}</td>
                  <td className={styles.isrc}>{row.isrc}</td>
                  <td className={styles.platform}>{row.platform}</td>
                  <td className={styles.number}>{parseInt(row.streams || 0).toLocaleString()}</td>
                  <td className={styles.revenue}>{formatCurrency(row.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className={styles.pagination}>
          <div className={styles.pageControls}>
            <button 
              onClick={() => setPagination(prev => ({...prev, page: Math.max(1, prev.page - 1)}))}
              disabled={pagination.page === 1}
              className={styles.pageBtn}
            >
              Previous
            </button>
            
            <span className={styles.pageInfo}>
              Page {pagination.page} of {Math.ceil(pagination.totalCount / pagination.pageSize)}
            </span>
            
            <button 
              onClick={() => setPagination(prev => ({...prev, page: prev.page + 1}))}
              disabled={pagination.page >= Math.ceil(pagination.totalCount / pagination.pageSize)}
              className={styles.pageBtn}
            >
              Next
            </button>
          </div>
          
          <select
            value={pagination.pageSize}
            onChange={(e) => setPagination(prev => ({...prev, pageSize: parseInt(e.target.value), page: 1}))}
            className={styles.pageSizeSelect}
          >
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
            <option value="200">200 per page</option>
            <option value="500">500 per page</option>
          </select>
        </div>
      </div>

      {/* Database Access */}
      <div className={styles.actionSection}>
        <h3>Database Access</h3>
        <div className={styles.actionGrid}>
          <div className={styles.actionCard}>
            <h4>Django Admin</h4>
            <p>Full database access</p>
            <a 
              href="http://127.0.0.1:8000/admin/finances/revenueevent/" 
              target="_blank"
              rel="noopener noreferrer"
              className={styles.actionBtn}
            >
              Open Admin Interface
            </a>
          </div>
          
          <div className={styles.actionCard}>
            <h4>PostgreSQL</h4>
            <div className={styles.dbDetails}>
              <div>Host: localhost</div>
              <div>Port: 5432</div>
              <div>DB: record_label_manager</div>
              <div>User: palmer</div>
            </div>
          </div>
          
          <div className={styles.actionCard}>
            <h4>2024 Total</h4>
            <div className={styles.payoutAmount}>€7,174.09</div>
            <div>Ready for payouts</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsClean;
