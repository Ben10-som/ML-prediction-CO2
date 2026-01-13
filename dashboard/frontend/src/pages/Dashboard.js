import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, CartesianGrid, ResponsiveContainer,
    Cell, PieChart, Pie, Legend, ScatterChart, Scatter, AreaChart, Area, Label
} from 'recharts';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import {
    LayoutDashboard, Map as MapIcon, Zap, Calendar, Trophy, PieChart as PieIcon,
    Activity, TrendingUp, Filter
} from 'lucide-react';
import './Dashboard.css';

// --- Heatmap Component ---
function Heatmap({ points }) {
    const map = useMap();
    useEffect(() => {
        if (!points || points.length === 0) return;
        const heatLayer = L.heatLayer(points, {
            radius: 25,
            blur: 15,
            maxZoom: 14,
            max: 1500,
            gradient: { 0.4: 'blue', 0.65: 'lime', 1: 'red' }
        }).addTo(map);

        return () => { if (map.hasLayer(heatLayer)) map.removeLayer(heatLayer); };
    }, [points, map]);
    return null;
}

// --- Main Dashboard ---
function Dashboard() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filters
    const [selectedYear, setSelectedYear] = useState('All');
    const [selectedType, setSelectedType] = useState('All');

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data-raw')
            .then(res => {
                const rawData = (res.data.raw_data || []).map(row => ({
                    ...row,
                    id: Math.random().toString(36).substr(2, 9),
                    Neighborhood: row.Neighborhood || "Unknown",
                    PrimaryPropertyType: row.PrimaryPropertyType || "Other",
                    YearBuilt: Number(row.YearBuilt),
                    CO2Emissions: Number(row.TotalGHGEmissions) || Number(row.CO2Emissions) || 0,
                    EnergyStar: Number(row.ENERGYSTARScore) || 0,
                    SiteEnergy: Number(row['SiteEnergyUse(kBtu)']) || 0,
                    Elec: Number(row['Electricity(kBtu)']) || 0,
                    Gas: Number(row['NaturalGas(kBtu)']) || 0,
                    Steam: Number(row['SteamUse(kBtu)']) || 0,
                    lat: Number(row.Latitude),
                    lon: Number(row.Longitude)
                })).filter(d => d.lat && d.lon && d.CO2Emissions > 0);
                setData(rawData);
                setLoading(false);
            })
            .catch(err => { console.error(err); setLoading(false); });
    }, []);

    // --- Computed Data ---
    const filteredData = useMemo(() => {
        return data.filter(d => {
            const matchYear = selectedYear === 'All' || d.YearBuilt === Number(selectedYear);
            const matchType = selectedType === 'All' || d.PrimaryPropertyType === selectedType;
            return matchYear && matchType;
        });
    }, [data, selectedYear, selectedType]);

    // KPIs
    const kpis = useMemo(() => {
        const totalCO2 = filteredData.reduce((acc, curr) => acc + curr.CO2Emissions, 0);
        const totalEnergy = filteredData.reduce((acc, curr) => acc + curr.SiteEnergy, 0);
        const avgCO2 = filteredData.length ? totalCO2 / filteredData.length : 0;
        const avgEnergyStar = filteredData.reduce((acc, curr) => acc + curr.EnergyStar, 0) / (filteredData.length || 1);

        return {
            totalCO2,
            totalEnergy,
            avgCO2,
            avgEnergyStar,
            count: filteredData.length
        };
    }, [filteredData]);

    // Chart 1: Top 15 Neighborhoods
    const topNeighborhoods = useMemo(() => {
        const counts = {};
        filteredData.forEach(d => counts[d.Neighborhood] = (counts[d.Neighborhood] || 0) + d.CO2Emissions);
        return Object.entries(counts)
            .map(([name, val]) => ({ name, value: val }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 15);
    }, [filteredData]);

    // Chart 2: Property Type
    const typeData = useMemo(() => {
        const counts = {};
        filteredData.forEach(d => counts[d.PrimaryPropertyType] = (counts[d.PrimaryPropertyType] || 0) + d.CO2Emissions);
        let sorted = Object.entries(counts)
            .map(([name, val]) => ({ name, value: val }))
            .sort((a, b) => b.value - a.value);
        if (sorted.length > 5) {
            const top = sorted.slice(0, 5);
            const other = sorted.slice(5).reduce((a, b) => a + b.value, 0);
            return [...top, { name: 'Others', value: other }];
        }
        return sorted;
    }, [filteredData]);

    // Chart 3: Energy vs CO2 Scatter
    const efficiencyData = useMemo(() => {
        return filteredData.slice(0, 200).map(d => ({
            x: d.SiteEnergy,
            y: d.CO2Emissions,
            size: d.EnergyStar
        }));
    }, [filteredData]);

    // Chart 4: Energy Trends
    const energyTrends = useMemo(() => {
        const buckets = {};
        filteredData.forEach(d => {
            const decade = Math.floor(d.YearBuilt / 10) * 10;
            if (!buckets[decade]) buckets[decade] = { name: decade, Elec: 0, Gas: 0 };
            buckets[decade].Elec += d.Elec;
            buckets[decade].Gas += d.Gas;
        });
        return Object.values(buckets).sort((a, b) => a.name - b.name);
    }, [filteredData]);

    const heatPoints = useMemo(() => filteredData.map(d => [d.lat, d.lon, d.CO2Emissions]), [filteredData]);
    const years = useMemo(() => [...new Set(data.map(d => d.YearBuilt))].sort().reverse(), [data]);
    const types = useMemo(() => [...new Set(data.map(d => d.PrimaryPropertyType))].sort(), [data]);
    const COLORS = ['#7c3aed', '#c084fc', '#10b981', '#f59e0b', '#ef4444', '#64748b'];

    if (loading) return <div className="loading">Chargement des données...</div>;

    return (
        <div className="dashboard-container">
            {/* 1. TOP CONTROLS */}
            <div className="dashboard-top-section">
                <header className="main-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <LayoutDashboard size={32} color="#7c3aed" />
                        <div>
                            <h2>Analytics Dashboard</h2>
                            <p>Supervision énergétique et environnementale</p>
                        </div>
                    </div>
                    <div className="header-filters">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b' }}>
                            <Filter size={18} />
                        </div>
                        <select value={selectedYear} onChange={e => setSelectedYear(e.target.value)}>
                            <option value="All">Année: Toutes</option>
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                        <select value={selectedType} onChange={e => setSelectedType(e.target.value)}>
                            <option value="All">Type: Tous</option>
                            {types.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>
                </header>

                <div className="kpi-banner">
                    <div className="kpi-box">
                        <span className="kpi-label">Total CO₂</span>
                        <span className="kpi-number">{kpis.totalCO2.toLocaleString(undefined, { maximumFractionDigits: 0 })} <small>T</small></span>
                    </div>
                    <div className="kpi-box">
                        <span className="kpi-label">Énergie Totale</span>
                        <span className="kpi-number">{(kpis.totalEnergy / 1000000).toFixed(1)} <small>M kBtu</small></span>
                    </div>
                    <div className="kpi-box">
                        <span className="kpi-label">Nb Bâtiments</span>
                        <span className="kpi-number">{kpis.count}</span>
                    </div>
                    <div className="kpi-box">
                        <span className="kpi-label">Score EnergyStar</span>
                        <span className="kpi-number score">{kpis.avgEnergyStar.toFixed(1)}</span>
                    </div>
                </div>
            </div>

            {/* 2. MAP SECTION */}
            <div className="map-block">
                <div className="block-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <MapIcon size={20} />
                    <h3>Cartographie des Émissions</h3>
                </div>
                <MapContainer center={[47.6062, -122.3321]} zoom={12} scrollWheelZoom={false} className="standard-map">
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    />
                    <Heatmap points={heatPoints} />
                </MapContainer>
            </div>

            {/* 3. CHARTS GRID */}
            <div className="analytics-grid">

                {/* Top 15 Polluters */}
                <div className="chart-card wide">
                    <h3><Trophy size={18} style={{ marginRight: '8px', color: '#f59e0b' }} /> Top 15 Quartiers les plus polluants</h3>
                    <ResponsiveContainer width="100%" height={350}>
                        <BarChart data={topNeighborhoods} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={true} />
                            <XAxis type="number">
                                <Label value="Émissions de CO₂ (Tonnes)" offset={-10} position="insideBottom" />
                            </XAxis>
                            <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11 }}>
                                <Label value="Quartier" angle={-90} position="insideLeft" style={{ textAnchor: 'middle' }} />
                            </YAxis>
                            <RechartsTooltip contentStyle={{ borderRadius: '8px' }} cursor={{ fill: '#f3e8ff' }} />
                            <Bar dataKey="value" fill="#7c3aed" radius={[0, 4, 4, 0]}>
                                {topNeighborhoods.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Pie Chart */}
                <div className="chart-card">
                    <h3><PieIcon size={18} style={{ marginRight: '8px', color: '#10b981' }} /> Répartition par Usage</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={typeData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {typeData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <RechartsTooltip />
                            <Legend verticalAlign="bottom" />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Scatter */}
                <div className="chart-card">
                    <h3><Activity size={18} style={{ marginRight: '8px', color: '#ef4444' }} /> Efficacité : Énergie vs CO₂</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 80 }}>
                            <CartesianGrid />
                            <XAxis type="number" dataKey="x" name="Énergie" unit=" kBtu">
                                <Label value="Conso Énergétique (kBtu)" offset={0} position="insideBottom" />
                            </XAxis>
                            <YAxis type="number" dataKey="y" name="CO2" unit=" t">
                                <Label value="CO₂ (Tonnes)" angle={-90} position="left" style={{ textAnchor: 'middle' }} offset={10} />
                            </YAxis>
                            <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter name="Batiments" data={efficiencyData} fill="#f59e0b" fillOpacity={0.6} />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>

                {/* Trends Area */}
                <div className="chart-card wide">
                    <h3><TrendingUp size={18} style={{ marginRight: '8px', color: '#3b82f6' }} /> Évolution Mix Énergétique</h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <AreaChart data={energyTrends} margin={{ top: 10, right: 30, left: 80, bottom: 40 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="name">
                                <Label value="Décennie de Construction" offset={0} position="insideBottom" />
                            </XAxis>
                            <YAxis tickFormatter={(val) => `${(val / 1000000).toFixed(0)}M`}>
                                <Label value="Total Énergie (kBtu)" angle={-90} position="left" style={{ textAnchor: 'middle' }} offset={10} />
                            </YAxis>
                            <RechartsTooltip formatter={(val) => `${(val / 1000000).toFixed(2)}M kBtu`} />
                            <Legend verticalAlign="top" />
                            <Area type="monotone" dataKey="Elec" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="Électricité" />
                            <Area type="monotone" dataKey="Gas" stackId="1" stroke="#ef4444" fill="#ef4444" name="Gaz" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
