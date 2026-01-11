import { useState, useEffect } from 'react';
import axios from 'axios';
import './History.css';

function History() {
    const [data, setData] = useState([]);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data?limit=50')
            .then(res => setData(res.data.predictions))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="page history-page">
            <h2>Historique des prédictions</h2>
            <table>
                <thead>
                    <tr>
                        <th>YearBuilt</th>
                        <th>NumberofBuildings</th>
                        <th>NumberofFloors</th>
                        <th>PropertyGFATotal</th>
                        <th>Prediction CO₂</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, idx) => (
                        <tr key={idx}>
                            <td>{row.YearBuilt}</td>
                            <td>{row.NumberofBuildings}</td>
                            <td>{row.NumberofFloors}</td>
                            <td>{row.PropertyGFATotal}</td>
                            <td>{row.predicted_CO2.toFixed(2)}</td>
                            <td>{row.timestamp}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default History;
