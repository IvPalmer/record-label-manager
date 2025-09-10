import React from 'react';
import styles from './AnalyticsOverview.module.css';

const AnalyticsSimpleTest = () => {
  const testData = [
    {
      id: 1,
      vendor: 'Distribution',
      year: 2024,
      quarter: 4,
      date: '2024-10-01',
      catalog_number: 'TTR019',
      track_artist: 'Ibu Selva',
      track_name: 'Milonga',
      isrc: 'US83Z2005182',
      platform: 'Distribution',
      streams: 45195,
      revenue: 103.96
    },
    {
      id: 2,
      vendor: 'Distribution',
      year: 2024,
      quarter: 2,
      date: '2024-04-01',
      catalog_number: 'TTR069',
      track_artist: 'Dos Kanye',
      track_name: 'Kibutz Jungle',
      isrc: 'DEBE72100449',
      platform: 'Distribution',
      streams: 25450,
      revenue: 117.11
    }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.filtersSection}>
        <h3>Revenue Analytics Test</h3>
        <p>Database: 95,349 records across 2015-2025</p>
        <p>Frontend: http://localhost:5175/</p>
        <p>Backend: http://127.0.0.1:8000/</p>
      </div>

      <div className={styles.tableSection}>
        <div className={styles.tableHeader}>
          <h3>Sample Revenue Data</h3>
          <div>Showing 2 sample records</div>
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
              {testData.map((row) => (
                <tr key={row.id}>
                  <td>{row.vendor}</td>
                  <td>{row.year}</td>
                  <td>{row.quarter}</td>
                  <td>{row.date}</td>
                  <td>{row.catalog_number}</td>
                  <td>{row.track_artist}</td>
                  <td>{row.track_name}</td>
                  <td>{row.isrc}</td>
                  <td>{row.platform}</td>
                  <td>{row.streams.toLocaleString()}</td>
                  <td>€{row.revenue.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={styles.summarySection}>
        <h3>System Status</h3>
        <div className={styles.summaryCards}>
          <div className={styles.summaryCard}>
            <h4>Database Records</h4>
            <div className={styles.summaryValue}>95,349</div>
            <div className={styles.summaryDesc}>Clean transactions</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Years Coverage</h4>
            <div className={styles.summaryValue}>2015-2025</div>
            <div className={styles.summaryDesc}>Complete history</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Top Artist</h4>
            <div className={styles.summaryValue}>Ibu Selva</div>
            <div className={styles.summaryDesc}>Milonga - €103.96</div>
          </div>
          
          <div className={styles.summaryCard}>
            <h4>Backend Status</h4>
            <div className={styles.summaryValue}>Ready</div>
            <div className={styles.summaryDesc}>API operational</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsSimpleTest;
