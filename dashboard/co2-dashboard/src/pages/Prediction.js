import { useState } from 'react';
import axios from 'axios';
import './Prediction.css';

function Prediction() {
    const [formData, setFormData] = useState({
        YearBuilt: '', NumberofBuildings: '', NumberofFloors: '', PropertyGFATotal: ''
    });
    const [prediction, setPrediction] = useState(null);

    const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post('http://127.0.0.1:8000/predict', formData);
            setPrediction(res.data.prediction_CO2);
        } catch (error) {
            console.error(error);
            alert("Erreur lors de la prédiction");
        }
    }

    return (
        <div className="page prediction-page">
            <h2>Prédiction CO₂</h2>
            <form onSubmit={handleSubmit}>
                {Object.keys(formData).map((key) => (
                    <div key={key}>
                        <label>{key}:</label>
                        <input type="number" name={key} value={formData[key]} onChange={handleChange} />
                    </div>
                ))}
                <button type="submit">Prédire</button>
            </form>

            {prediction !== null && <div className="result"><h3>Prediction: {prediction.toFixed(2)} CO₂</h3></div>}
        </div>
    );
}

export default Prediction;
