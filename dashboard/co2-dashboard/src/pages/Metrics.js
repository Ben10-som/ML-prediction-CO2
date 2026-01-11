import { useEffect, useState } from 'react';
import axios from 'axios';
import './Metrics.css';

function Metrics() {
    const [metrics, setMetrics] = useState({ total_predictions: 0, average_CO2: 0 });

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/metrics')
            .then(res => setMetrics(res.data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="page metrics-page">
            <h2>Métriques du modèle</h2>
            <div className="metrics-cards">
                <div className="card">
                    <h3>Total prédictions</h3>
                    <p>{metrics.total_predictions}</p>
                </div>
                <div className="card">
                    <h3>Prédiction moyenne CO₂</h3>
                    <p>{metrics.average_CO2?.toFixed(2)}</p>
                </div>
            </div>
        </div>
    );
}

export default Metrics;
