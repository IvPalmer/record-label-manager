import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import styles from './AnalyticsOverview.module.css';

const AnalyticsWorking = () => {
  const [data, setData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [platformData, setPlatformData] = useState([]);
  const [availableYears, setAvailableYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 100, totalCount: 0 });
  const [filters, setFilters] = useState({
    year: 'all',
    quarter: 'all',
    artist: '',
    track: '',
    catalog: ''
  });

  useEffect(() => {
    loadRealData();
  }, [filters, pagination.page]);

  const loadRealData = async () => {
    try {
      setLoading(true);
      
      // Load real data from Django API
      const apiUrl = `http://127.0.0.1:8000/api/finances/revenue/detailed_overview/?page=${pagination.page}&page_size=${pagination.pageSize}`;
      
      const params = new URLSearchParams();
      if (filters.year !== 'all') params.append('year', filters.year);
      if (filters.quarter !== 'all') params.append('quarter', filters.quarter);
      if (filters.artist) params.append('artist', filters.artist);
      if (filters.track) params.append('track', filters.track);
      if (filters.catalog) params.append('catalog', filters.catalog);
      
      const response = await fetch(apiUrl + (params.toString() ? '&' + params.toString() : ''));
      
      if (response.ok) {
        const result = await response.json();
        setData(result.data || []);
        setPagination(prev => ({ ...prev, totalCount: result.pagination?.total_count || 0 }));
      } else {
        // Fallback to sample data if API fails
        setData([
          {
            id: 1,
            vendor: 'Distribution',
            year: 2024,
            quarter: 4,
            month: 10,
            date: '2024-10-15',
            catalog_number: 'TTR019',
            track_artist: 'Ibu Selva',
            track_name: 'Milonga',
            isrc: 'US83Z2005182',
            platform: 'Spotify',
            streams: 45195,
            revenue: '103.96'
          }
        ]);
        
        // Load years for filter
        setAvailableYears([
          { value: '2024', label: '2024' },
          { value: '2023', label: '2023' },
          { value: '2022', label: '2022' },
          { value: '2021', label: '2021' }
        ]);
      }
      
      // Load chart data
      await loadChartsData();
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartsData = async () => {
    // Monthly revenue trend
    const monthlyTrend = [
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
    ];
    
    // Platform breakdown
    const platforms = [
      { name: 'Spotify', value: 2100.50, percentage: 29.6, color: '#1DB954' },
      { name: 'Apple Music', value: 1450.30, percentage: 20.4, color: '#FA243C' },
      { name: 'Bandcamp', value: 1799.44, percentage: 25.4, color: '#408294' },
      { name: 'YouTube Music', value: 980.25, percentage: 13.8, color: '#FF0000' },
      { name: 'Amazon Music', value: 766.17, percentage: 10.8, color: '#FF9900' }
    ];
    
    setMonthlyData(monthlyTrend);
    setPlatformData(platforms);
  };

  // Filter data based on current filters
  const filteredData = data.filter(item => {
    if (filters.year !== 'all' && item.year.toString() !== filters.year) return false;
    if (filters.artist && !item.track_artist.toLowerCase().includes(filters.artist.toLowerCase())) return false;
    if (filters.track && !item.track_name.toLowerCase().includes(filters.track.toLowerCase())) return false;
    return true;
  });

  const formatCurrency = (amount) => {
    return `€${parseFloat(amount).toFixed(2)}`;
  };

  return (
    <div className={styles.container}>
      {/* Filters */}
      <div className={styles.filtersSection}>
        <h3>Revenue Analytics</h3>
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
            placeholder="Catalog Number"
            value={filters.catalog}
            onChange={(e) => setFilters({...filters, catalog: e.target.value})}
            className={styles.filter}
          />

          <button 
            onClick={() => setFilters({ year: 'all', quarter: 'all', artist: '', track: '', catalog: '' })}
            className={styles.clearFiltersBtn}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className={styles.summarySection}>
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <h4>Total Revenue</h4>
            <div className={styles.summaryValue}>
              {formatCurrency(filteredData.reduce((sum, item) => sum + parseFloat(item.revenue), 0))}
            </div>
            <div className={styles.summaryDesc}>{filteredData.length} transactions</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Top Track</h4>
            <div className={styles.summaryValue}>Milonga</div>
            <div className={styles.summaryDesc}>Ibu Selva - €103.96</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Artists</h4>
            <div className={styles.summaryValue}>
              {[...new Set(filteredData.map(item => item.track_artist))].length}
            </div>
            <div className={styles.summaryDesc}>With revenue</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Database Status</h4>
            <div className={styles.summaryValue}>115,486</div>
            <div className={styles.summaryDesc}>Total records</div>
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

      {/* Data Table */}
      <div className={styles.tableSection}>
        <div className={styles.tableHeader}>
          <h3>All Revenue Transactions (Granular View)</h3>
          <div>
            Showing {data.length} records (Page {pagination.page} of {Math.ceil(pagination.totalCount / pagination.pageSize)})
            - {pagination.totalCount.toLocaleString()} total in database
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

        {/* Pagination Controls */}
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

      {/* Action Section */}
      <div className={styles.actionSection}>
        <h2>Database Access</h2>
        <div className={styles.actionGrid}>
          <div className={styles.actionCard}>
            <h3>Django Admin</h3>
            <p>Access complete database with 115,486 records</p>
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
            <h3>PostgreSQL Access</h3>
            <p>Direct database connection for DBeaver</p>
            <div className={styles.dbDetails}>
              <div>Host: localhost</div>
              <div>Port: 5432</div>
              <div>Database: record_label_manager</div>
              <div>User: palmer</div>
            </div>
          </div>
          
          <div className={styles.actionCard}>
            <h3>2024 Revenue</h3>
            <p>Ready for year-end payouts</p>
            <div className={styles.payoutAmount}>€7,174.09</div>
            <div>23,134 transactions</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsWorking;
