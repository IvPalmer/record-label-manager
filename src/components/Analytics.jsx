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
  const [monthlyData, setMonthlyData] = useState([]);
  const [quarterlyData, setQuarterlyData] = useState([]);
  const [platformData, setPlatformData] = useState([]);
  const [kpiData, setKpiData] = useState(null);
  const [availableYears, setAvailableYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 100, totalCount: 0 });
  const [activeTab, setActiveTab] = useState('overview');
  const [currentCurrency, setCurrentCurrency] = useState('BRL');
  const [currencyLoading, setCurrencyLoading] = useState(false);
  
  // Pre-loaded data for all currencies
  const [allCurrencyData, setAllCurrencyData] = useState({
    BRL: { kpi: null, monthly: [], quarterly: [], platform: [] },
    USD: { kpi: null, monthly: [], quarterly: [], platform: [] },
    EUR: { kpi: null, monthly: [], quarterly: [], platform: [] }
  });
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

  // Only trigger data loading when appliedFilters, pagination, or tab changes
  useEffect(() => {
    loadData(); // Still load detailed table data with current currency
    loadAllCurrencyData(); // Load all currency data for charts/KPIs
  }, [appliedFilters, pagination.page, activeTab]);


  // Load data for all currencies at once
  const loadAllCurrencyData = async () => {
    try {
      const currencies = ['BRL', 'USD', 'EUR'];
      const chartParams = new URLSearchParams();
      if (appliedFilters.year !== 'all') chartParams.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') chartParams.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) chartParams.append('artist', appliedFilters.artist);
      if (appliedFilters.track) chartParams.append('track', appliedFilters.track);
      if (appliedFilters.catalog) chartParams.append('catalog', appliedFilters.catalog);

      const newAllCurrencyData = { ...allCurrencyData };

      // Load data for each currency in parallel
      await Promise.all(currencies.map(async (currency) => {
        const currencyParams = new URLSearchParams(chartParams);
        currencyParams.append('currency', currency);

        try {
          const [currencyResponse, kpiResponse, monthlyResponse, quarterlyResponse, platformResponse] = await Promise.all([
            fetch(`http://127.0.0.1:8000/api/finances/revenue/currency_data/?${currencyParams.toString()}`),
            fetch(`http://127.0.0.1:8000/api/finances/revenue/kpi_summary/?${currencyParams.toString()}`),
            fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_overview/?${currencyParams.toString()}`),
            fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_revenue_chart/?${currencyParams.toString()}`),
            fetch(`http://127.0.0.1:8000/api/finances/revenue/platform_pie_chart/?${currencyParams.toString()}`)
          ]);

          if (currencyResponse.ok && kpiResponse.ok) {
            const currencyData = await currencyResponse.json();
            const kpiData = await kpiResponse.json();
            
            // Merge currency-specific revenue amounts with full KPI data
            const mergedKpiData = {
              ...kpiData,
              overall_total: currencyData.overall_total,
              bandcamp_total: currencyData.bandcamp_total,
              distribution_total: currencyData.distribution_total,
              total_revenue: currencyData.overall_total
            };
            
            console.log(`Merged KPI data for ${currency}:`, {
              unique_artists: mergedKpiData.unique_artists,
              unique_tracks: mergedKpiData.unique_tracks,
              total_transactions: mergedKpiData.total_transactions,
              overall_total: mergedKpiData.overall_total
            });
            
            newAllCurrencyData[currency].kpi = mergedKpiData;
          }
          if (monthlyResponse.ok) {
            newAllCurrencyData[currency].monthly = await monthlyResponse.json();
          }
          if (quarterlyResponse.ok) {
            newAllCurrencyData[currency].quarterly = await quarterlyResponse.json();
          }
          if (platformResponse.ok) {
            newAllCurrencyData[currency].platform = await platformResponse.json();
          }
        } catch (error) {
          console.warn(`Failed to load ${currency} data:`, error);
        }
      }));

      setAllCurrencyData(newAllCurrencyData);
      
      // Set initial data for current currency
      updateDisplayDataForCurrency(currentCurrency, newAllCurrencyData);
      
    } catch (error) {
      console.error('Failed to load currency data:', error);
    }
  };

  // Update display data when currency changes (no API calls)
  const updateDisplayDataForCurrency = (currency, currencyData = allCurrencyData) => {
    console.log(`Switching to ${currency}:`, currencyData[currency]);
    const data = currencyData[currency];
    
    if (data && data.kpi) {
      console.log(`Setting KPI data for ${currency}:`, {
        unique_artists: data.kpi.unique_artists,
        unique_tracks: data.kpi.unique_tracks,
        total_transactions: data.kpi.total_transactions,
        overall_total: data.kpi.overall_total
      });
      setKpiData(data.kpi);
    } else {
      console.log(`No KPI data available for ${currency}`);
    }
    
    if (data && data.monthly) setMonthlyData(data.monthly);
    if (data && data.quarterly) setQuarterlyData(data.quarterly);
    if (data && data.platform) setPlatformData(data.platform);
  };

  // Handle currency switching with visual feedback
  const handleCurrencyChange = (newCurrency) => {
    setCurrencyLoading(true);
    setCurrentCurrency(newCurrency);
    
    // Small delay to show loading state, then update data
    setTimeout(() => {
      updateDisplayDataForCurrency(newCurrency);
      setCurrencyLoading(false);
    }, 100);
  };

  // Update data when currency changes
  useEffect(() => {
    if (allCurrencyData[currentCurrency] && allCurrencyData[currentCurrency].kpi) {
      updateDisplayDataForCurrency(currentCurrency);
    }
  }, [currentCurrency, allCurrencyData]);

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


  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build filter parameters using appliedFilters and current currency
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.pageSize.toString(),
        currency: currentCurrency
      });
      
      if (appliedFilters.year !== 'all') params.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') params.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) params.append('artist', appliedFilters.artist);
      if (appliedFilters.track) params.append('track', appliedFilters.track);
      if (appliedFilters.catalog) params.append('catalog', appliedFilters.catalog);
      
      // Load chart data with same filters (without pagination)
      const chartParams = new URLSearchParams();
      chartParams.append('currency', currentCurrency);
      if (appliedFilters.year !== 'all') chartParams.append('year', appliedFilters.year);
      if (appliedFilters.quarter !== 'all') chartParams.append('quarter', appliedFilters.quarter);
      if (appliedFilters.artist) chartParams.append('artist', appliedFilters.artist);
      if (appliedFilters.track) chartParams.append('track', appliedFilters.track);
      if (appliedFilters.catalog) chartParams.append('catalog', appliedFilters.catalog);
      
      // Load monthly aggregated data for overview tab
      const monthlyResponse = await fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_overview/?${chartParams.toString()}`);
      if (monthlyResponse.ok) {
        const monthlyResult = await monthlyResponse.json();
        setMonthlyData(monthlyResult || []);
      }

      // Load detailed table data only when on detailed tab
      if (activeTab === 'detailed') {
        const tableResponse = await fetch(`http://127.0.0.1:8000/api/finances/revenue/detailed_overview/?${params.toString()}`);
        
        if (tableResponse.ok) {
          const result = await tableResponse.json();
          setData(result.data || []);
          setPagination(prev => ({ ...prev, totalCount: result.pagination?.total_count || 0 }));
        } else {
          setError('Failed to load detailed data from API');
          setData([]);
        }
      }
      
      try {
        const [quarterlyResponse, platformResponse] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/finances/revenue/monthly_revenue_chart/?${chartParams.toString()}`),
          fetch(`http://127.0.0.1:8000/api/finances/revenue/platform_pie_chart/?${chartParams.toString()}`)
        ]);
        
        if (quarterlyResponse.ok) {
          const quarterlyResult = await quarterlyResponse.json();
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

  // Backend provides amounts in all currencies, format based on current selection
  const formatCurrency = (amount) => {
    const n = Number(amount);
    if (!isFinite(n)) return '';
    
    switch (currentCurrency) {
      case 'USD':
        return `$${n.toLocaleString('en-US', { 
          minimumFractionDigits: 0, 
          maximumFractionDigits: 0 
        })}`;
      case 'EUR':
        return `€${n.toLocaleString('de-DE', { 
          minimumFractionDigits: 0, 
          maximumFractionDigits: 0 
        })}`;
      case 'BRL':
      default:
        return `R$${n.toLocaleString('pt-BR', { 
          minimumFractionDigits: 0, 
          maximumFractionDigits: 0 
        })}`;
    }
  };

  // Keep legacy functions for backward compatibility
  const formatBRL = (amount) => formatCurrency(amount);
  const formatUSD = (amount) => formatCurrency(amount);

  const formatNumber = (num) => {
    const n = Number(num || 0);
    if (!isFinite(n)) return '0';
    // Use Brazilian locale formatting for numbers
    return Math.round(n).toLocaleString('pt-BR');
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

  // Use backend data directly - backend now handles top 5 + Others aggregation
  const distributionChartData = React.useMemo(() => {
    if (!quarterlyData || quarterlyData.length === 0) return [];
    
    // Find first index where distribution has any value to avoid long empty leading span
    const firstIdx = quarterlyData.findIndex(row => 
      distributionKeys.some(k => Number(row[k]) > 0)
    );
    if (firstIdx === -1) return [];
    
    return quarterlyData.slice(firstIdx);
  }, [quarterlyData, distributionKeys]);

  // Get distribution keys for rendering (exclude Bandcamp and period)
  const distributionRenderKeys = React.useMemo(() => {
    if (!distributionChartData.length) return [];
    
    // Get all keys except 'period' and 'Bandcamp'
    const keys = new Set();
    distributionChartData.forEach(row => {
      Object.keys(row).forEach(key => {
        if (key !== 'period' && key !== 'Bandcamp') {
          keys.add(key);
        }
      });
    });
    
    return Array.from(keys);
  }, [distributionChartData]);

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

  // Consistent platform color mapping - differentiated colors for all platforms
  const platformColors = {
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

  // Simple color palette for multiple distribution platforms (fallback)
  const palette = ['#667eea', '#1DB954', '#FA243C', '#FF9900', '#CC0000', '#4ECDC4', '#A78BFA', '#F59E0B'];

  const safeCurrency = (v) => {
    const n = Number(v);
    if (!isFinite(n)) return '';
    
    switch (currentCurrency) {
      case 'USD':
        return `$${Math.round(n).toLocaleString('en-US')}`;
      case 'EUR':
        return `€${Math.round(n).toLocaleString('de-DE')}`;
      case 'BRL':
      default:
        return `R$${Math.round(n).toLocaleString('pt-BR')}`;
    }
  };

  // Helper: take top N by value and group remainder into "Others"
  const topNWithOthers = (items, n, exclude = [], recalculatePercentages = false, minThreshold = 0) => {
    const filtered = (items || []).filter(i => i && !exclude.includes(i.name) && (Number(i.value) || 0) > minThreshold);
    const sorted = [...filtered].sort((a, b) => (b.value || 0) - (a.value || 0));
    const top = sorted.slice(0, n);
    const rest = sorted.slice(n);
    const othersTotal = rest.reduce((sum, it) => sum + (Number(it.value) || 0), 0);

    let result = [...top];
    if (othersTotal > 0) {
      result.push({ name: 'Others', value: othersTotal, percentage: 0, color: '#9CA3AF' });
    }

    // Recalculate percentages if requested (for filtered data)
    if (recalculatePercentages) {
      const total = result.reduce((sum, item) => sum + (Number(item.value) || 0), 0);
      result = result.map(item => ({
        ...item,
        percentage: total > 0 ? Math.round((Number(item.value) / total * 100) * 10) / 10 : 0
      }));
    }

    // Apply consistent platform colors
    return result.map(item => ({
      ...item,
      color: platformColors[item.name] || item.color || '#9CA3AF'
    }));
  };

  return (
    <div className={styles.container}>
      {/* Filters */}
      <div className={styles.filtersSection}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3>Revenue Analytics ({pagination.totalCount.toLocaleString('pt-BR')} records)</h3>
          
          {/* Currency Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '14px', color: '#666' }}>
              Currency: {currencyLoading && <span style={{ color: '#007bff' }}>⟳</span>}
            </span>
            <div style={{ display: 'flex', border: '1px solid #ddd', borderRadius: '6px', overflow: 'hidden' }}>
              {['BRL', 'USD', 'EUR'].map(currency => (
                <button
                  key={currency}
                  onClick={() => handleCurrencyChange(currency)}
                  disabled={currencyLoading}
                  style={{
                    padding: '6px 12px',
                    border: 'none',
                    backgroundColor: currentCurrency === currency ? '#007bff' : '#fff',
                    color: currentCurrency === currency ? '#fff' : '#333',
                    cursor: 'pointer',
                    fontSize: '12px',
                    fontWeight: currentCurrency === currency ? 'bold' : 'normal',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (currentCurrency !== currency) {
                      e.target.style.backgroundColor = '#f8f9fa';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (currentCurrency !== currency) {
                      e.target.style.backgroundColor = '#fff';
                    }
                  }}
                >
                  {currency === 'BRL' ? 'R$' : currency === 'USD' ? '$' : '€'} {currency}
                </button>
              ))}
            </div>
          </div>
        </div>
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
              <div className={styles.kpiChange}>all time earnings ({currentCurrency})</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Artists</div>
              <div className={styles.kpiValue}>{formatNumber(kpiData.unique_artists)}</div>
              <div className={styles.kpiChange}>earning revenue</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Tracks</div>
              <div className={styles.kpiValue}>{formatNumber(kpiData.unique_tracks)}</div>
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
              <div className={styles.kpiChange}>all time earnings ({currentCurrency})</div>
            </div>

            <div className={styles.kpiItem}>
              <div className={styles.kpiLabel}>Distribution Revenue</div>
              <div className={styles.kpiValue}>{formatCurrency(kpiData.distribution_total || 0)}</div>
              <div className={styles.kpiChange}>all time earnings ({currentCurrency})</div>
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
              <YAxis domain={[0, 'dataMax']} tickFormatter={safeCurrency} />
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
              <YAxis domain={[0, 'dataMax']} tickFormatter={safeCurrency} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              {distributionRenderKeys.map((key, idx) => (
                <Line 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stroke={platformColors[key] || palette[idx % palette.length]} 
                  strokeWidth={2} 
                  connectNulls={true}
                  dot={false}
                />
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
                data={(() => {
                  // Create Bandcamp + top 5 distribution + Others structure
                  const bandcamp = platformData.find(p => p.name === 'Bandcamp');
                  const distributionPlatforms = platformData.filter(p => p.name !== 'Bandcamp');
                  const top5Distribution = topNWithOthers(distributionPlatforms, 5, [], true);
                  
                  let result = [];
                  if (bandcamp) {
                    result.push(bandcamp);
                  }
                  result = result.concat(top5Distribution);
                  
                  // Recalculate percentages for the final set
                  const total = result.reduce((sum, item) => sum + (Number(item.value) || 0), 0);
                  return result.map(item => ({
                    ...item,
                    percentage: total > 0 ? Math.round((Number(item.value) / total * 100) * 10) / 10 : 0,
                    color: platformColors[item.name] || item.color || '#9CA3AF'
                  }));
                })()}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name} ${percentage}%`}
              >
                {(() => {
                  const bandcamp = platformData.find(p => p.name === 'Bandcamp');
                  const distributionPlatforms = platformData.filter(p => p.name !== 'Bandcamp');
                  const top5Distribution = topNWithOthers(distributionPlatforms, 5, [], true);
                  
                  let result = [];
                  if (bandcamp) {
                    result.push(bandcamp);
                  }
                  result = result.concat(top5Distribution);
                  
                  const total = result.reduce((sum, item) => sum + (Number(item.value) || 0), 0);
                  return result.map((item, index) => ({
                    ...item,
                    percentage: total > 0 ? Math.round((Number(item.value) / total * 100) * 10) / 10 : 0,
                    color: platformColors[item.name] || item.color || '#9CA3AF'
                  })).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ));
                })()}
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
                data={topNWithOthers(platformData.filter(p => p.name !== 'Bandcamp'), 5, [], true)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percentage }) => `${name} ${percentage}%`}
              >
                {topNWithOthers(platformData.filter(p => p.name !== 'Bandcamp'), 5, [], true).map((entry, index) => (
                  <Cell key={`cell-dist-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabNavigation} style={{ marginTop: '2rem', marginBottom: '1rem' }}>
        <button 
          onClick={() => setActiveTab('overview')}
          className={activeTab === 'overview' ? styles.activeTab : styles.tab}
          style={{
            padding: '10px 20px',
            marginRight: '10px',
            backgroundColor: activeTab === 'overview' ? '#007acc' : '#f0f0f0',
            color: activeTab === 'overview' ? 'white' : 'black',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Monthly Overview
        </button>
        <button 
          onClick={() => setActiveTab('detailed')}
          className={activeTab === 'detailed' ? styles.activeTab : styles.tab}
          style={{
            padding: '10px 20px',
            backgroundColor: activeTab === 'detailed' ? '#007acc' : '#f0f0f0',
            color: activeTab === 'detailed' ? 'white' : 'black',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Detailed Transactions
        </button>
      </div>

      {/* Monthly Overview Table */}
      {activeTab === 'overview' && (
        <div className={styles.tableSection}>
          <div className={styles.tableHeader}>
            <h3>Monthly Revenue Overview</h3>
            <div>
              Showing {monthlyData.length} months
            </div>
          </div>

          <div className={styles.tableContainer}>
            <table className={styles.detailedTable}>
              <thead>
                 <tr>
                   <th>Month</th>
                   <th>Total Revenue</th>
                   <th>Downloads</th>
                   <th>Streams</th>
                   <th>Artists</th>
                   <th>Tracks</th>
                   <th>Top Release</th>
                   <th>Top Platforms</th>
                 </tr>
              </thead>
              <tbody>
                {monthlyData.map((month) => (
                   <tr key={month.month}>
                     <td className={styles.monthName}>{month.month_name}</td>
                     <td className={styles.revenue}>{formatCurrency(month.total_revenue)}</td>
                     <td className={styles.number}>{parseInt(month.total_downloads || 0).toLocaleString()}</td>
                     <td className={styles.number}>{parseInt(month.total_streams || 0).toLocaleString()}</td>
                     <td className={styles.number}>{month.unique_artists}</td>
                     <td className={styles.number}>{month.unique_tracks}</td>
                     <td className={styles.catalog}>{month.top_release}</td>
                     <td className={styles.platforms}>
                       {month.top_platforms.slice(0, 3).map((platform, idx) => (
                         <span key={idx} style={{ marginRight: '8px', fontSize: '0.85em' }}>
                           {platform.name} ({platform.percentage}%)
                         </span>
                       ))}
                     </td>
                   </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detailed Transactions Table */}
      {activeTab === 'detailed' && (
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
                  <th>Quantity</th>
                  <th>Type</th>
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
                  <td className={styles.number}>
                    {parseInt((row.downloads || 0) + (row.streams || 0)).toLocaleString()}
                  </td>
                  <td className={styles.type}>
                    {row.vendor === 'Bandcamp' || (row.platform && row.platform.toLowerCase().includes('beatport')) ? 
                      'Downloads' : 'Streams'
                    }
                  </td>
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
      )}
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
