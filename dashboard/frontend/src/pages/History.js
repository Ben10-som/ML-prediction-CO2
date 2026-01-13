import { useState, useEffect } from 'react';
import axios from 'axios';
import { History as HistoryIcon, Clock, CheckCircle2 } from 'lucide-react';
import './History.css';

function History() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data?limit=50')
            .then(res => {
                setData(res.data.predictions || []);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    const formatDate = (isoString) => {
        if (!isoString) return '-';
        return new Date(isoString).toLocaleString('fr-FR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    };

    if (loading) return <div className="loading">Chargement de l'historique...</div>;

    return (
        <div className="page history-page">
            <div className="history-header">
                <div>
                    <h2><HistoryIcon size={28} className="icon-title" /> Historique des Prédictions</h2>
                    <p>Suivi des 50 dernières estimations réalisées.</p>
                </div>
                <div className="badge-count">
                    {data.length} enregistrements
                </div>
            </div>

            <div className="table-wrapper">
                {data.length === 0 ? (
                    <div className="empty-state">
                        <Clock size={48} color="#cbd5e1" />
                        <p>Aucun historique disponible pour le moment.</p>
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Date & Heure</th>
                                <th>Année Constr.</th>
                                <th>Bâtiments</th>
                                <th>Étages</th>
                                <th>Surface (sqft)</th>
                                <th>Prédiction CO₂ (t)</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.map((row, idx) => (
                                <tr key={idx}>
                                    <td className="col-date">{formatDate(row.timestamp)}</td>
                                    <td>{row.YearBuilt}</td>
                                    <td>{row.NumberofBuildings}</td>
                                    <td>{row.NumberofFloors}</td>
                                    <td>{Number(row.PropertyGFATotal).toLocaleString()}</td>
                                    <td className="col-prediction">{Number(row.predicted_CO2).toFixed(2)}</td>
                                    <td><CheckCircle2 size={16} color="#10b981" /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}

export default History;
