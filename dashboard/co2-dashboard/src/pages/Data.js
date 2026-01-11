import { useState, useEffect } from 'react';
import axios from 'axios';
import './Data.css';

function Data() {
    const [data, setData] = useState([]);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/data-raw')
            .then(res => {
                console.log("Réponse API:", res.data);
                setData(res.data.raw_data || []);
            })
            .catch(err => console.error("Erreur API:", err));
    }, []);

    if (data.length === 0) return <p>Chargement des données...</p>;

    return (
        <div className="page data-page">
            <h2>Données brutes</h2>
            <table>
                <thead>
                    <tr>
                        {Object.keys(data[0]).map((key) => <th key={key}>{key}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, idx) => (
                        <tr key={idx}>
                            {Object.keys(row).map((key) => <td key={key}>{row[key]}</td>)}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default Data;
