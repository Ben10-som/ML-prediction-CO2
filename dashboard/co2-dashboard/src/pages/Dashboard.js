import { useEffect, useState } from 'react';
import axios from 'axios';
import {
    LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import './Dashboard.css';

// Composant Heatmap
function Heatmap({ points }) {
    const map = useMap();
    useEffect(() => {
        const heatLayer = L.heatLayer(points, {
            radius: 25,
            blur: 15,
            maxZoom: 17
        }).addTo(map);
        return () => { map.removeLayer(heatLayer); };
    }, [points, map]);
    return null;
}

function Dashboard() {
    const [data, setData] = useState([]);
    const [yearFilter, setYearFilter] = useState(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data-raw')
            .then(res => {
                const rawData = res.data.raw_data.map(row => ({
                    ...row,
                    NumberofBuildings: Number(row.NumberofBuildings),
                    NumberofFloors: Number(row.NumberofFloors),
                    PropertyGFATotal: Number(row.PropertyGFATotal),
                    CO2Emissions: Number(row.CO2Emissions) || 0,
                    YearBuilt: Number(row.YearBuilt),
                    lat: Number(row.Latitude) || 47.6062,
                    lon: Number(row.Longitude) || -122.3321
                }));
                setData(rawData);
            })
            .catch(err => console.error(err));
    }, []);

    if (data.length === 0) return <p>Chargement des graphiques...</p>;

    const filteredData = yearFilter ? data.filter(d => d.YearBuilt === yearFilter) : data;
    const years = Array.from(new Set(data.map(d => d.YearBuilt))).sort();

    return (
        <div className="page dashboard-page">
            <h2>Tableau de bord CO₂ - Seattle</h2>

            {/* Filtre par année */}
            <div className="filter">
                <label>Filtrer par année: </label>
                <select value={yearFilter || ""} onChange={(e) => setYearFilter(e.target.value ? Number(e.target.value) : null)}>
                    <option value="">Toutes</option>
                    {years.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
            </div>

            {/* BarChart : nombre de bâtiments */}
            <div className="chart-container">
                <h3>Nombre de bâtiments par année</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="YearBuilt" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="NumberofBuildings" fill="#1e90ff" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* LineChart : surface totale */}
            <div className="chart-container">
                <h3>Surface totale des bâtiments</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="YearBuilt" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="PropertyGFATotal" stroke="#00bfff" />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* LineChart : émissions CO₂ */}
            <div className="chart-container">
                <h3>Émissions CO₂ totales par année</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="YearBuilt" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="CO2Emissions" stroke="#1e90ff" />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Histogramme : distribution des bâtiments par nombre d'étages */}
            <div className="chart-container">
                <h3>Distribution des bâtiments par nombre d'étages</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={filteredData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="NumberofFloors" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="NumberofBuildings" fill="#87cefa" />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Carte interactive avec heatmap */}
            <div className="chart-container">
                <h3>Carte des émissions CO₂</h3>
                <MapContainer center={[47.6062, -122.3321]} zoom={12} style={{ height: "500px", width: "100%" }}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    {filteredData.map((row, idx) => (
                        <Marker key={idx} position={[row.lat, row.lon]}>
                            <Popup>
                                Année: {row.YearBuilt}<br />
                                Bâtiments: {row.NumberofBuildings}<br />
                                Surface: {row.PropertyGFATotal}<br />
                                CO₂: {row.CO2Emissions}
                            </Popup>
                        </Marker>
                    ))}
                    <Heatmap points={filteredData.map(d => [d.lat, d.lon, d.CO2Emissions])} />
                </MapContainer>
            </div>
        </div>
    );
}

export default Dashboard;
