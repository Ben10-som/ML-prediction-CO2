import { useState, useEffect } from 'react';
import axios from 'axios';
import './Data.css';

function Data() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data-raw')
            .then(res => {
                setData(res.data.raw_data || []);
                setLoading(false);
            })
            .catch(err => {
                console.error("Erreur API:", err);
                setLoading(false);
            });
    }, []);

    const downloadCSV = () => {
        if (data.length === 0) return;

        const headers = Object.keys(data[0]).join(",");
        const rows = data.map(row => Object.values(row).map(v => `"${v}"`).join(",")).join("\n");
        const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + rows;

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "seattle_co2_data.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    if (loading) return <div className="loading">Chargement des données...</div>;

    return (
        <div className="page data-page">
            <div className="data-header">
                <div>
                    <h2>Base de Données</h2>
                    <p>Exploration des données brutes utilisées pour l'entraînement.</p>
                </div>
                <button onClick={downloadCSV} className="btn-download">
                    📥 Télécharger CSV
                </button>
            </div>

            <div className="table-container">
                <table>
                    <thead>
                        <tr>
                            {data.length > 0 && Object.keys(data[0]).slice(0, 10).map((key) => <th key={key}>{key}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {data.slice(0, 50).map((row, idx) => (
                            <tr key={idx}>
                                {Object.values(row).slice(0, 10).map((val, i) => <td key={i}>{val}</td>)}
                            </tr>
                        ))}
                    </tbody>
                </table>
                <p className="table-info">Affichage des 50 premières lignes (Total: {data.length} entrées)</p>
            </div>
        </div>
    );
}

export default Data;
