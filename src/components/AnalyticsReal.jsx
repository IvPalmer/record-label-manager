import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import styles from './AnalyticsOverview.module.css';

const AnalyticsReal = () => {
  const [data, setData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [platformData, setPlatformData] = useState([]);
  const [availableYears, setAvailableYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 100, totalCount: 0 });
  const [filters, setFilters] = useState({
    year: 'all',
    quarter: 'all',
    artist: '',
    track: '',
    catalog: ''
  });

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    loadData();
  }, [filters, pagination.page]);

  const loadFilterOptions = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/finances/revenue/filter_options/');
      if (response.ok) {
        const options = await response.json();
        setAvailableYears(options.years || []);
      }
    } catch (error) {
      console.log('Using fallback years');
      setAvailableYears([
        { value: '2025', label: '2025' },
        { value: '2024', label: '2024' },
        { value: '2023', label: '2023' },
        { value: '2022', label: '2022' },
        { value: '2021', label: '2021' },
        { value: '2020', label: '2020' },
        { value: '2019', label: '2019' },
        { value: '2018', label: '2018' },
        { value: '2017', label: '2017' },
        { value: '2016', label: '2016' },
        { value: '2015', label: '2015' }
      ]);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build filter parameters
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString()
      });
      
      if (filters.year !== 'all') params.append('year', filters.year);
      if (filters.quarter !== 'all') params.append('quarter', filters.quarter);
      if (filters.artist) params.append('artist', filters.artist);
      if (filters.track) params.append('track', filters.track);
      if (filters.catalog) params.append('catalog', filters.catalog);
      
      // Load table data
      const tableResponse = await fetch(`http://127.0.0.1:8000/api/finances/revenue/detailed_overview/?${params.toString()}`);
      
      if (tableResponse.ok) {
        const result = await tableResponse.json();
        setData(result.data || []);
        setPagination(prev => ({ ...prev, totalCount: result.pagination?.total_count || 0 }));
      } else {
        setError('Failed to load data from API');
        setData([]);
      }
      
      // Load chart data with same filters (without pagination)
      const chartParams = new URLSearchParams();
      if (filters.year !== 'all') chartParams.append('year', filters.year);
      if (filters.quarter !== 'all') chartParams.append('quarter', filters.quarter);
      if (filters.artist) chartParams.append('artist', filters.artist);
      if (filters.track) chartParams.append('track', filters.track);
      if (filters.catalog) chartParams.append('catalog', filters.catalog);
      
      try {
        const [monthlyResponse, platformResponse] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_revenue_chart/?${chartParams.toString()}`),
          fetch(`http://127.0.0.1:8000/api/finances/revenue/platform_pie_chart/?${chartParams.toString()}`)
        ]);
        
        if (monthlyResponse.ok) {
          const monthlyResult = await monthlyResponse.json();
          setMonthlyData(monthlyResult || []);
        }
        
        if (platformResponse.ok) {
          const platformResult = await platformResponse.json();
          setPlatformData(platformResult || []);
        }
      } catch (chartError) {
        console.log('Chart data loading failed, using defaults');
      }
      
    } catch (error) {
      setError(`Error: ${error.message}`);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return `€${parseFloat(amount || 0).toFixed(2)}`;
  };

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.filtersSection}>
          <h3>Analytics Error</h3>
          <p>{error}</p>
          <p>Backend URL: http://127.0.0.1:8000/</p>
          <p>Frontend URL: http://localhost:5175/</p>
          <a href="http://127.0.0.1:8000/admin/" target="_blank">Try Django Admin</a>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.filtersSection}>
          <h3>Loading Real Data...</h3>
          <p>Connecting to database with 95,349 records</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Filters */}
      <div className={styles.filtersSection}>
        <h3>Revenue Analytics - Real Data (95,349 records)</h3>
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
            placeholder="Catalog (TTR019, etc.)"
            value={filters.catalog}
            onChange={(e) => setFilters({...filters, catalog: e.target.value})}
            className={styles.filter}
          />

          <button 
            onClick={() => setFilters({ year: 'all', quarter: 'all', artist: '', track: '', catalog: '' })}
            className={styles.clearFiltersBtn}
          >
            Clear All
          </button>
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
          <h3>All Revenue Transactions</h3>
          <div>
            Showing {data.length} of {pagination.totalCount.toLocaleString()} 
            (Page {pagination.page} of {Math.ceil(pagination.totalCount / pagination.pageSize)})
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
                  <td className={styles.revenue}>
                    {row.vendor === 'Bandcamp' && row.currency === 'USD' ? 
                      `$${parseFloat(row.original_amount || row.revenue).toFixed(2)}` : 
                      formatCurrency(row.revenue)
                    }
                  </td>
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

      {/* Summary */}
      <div className={styles.summarySection}>
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <h4>Database Total</h4>
            <div className={styles.summaryValue}>95,349</div>
            <div className={styles.summaryDesc}>All years (2015-2025)</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Filtered Results</h4>
            <div className={styles.summaryValue}>{pagination.totalCount.toLocaleString()}</div>
            <div className={styles.summaryDesc}>Matching criteria</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Current Page</h4>
            <div className={styles.summaryValue}>{data.length}</div>
            <div className={styles.summaryDesc}>Records shown</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Bandcamp Revenue</h4>
            <div className={styles.summaryValue}>$29,674</div>
            <div className={styles.summaryDesc}>Real sales payouts</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsReal;