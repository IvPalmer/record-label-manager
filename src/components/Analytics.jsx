import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Area, AreaChart } from 'recharts';
import styles from './Analytics.module.css';

const Analytics = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedYear, setSelectedYear] = useState('2024');
  const [data, setData] = useState({
    overview: null,
    artistBreakdown: [],
    trackBreakdown: [],
    platformBreakdown: [],
    quarterlyData: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedYear]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    
    // Mock data based on your real financial data
    const mockData = {
      overview: {
        totalRevenue: 7096.66,
        distributionRevenue: 5297.22,
        bandcampRevenue: 1799.44,
        totalTracks: 156,
        totalArtists: 23,
        totalTransactions: 11000
      },
      
      quarterlyData: [
        { quarter: 'Q1', distribution: 1091.55, bandcamp: 450.25, total: 1541.80 },
        { quarter: 'Q2', distribution: 1445.29, bandcamp: 523.18, total: 1968.47 },
        { quarter: 'Q3', distribution: 1481.01, bandcamp: 412.33, total: 1893.34 },
        { quarter: 'Q4', distribution: 1279.36, bandcamp: 413.68, total: 1693.04 }
      ],
      
      platformBreakdown: [
        { name: 'Spotify', revenue: 2100.50, percentage: 29.6, color: '#1DB954' },
        { name: 'Apple Music', revenue: 1450.30, percentage: 20.4, color: '#FA243C' },
        { name: 'YouTube Music', revenue: 980.25, percentage: 13.8, color: '#FF0000' },
        { name: 'Amazon Music', revenue: 766.17, percentage: 10.8, color: '#FF9900' },
        { name: 'Bandcamp', revenue: 1799.44, percentage: 25.4, color: '#408294' }
      ],
      
      artistBreakdown: [
        { artist: 'Ibu Selva', revenue: 1426.45, tracks: 8, percentage: 20.1 },
        { artist: 'BirdZzie', revenue: 892.33, tracks: 5, percentage: 12.6 },
        { artist: 'Yaguareté', revenue: 645.28, tracks: 3, percentage: 9.1 },
        { artist: 'Kurup', revenue: 521.67, tracks: 4, percentage: 7.4 },
        { artist: 'Cigarra', revenue: 398.45, tracks: 6, percentage: 5.6 },
        { artist: 'Pandemonius', revenue: 334.78, tracks: 3, percentage: 4.7 },
        { artist: 'Bmind', revenue: 287.92, tracks: 2, percentage: 4.1 },
        { artist: 'Salvador Araguaya', revenue: 245.88, tracks: 2, percentage: 3.5 }
      ],
      
      trackBreakdown: [
        { artist: 'Ibu Selva', title: 'Milonga', isrc: 'US83Z2005182', catalog: 'TTR019', revenue: 1126.01, streams: 185000 },
        { artist: 'BirdZzie', title: 'En Tu Puerta Estamos Cuatro', isrc: 'QZNRS2038186', catalog: 'TTR???', revenue: 620.38, streams: 44000 },
        { artist: 'Yaguareté', title: 'Bachianas Brasileiras N5', isrc: 'QZJRB1957380', catalog: 'TTR???', revenue: 510.18, streams: 162000 },
        { artist: 'Kurup', title: 'Três Mulheres de Xangô', isrc: 'US83Z2014031', catalog: 'TTR003', revenue: 501.64, streams: 107000 },
        { artist: 'Unknown', title: 'Unknown Track', isrc: 'DEBE72300408', catalog: 'TTR???', revenue: 402.64, streams: 150000 }
      ]
    };
    
    setData(mockData);
    setLoading(false);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const exportData = (dataType) => {
    let csvContent = '';
    let filename = `${dataType}-${selectedYear}.csv`;
    
    switch(dataType) {
      case 'artists':
        csvContent = [
          ['Artist', 'Revenue_EUR', 'Tracks_Count', 'Percentage'],
          ...data.artistBreakdown.map(artist => [
            artist.artist, artist.revenue, artist.tracks, artist.percentage + '%'
          ])
        ].map(row => row.join(',')).join('\n');
        break;
        
      case 'tracks':
        csvContent = [
          ['Artist', 'Track', 'ISRC', 'Catalog', 'Revenue_EUR', 'Streams'],
          ...data.trackBreakdown.map(track => [
            track.artist, track.title, track.isrc, track.catalog, track.revenue, track.streams
          ])
        ].map(row => row.join(',')).join('\n');
        break;
        
      case 'quarterly':
        csvContent = [
          ['Quarter', 'Distribution_EUR', 'Bandcamp_EUR', 'Total_EUR'],
          ...data.quarterlyData.map(q => [
            q.quarter, q.distribution, q.bandcamp, q.total
          ])
        ].map(row => row.join(',')).join('\n');
        break;
    }
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className={styles.container}>Loading analytics...</div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>📊 Revenue Analytics</h1>
        <div className={styles.controls}>
          <select 
            value={selectedYear} 
            onChange={(e) => setSelectedYear(e.target.value)}
            className={styles.select}
          >
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
            <option value="all">All Years</option>
          </select>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className={styles.tabNav}>
        <button 
          className={`${styles.tab} ${activeTab === 'overview' ? styles.active : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'artists' ? styles.active : ''}`}
          onClick={() => setActiveTab('artists')}
        >
          🎵 Artists
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'tracks' ? styles.active : ''}`}
          onClick={() => setActiveTab('tracks')}
        >
          🎶 Tracks
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'platforms' ? styles.active : ''}`}
          onClick={() => setActiveTab('platforms')}
        >
          🌍 Platforms
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className={styles.tabContent}>
          {/* KPI Cards */}
          <div className={styles.kpiGrid}>
            <div className={styles.kpiCard}>
              <h3>Total Revenue</h3>
              <div className={styles.kpiValue}>{formatCurrency(data.overview.totalRevenue)}</div>
              <div className={styles.kpiSubtext}>{selectedYear} performance</div>
            </div>
            
            <div className={styles.kpiCard}>
              <h3>Active Artists</h3>
              <div className={styles.kpiValue}>{data.overview.totalArtists}</div>
              <div className={styles.kpiSubtext}>earning revenue</div>
            </div>
            
            <div className={styles.kpiCard}>
              <h3>Total Tracks</h3>
              <div className={styles.kpiValue}>{data.overview.totalTracks}</div>
              <div className={styles.kpiSubtext}>with earnings</div>
            </div>
            
            <div className={styles.kpiCard}>
              <h3>Transactions</h3>
              <div className={styles.kpiValue}>{formatNumber(data.overview.totalTransactions)}</div>
              <div className={styles.kpiSubtext}>across all platforms</div>
            </div>
          </div>

          {/* Charts Row */}
          <div className={styles.chartsRow}>
            {/* Quarterly Performance */}
            <div className={styles.chartCard}>
              <h3>📈 Quarterly Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={data.quarterlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="quarter" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Area type="monotone" dataKey="distribution" stackId="1" stroke="#667eea" fill="#667eea" />
                  <Area type="monotone" dataKey="bandcamp" stackId="1" stroke="#408294" fill="#408294" />
                </AreaChart>
              </ResponsiveContainer>
              <button 
                className={styles.exportBtn}
                onClick={() => exportData('quarterly')}
              >
                📊 Export Quarterly Data
              </button>
            </div>

            {/* Platform Breakdown */}
            <div className={styles.chartCard}>
              <h3>🌍 Platform Revenue Share</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.platformBreakdown}
                    dataKey="revenue"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percentage }) => `${name} ${percentage}%`}
                  >
                    {data.platformBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Artists Tab */}
      {activeTab === 'artists' && (
        <div className={styles.tabContent}>
          <div className={styles.sectionHeader}>
            <h2>🎵 Revenue by Artist</h2>
            <button 
              className={styles.exportBtn}
              onClick={() => exportData('artists')}
            >
              📊 Export Artist Data
            </button>
          </div>
          
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Artist</th>
                  <th>Total Revenue</th>
                  <th>Tracks</th>
                  <th>% of Total</th>
                </tr>
              </thead>
              <tbody>
                {data.artistBreakdown.map((artist, index) => (
                  <tr key={artist.artist}>
                    <td>#{index + 1}</td>
                    <td className={styles.artistName}>{artist.artist}</td>
                    <td className={styles.revenue}>{formatCurrency(artist.revenue)}</td>
                    <td>{artist.tracks}</td>
                    <td>{artist.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tracks Tab */}
      {activeTab === 'tracks' && (
        <div className={styles.tabContent}>
          <div className={styles.sectionHeader}>
            <h2>🎶 Revenue by Track</h2>
            <button 
              className={styles.exportBtn}
              onClick={() => exportData('tracks')}
            >
              📊 Export Track Data
            </button>
          </div>
          
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Artist</th>
                  <th>Track</th>
                  <th>Catalog</th>
                  <th>Revenue</th>
                  <th>Streams</th>
                  <th>ISRC</th>
                </tr>
              </thead>
              <tbody>
                {data.trackBreakdown.map((track, index) => (
                  <tr key={track.isrc}>
                    <td>#{index + 1}</td>
                    <td className={styles.artistName}>{track.artist}</td>
                    <td className={styles.trackTitle}>{track.title}</td>
                    <td className={styles.catalog}>{track.catalog}</td>
                    <td className={styles.revenue}>{formatCurrency(track.revenue)}</td>
                    <td>{formatNumber(track.streams)}</td>
                    <td className={styles.isrc}>{track.isrc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Platforms Tab */}
      {activeTab === 'platforms' && (
        <div className={styles.tabContent}>
          <div className={styles.sectionHeader}>
            <h2>🌍 Platform Performance</h2>
          </div>
          
          <div className={styles.platformGrid}>
            {data.platformBreakdown.map((platform) => (
              <div key={platform.name} className={styles.platformCard}>
                <div className={styles.platformHeader}>
                  <div 
                    className={styles.platformColor} 
                    style={{ backgroundColor: platform.color }}
                  ></div>
                  <h3>{platform.name}</h3>
                </div>
                <div className={styles.platformRevenue}>
                  {formatCurrency(platform.revenue)}
                </div>
                <div className={styles.platformPercentage}>
                  {platform.percentage}% of total revenue
                </div>
              </div>
            ))}
          </div>

          {/* Platform Performance Chart */}
          <div className={styles.chartCard}>
            <h3>💰 Platform Revenue Comparison</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data.platformBreakdown} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Bar dataKey="revenue" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Bottom Action Section */}
      <section className={styles.actionSection}>
        <h2>💰 Year-End Payout Summary</h2>
        <div className={styles.payoutSummary}>
          <div className={styles.payoutCard}>
            <h3>🎯 2024 Total</h3>
            <div className={styles.payoutAmount}>{formatCurrency(data.overview.totalRevenue)}</div>
            <p>Ready for artist distribution</p>
          </div>
          
          <div className={styles.payoutCard}>
            <h3>🏆 Top Artist</h3>
            <div className={styles.payoutAmount}>Ibu Selva</div>
            <p>{formatCurrency(1426.45)} earned</p>
          </div>
          
          <div className={styles.payoutCard}>
            <h3>🎵 Top Track</h3>
            <div className={styles.payoutAmount}>Milonga</div>
            <p>{formatCurrency(1126.01)} earned</p>
          </div>
        </div>
        
        <div className={styles.actionButtons}>
          <a 
            href="http://127.0.0.1:8000/admin/finances/revenueevent/" 
            target="_blank"
            rel="noopener noreferrer"
            className={styles.actionBtn}
          >
            🔧 Django Admin
          </a>
          <button 
            onClick={() => exportData('artists')}
            className={styles.actionBtn}
          >
            📊 Export All Data
          </button>
        </div>
      </section>
    </div>
  );
};

export default Analytics;
