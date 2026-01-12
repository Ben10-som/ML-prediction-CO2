import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, CartesianGrid, ResponsiveContainer,
    Cell, PieChart, Pie, Legend, ScatterChart, Scatter
} from 'recharts';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import './Dashboard.css';

// --- Heatmap Component ---
function Heatmap({ points }) {
    const map = useMap();
    useEffect(() => {
        if (!points || points.length === 0) return;

        // Heatmap layer
        const heatLayer = L.heatLayer(points, {
            radius: 20,
            blur: 15,
            maxZoom: 15,
            max: 1000
        }).addTo(map);

        return () => {
            if (map.hasLayer(heatLayer)) map.removeLayer(heatLayer);
        };
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
                    // Energy Data for Mix Chart
                    Elec: Number(row['Electricity(kBtu)']) || 0,
                    Gas: Number(row['NaturalGas(kBtu)']) || 0,
                    Steam: Number(row['SteamUse(kBtu)']) || 0,
                    lat: Number(row.Latitude),
                    lon: Number(row.Longitude)
                })).filter(d => d.lat && d.lon);
                setData(rawData);
                setLoading(false);
            })
            .catch(err => {
                console.error("Erreur chargement données:", err);
                setLoading(false);
            });
    }, []);

    // --- Computed Data & KPIs ---

    const filteredData = useMemo(() => {
        return data.filter(d => {
            const matchYear = selectedYear === 'All' || d.YearBuilt === Number(selectedYear);
            const matchType = selectedType === 'All' || d.PrimaryPropertyType === selectedType;
            return matchYear && matchType;
        });
    }, [data, selectedYear, selectedType]);

    const kpis = useMemo(() => {
        const totalCO2 = filteredData.reduce((acc, curr) => acc + curr.CO2Emissions, 0);
        const avgCO2 = filteredData.length ? totalCO2 / filteredData.length : 0;
        const maxCO2 = Math.max(...filteredData.map(d => d.CO2Emissions), 0);
        // Innovation: Carbon Intensity (kg CO2 / kBtu) approx
        const totalEnergy = filteredData.reduce((acc, curr) => acc + curr.Elec + curr.Gas + curr.Steam, 0);
        const intensity = totalEnergy ? (totalCO2 * 1000) / totalEnergy : 0;

        return {
            totalCO2,
            avgCO2,
            maxCO2,
            count: filteredData.length,
            intensity: intensity.toFixed(2)
        };
    }, [filteredData]);

    const neighborhoodData = useMemo(() => {
        const counts = {};
        filteredData.forEach(d => {
            counts[d.Neighborhood] = (counts[d.Neighborhood] || 0) + d.CO2Emissions;
        });
        return Object.entries(counts)
            .map(([name, val]) => ({ name, value: val }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 10); // Top 10
    }, [filteredData]);

    // Innovation: Energy Mix Stacked Bar
    const energyMixData = useMemo(() => {
        const mix = {};
        filteredData.forEach(d => {
            const t = d.PrimaryPropertyType;
            if (!mix[t]) mix[t] = { name: t, Elec: 0, Gas: 0, Steam: 0 };
            mix[t].Elec += d.Elec;
            mix[t].Gas += d.Gas;
            mix[t].Steam += d.Steam;
        });
        // Sort by total energy
        return Object.values(mix)
            .sort((a, b) => (b.Elec + b.Gas + b.Steam) - (a.Elec + a.Gas + a.Steam))
            .slice(0, 5);
    }, [filteredData]);

    // Scatter Data (Year vs CO2)
    const scatterData = useMemo(() => {
        return filteredData.slice(0, 300).map(d => ({ x: d.YearBuilt, y: d.CO2Emissions }));
    }, [filteredData]);

    const heatPoints = useMemo(() => {
        return filteredData.map(d => [d.lat, d.lon, d.CO2Emissions]);
    }, [filteredData]);

    const years = useMemo(() => [...new Set(data.map(d => d.YearBuilt))].sort().reverse(), [data]);
    const types = useMemo(() => [...new Set(data.map(d => d.PrimaryPropertyType))].sort(), [data]);

    const COLORS = ['#7c3aed', '#c084fc', '#10b981', '#f59e0b', '#ef4444', '#64748b'];

    if (loading) return <div className="loading">Chargement des Analytics...</div>;

    return (
        <div className="page dashboard-page">
            <header className="dashboard-header">
                <div>
                    <h2>Energy Intelligence</h2>
                    <p className="subtitle">Analyse avancée des performances énergétiques</p>
                </div>

                <div className="filters-bar">
                    <div className="filter-group">
                        <label>Année</label>
                        <select value={selectedYear} onChange={e => setSelectedYear(e.target.value)}>
                            <option value="All">Toutes</option>
                            {years.map(y => <option key={y} value={y}>{y}</option>)}
                        </select>
                    </div>
                    <div className="filter-group">
                        <label>Type</label>
                        <select value={selectedType} onChange={e => setSelectedType(e.target.value)}>
                            <option value="All">Tous</option>
                            {types.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                    </div>
                </div>
            </header>

            {/* KPIs */}
            <div className="kpi-grid">
                <div className="card kpi-card">
                    <h3>Total Émissions</h3>
                    <p className="kpi-value">{kpis.totalCO2.toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="unit">t</span></p>
                </div>
                <div className="card kpi-card">
                    <h3>Intensité Carbone</h3>
                    <p className="kpi-value">{kpis.intensity} <span className="unit">kg/kBtu</span></p>
                </div>
                <div className="card kpi-card">
                    <h3>Moyenne / Bâtiment</h3>
                    <p className="kpi-value">{kpis.avgCO2.toFixed(1)} <span className="unit">t</span></p>
                </div>
                <div className="card kpi-card highlight">
                    <h3>Bâtiments Analysés</h3>
                    <p className="kpi-value">{kpis.count}</p>
                </div>
            </div>

            {/* Charts Row 1 */}
            <div className="charts-grid">
                <div className="chart-container">
                    <h3>📍 Pollution par Quartier (Top 10)</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={neighborhoodData} layout="vertical" margin={{ left: 40, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                            <XAxis type="number" hide />
                            <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                            <RechartsTooltip cursor={{ fill: '#f5f3ff' }} />
                            <Bar dataKey="value" fill="#7c3aed" radius={[0, 4, 4, 0]} barSize={20}>
                                {neighborhoodData.map((e, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-container">
                    <h3>⚡ Mix Énergétique (Top 5 Types)</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={energyMixData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={60} />
                            <YAxis hide />
                            <RechartsTooltip />
                            <Legend />
                            <Bar dataKey="Elec" stackId="a" fill="#3b82f6" name="Électricité" />
                            <Bar dataKey="Gas" stackId="a" fill="#f59e0b" name="Gaz Naturel" />
                            <Bar dataKey="Steam" stackId="a" fill="#ef4444" name="Vapeur" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 2 */}
            <div className="charts-grid">
                <div className="chart-container">
                    <h3>📅 Tendance: Âge du bâtiment vs Émissions</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                            <CartesianGrid />
                            <XAxis type="number" dataKey="x" name="Année" domain={['auto', 'auto']} />
                            <YAxis type="number" dataKey="y" name="CO2" unit="t" />
                            <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter name="Bâtiments" data={scatterData} fill="#8b5cf6" shape="circle" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>

                <div className="map-section" style={{ minHeight: '350px', background: 'white' }}>
                    <div className="map-header">
                        <h3>🗺️ Géographie des Émissions</h3>
                    </div>
                    <MapContainer center={[47.6062, -122.3321]} zoom={11} scrollWheelZoom={false} className="leaflet-map" style={{ height: '100%' }}>
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        />
                        <Heatmap points={heatPoints} />
                    </MapContainer>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
