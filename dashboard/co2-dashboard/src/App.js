import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Prediction from './pages/Prediction';
import Data from './pages/Data';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        {/* Sidebar */}
        <nav className="sidebar">
          <h2>CO2 Dashboard</h2>
          <ul>
            <li><Link to="/">Accueil</Link></li>
            <li><Link to="/data">Data</Link></li>
            <li><Link to="/dashboard">Dashboard</Link></li>
            <li><Link to="/prediction">Prediction</Link></li>
            <li><Link to="/history">history</Link></li>
          </ul>
        </nav>

        {/* Contenu principal */}
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/prediction" element={<Prediction />} />
            <Route path="/data" element={<Data />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
