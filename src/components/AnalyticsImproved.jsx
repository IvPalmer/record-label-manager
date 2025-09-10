import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import styles from './AnalyticsOverview.module.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, info: null };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Analytics error:', error, info);
    this.setState({ info });
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24 }}>
          <h3>Analytics failed to render</h3>
          <p>Try changing filters or reloading. The error has been logged to the console.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

// The main analytics UI and data logic. Wrapped by ErrorBoundary below so
// render-time issues surface as a friendly message instead of a blank page.
const AnalyticsContent = () => {
  const [data, setData] = useState([]);
  const [quarterlyData, setQuarterlyData] = useState([]);
  const [platformData, setPlatformData] = useState([]);
  const [kpiData, setKpiData] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 100, totalCount: 0 });
  
  // Separate applied filters from draft filters
  const [appliedFilters, setAppliedFilters] = useState({
    year: 'all',
    quarter: 'all',
    artist: '',
    track: '',
    catalog: ''
  });
  
  const [draftFilters, setDraftFilters] = useState({
    year: 'all',
    quarter: 'all',
    artist: '',
    track: '',
    catalog: ''
  });

  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Only trigger data loading when appliedFilters or pagination changes
  useEffect(() => {
    loadData();
    loadKpiData();
  }, [appliedFilters, pagination.page]);

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
        { value: '2024', label: '2024' },
        { value: '2023', label: '2023' },
        { value: '2022', label: '2022' },
        { value: '2021', label: '2021' },
        { value: '2020', label: '2020' },
        { value: '2019', label: '2019' },
        { value: '2018', label: '2018' },
        { value: '2017', label: '2017' }
      ]);
    }
  };

  const loadKpiData = async () => {
    try {
      const params = new URLSearchParams();
      if (appliedFilters.year !== 'all') params.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') params.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) params.append('artist', appliedFilters.artist);
      if (appliedFilters.track) params.append('track', appliedFilters.track);
      if (appliedFilters.catalog) params.append('catalog', appliedFilters.catalog);

      const response = await fetch(`http://127.0.0.1:8000/api/finances/revenue/kpi_summary/?${params.toString()}`);
      
      if (response.ok) {
        const result = await response.json();
        setKpiData(result);
      }
    } catch (error) {
      console.log('KPI data loading failed');
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build filter parameters using appliedFilters
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString()
      });
      
      if (appliedFilters.year !== 'all') params.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') params.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) params.append('artist', appliedFilters.artist);
      if (appliedFilters.track) params.append('track', appliedFilters.track);
      if (appliedFilters.catalog) params.append('catalog', appliedFilters.catalog);
      
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
      if (appliedFilters.year !== 'all') chartParams.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') chartParams.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) chartParams.append('artist', appliedFilters.artist);
      if (appliedFilters.track) chartParams.append('track', appliedFilters.track);
      if (appliedFilters.catalog) chartParams.append('catalog', appliedFilters.catalog);
      
      try {
        const [monthlyResponse, platformResponse] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_revenue_chart/?${chartParams.toString()}`),
          fetch(`http://127.0.0.1:8000/api/finances/revenue/platform_pie_chart/?${chartParams.toString()}`)
        ]);
        
        if (monthlyResponse.ok) {
          const quarterlyResult = await monthlyResponse.json();
          setQuarterlyData(quarterlyResult || []);
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

  // Apply filters function
  const applyFilters = () => {
    setAppliedFilters({ ...draftFilters });
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to page 1 when applying filters
  };

  // Clear filters function
  const clearFilters = () => {
    const clearedFilters = { year: 'all', quarter: 'all', artist: '', track: '', catalog: '' };
    setDraftFilters(clearedFilters);
    setAppliedFilters(clearedFilters);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const formatCurrency = (amount) => {
    const n = Number(amount);
    if (!isFinite(n)) return '';
    return `€${n.toFixed(2)}`;
  };

  const formatNumber = (num) => {
    return parseInt(num || 0).toLocaleString();
  };

  // Derive available platform keys from chart data
  // IMPORTANT: Hooks must not be conditional. Keep useMemo above any early returns.
  const allPlatformKeys = React.useMemo(() => {
    const set = new Set();
    (quarterlyData || []).forEach(row => {
      Object.keys(row).forEach(k => {
        if (
          k !== 'period' &&
          typeof k === 'string' &&
          row[k] !== null && row[k] !== undefined &&
          // filter out accidental numeric keys
          isNaN(Number(k))
        ) {
          set.add(k);
        }
      });
    });
    return Array.from(set);
  }, [quarterlyData]);

  const distributionKeys = allPlatformKeys.filter(k => k.toLowerCase() !== 'bandcamp');
  const hasBandcamp = allPlatformKeys.includes('Bandcamp');

  // Trim distribution chart to first month where distribution has any value to avoid long empty leading span
  const distributionChartData = React.useMemo(() => {
    if (!quarterlyData || quarterlyData.length === 0) return [];
    const firstIdx = quarterlyData.findIndex(row => distributionKeys.some(k => Number(row[k]) > 0));
    if (firstIdx === -1) return [];
    return quarterlyData.slice(firstIdx);
  }, [quarterlyData, distributionKeys]);

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.filtersSection}>
          <h3>Connection Error</h3>
          <p>{error}</p>
          <p>Backend: http://127.0.0.1:8000/</p>
          <p>Frontend: http://localhost:5174/</p>
          <a href="http://127.0.0.1:8000/admin/" target="_blank" rel="noopener noreferrer">Django Admin</a>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.filtersSection}>
          <h3>Loading Analytics</h3>
          <p>Connecting to database with 17,931 records</p>
        </div>
      </div>
    );
  }

  // Simple color palette for multiple distribution platforms
  const palette = ['#667eea', '#1DB954', '#FA243C', '#FF9900', '#FF0000', '#4ECDC4', '#A78BFA', '#F59E0B'];

  const safeEuro = (v) => {
    const n = Number(v);
    if (!isFinite(n)) return '';
    return `€${Math.round(n)}`;
  };

  // Helper: take top N by value and group remainder into "Others"
  const topNWithOthers = (items, n, exclude = []) => {
    const filtered = (items || []).filter(i => i && !exclude.includes(i.name));
    const sorted = [...filtered].sort((a, b) => (b.value || 0) - (a.value || 0));
    const top = sorted.slice(0, n);
    const rest = sorted.slice(n);
    const othersTotal = rest.reduce((sum, it) => sum + (Number(it.value) || 0), 0);
    const othersPerc = rest.reduce((sum, it) => sum + (Number(it.percentage) || 0), 0);
    if (othersTotal > 0) {
      top.push({ name: 'Others', value: othersTotal, percentage: Math.round(othersPerc * 10) / 10, color: '#9CA3AF' });
    }
    return top;
  };

  return (
    <div className={styles.container}>
      {/* Filters */}
      <div className={styles.filtersSection}>
        <h3>Revenue Analytics ({pagination.totalCount.toLocaleString()} records)</h3>
        <div className={styles.filtersGrid}>
          <select 
            value={draftFilters.year}
            onChange={(e) => setDraftFilters({...draftFilters, year: e.target.value})}
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
            value={draftFilters.quarter}
            onChange={(e) => setDraftFilters({...draftFilters, quarter: e.target.value})}
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
            value={draftFilters.artist}
            onChange={(e) => setDraftFilters({...draftFilters, artist: e.target.value})}
            className={styles.filter}
          />

          <input
            type="text"
            placeholder="Search Track"
            value={draftFilters.track}
            onChange={(e) => setDraftFilters({...draftFilters, track: e.target.value})}
            className={styles.filter}
          />

          <input
            type="text"
            placeholder="Catalog (TTR019, etc.)"
            value={draftFilters.catalog}
            onChange={(e) => setDraftFilters({...draftFilters, catalog: e.target.value})}
            className={styles.filter}
          />

          <button 
            onClick={applyFilters}
            className={styles.applyFiltersBtn}
          >
            Apply Filters
          </button>

          <button 
            onClick={clearFilters}
            className={styles.clearFiltersBtn}
          >
            Clear All
          </button>
        </div>
      </div>

      {/* KPI Summary */}
      {kpiData && (
        <div className={styles.kpiSummary}>
          <div className={styles.kpiGrid}>
            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Overall Revenue</div>
              <div className={styles.kpiValue}>{formatCurrency(kpiData.overall_total || kpiData.total_revenue)}</div>
              <div className={styles.kpiChange}>all time earnings</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Artists</div>
              <div className={styles.kpiValue}>{kpiData.unique_artists}</div>
              <div className={styles.kpiChange}>earning revenue</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Tracks</div>
              <div className={styles.kpiValue}>{kpiData.unique_tracks}</div>
              <div className={styles.kpiChange}>with sales</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Transactions</div>
              <div className={styles.kpiValue}>{formatNumber(kpiData.total_transactions)}</div>
              <div className={styles.kpiChange}>{formatCurrency(kpiData.avg_per_transaction)} average</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Bandcamp Revenue</div>
              <div className={styles.kpiValue}>{formatCurrency(kpiData.bandcamp_total || 0)}</div>
              <div className={styles.kpiChange}>all time earnings</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Distribution Revenue</div>
              <div className={styles.kpiValue}>{formatCurrency(kpiData.distribution_total || 0)}</div>
              <div className={styles.kpiChange}>all time earnings</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Top Artist</div>
              <div className={styles.kpiValue}>{kpiData?.top_artist?.name || 'N/A'}</div>
              <div className={styles.kpiChange}>{formatCurrency(kpiData?.top_artist?.revenue || 0)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className={styles.chartsSection}>
        {/* Bandcamp only */}
        <div className={styles.chartCard} style={{ minHeight: 320 }}>
          <h3>Bandcamp - Daily Revenue</h3>
          {quarterlyData && quarterlyData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={quarterlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 'dataMax']} tickFormatter={safeEuro} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              {hasBandcamp && (
                <Line type="linear" dataKey="Bandcamp" stroke="#408294" strokeWidth={2} connectNulls={true} dot={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
          ) : (
            <div style={{ padding: 12, color: '#6b7280' }}>No chart data available</div>
          )}
        </div>

        {/* Distribution split by platform/store */}
        <div className={styles.chartCard} style={{ minHeight: 320 }}>
          <h3>Distribution - Daily Revenue by Platform</h3>
          {distributionChartData && distributionChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={distributionChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 'dataMax']} tickFormatter={safeEuro} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              {distributionKeys.map((key, idx) => (
                <Line key={key} type="linear" dataKey={key} stroke={palette[idx % palette.length]} strokeWidth={2} connectNulls={true} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
          ) : (
            <div style={{ padding: 12, color: '#6b7280' }}>No chart data available</div>
          )}
        </div>

        <div className={styles.chartCard}>
          <h3>Platform Revenue Share</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={topNWithOthers(platformData, 10)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name} ${percentage}%`}
              >
                {topNWithOthers(platformData, 10).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Total Distribution Revenue by Platform */}
        <div className={styles.chartCard}>
          <h3>Distribution Revenue by Platform (Total)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={topNWithOthers(platformData.filter(p => p.name !== 'Bandcamp'), 10)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name} ${percentage}%`}
              >
                {topNWithOthers(platformData.filter(p => p.name !== 'Bandcamp'), 10).map((entry, index) => (
                  <Cell key={`cell-dist-${index}`} fill={entry.color} />
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
          <h3>Revenue Transactions</h3>
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
                <th>Source</th>
                <th>Year</th>
                <th>Q</th>
                <th>Date</th>
                <th>Catalog</th>
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
                  <td className={styles.vendor}>{row.vendor}</td>
                  <td className={styles.source}>{row.data_source || 'CSV'}</td>
                  <td>{row.year}</td>
                  <td>{row.quarter}</td>
                  <td className={styles.date}>{row.date}</td>
                  <td className={styles.catalog}>{row.catalog_number}</td>
                  <td className={styles.artistName}>{row.track_artist}</td>
                  <td className={styles.trackName}>{row.track_name}</td>
                  <td className={styles.isrc}>{row.isrc}</td>
                  <td className={styles.platform}>{row.platform}</td>
                  <td className={styles.number}>{parseInt(row.downloads || 0).toLocaleString()}</td>
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
    </div>
  );
};

const AnalyticsImproved = () => {
  return (
    <ErrorBoundary>
      <AnalyticsContent />
    </ErrorBoundary>
  );
};

export default AnalyticsImproved;
