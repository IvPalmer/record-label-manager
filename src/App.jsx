import React from 'react';
import { BrowserRouter as Router, Route, Routes, NavLink } from 'react-router-dom';
import './App.css';

// Import components
import Dashboard from './components/Dashboard';
import Releases from './components/Releases';
import ReleaseDetail from './components/ReleaseDetail';
import Tracks from './components/Tracks';
import TrackDetail from './components/TrackDetail';
import Calendar from './components/Calendar';
import Artists from './components/Artists';
import ArtistDetail from './components/ArtistDetail';
import Demos from './components/Demos';
import DemoDetail from './components/DemoDetail';
import Documents from './components/Documents';
import Settings from './components/Settings';
import Analytics from './components/Analytics';

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('App render error:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24 }}>
          <h3>Something went wrong</h3>
          <p>The UI failed to render. Check the console for details.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <nav className="sidebar">
          <h1>Record Label Manager</h1>
          <ul>
            {/* Use NavLink for active styling */}
            <li><NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''} end>Dashboard</NavLink></li>
            <li><NavLink to="/releases" className={({ isActive }) => isActive ? 'active' : ''}>Releases</NavLink></li>
            <li><NavLink to="/tracks" className={({ isActive }) => isActive ? 'active' : ''}>Tracks</NavLink></li>
            <li><NavLink to="/calendar" className={({ isActive }) => isActive ? 'active' : ''}>Calendar</NavLink></li>
            <li><NavLink to="/artists" className={({ isActive }) => isActive ? 'active' : ''}>Artists</NavLink></li>
            <li><NavLink to="/analytics" className={({ isActive }) => isActive ? 'active' : ''}>Analytics</NavLink></li>
            <li><NavLink to="/demos" className={({ isActive }) => isActive ? 'active' : ''}>Demos</NavLink></li>
            <li><NavLink to="/documents" className={({ isActive }) => isActive ? 'active' : ''}>Documents</NavLink></li>
            <li><NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>Settings</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <AppErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/releases" element={<Releases />} />
            <Route path="/releases/:id" element={<ReleaseDetail />} />
            <Route path="/tracks" element={<Tracks />} />
            <Route path="/tracks/:id" element={<TrackDetail />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/artists" element={<Artists />} />
            <Route path="/artists/:id" element={<ArtistDetail />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/demos" element={<Demos />} />
            <Route path="/demos/:id" element={<DemoDetail />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
          </AppErrorBoundary>
        </main>
      </div>
    </Router>
  );
}

export default App;
