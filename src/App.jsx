import React from 'react';
import { BrowserRouter as Router, Route, Routes, NavLink } from 'react-router-dom';
import './App.css';

// Import components
import Dashboard from './components/Dashboard';
import Releases from './components/Releases';
import Calendar from './components/Calendar';
import Artists from './components/Artists';
import Demos from './components/Demos';
import Documents from './components/Documents';
import Settings from './components/Settings';

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
            <li><NavLink to="/calendar" className={({ isActive }) => isActive ? 'active' : ''}>Calendar</NavLink></li>
            <li><NavLink to="/artists" className={({ isActive }) => isActive ? 'active' : ''}>Artists</NavLink></li>
            <li><NavLink to="/demos" className={({ isActive }) => isActive ? 'active' : ''}>Demos</NavLink></li>
            <li><NavLink to="/documents" className={({ isActive }) => isActive ? 'active' : ''}>Documents</NavLink></li>
            <li><NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>Settings</NavLink></li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/releases" element={<Releases />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/artists" element={<Artists />} />
            <Route path="/demos" element={<Demos />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/settings" element={<Settings />} />
            {/* Add more specific routes later, e.g., /releases/:id */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
