import { useState } from 'react';
import axios from 'axios';
import './Prediction.css';

function Prediction() {
    const [formData, setFormData] = useState({
        NumberofFloors: '',
        NumberofBuildings: '',
        Age: '',
        ENERGYSTARScore: '',
        PrimaryPropertyType: 'Small- and Mid-Sized Office',
        BuildingType: 'NonResidential',
        Neighborhood: '',
        Latitude: '',
        Longitude: '',
        Has_Parking: false,
        Has_Gas: false,
        Has_Steam: false,
        PropertyGFATotal: '' // Added for better accuracy
    });
    const [prediction, setPrediction] = useState(null);

    const propertyTypes = [
        'Hotel', 'Other', 'Mixed Use Property', 'University',
        'Small- and Mid-Sized Office', 'Self-Storage Facility',
        'K-12 School', 'Large Office', 'Medical Office', 'Retail Store',
        'Hospital', 'Warehouse', 'Distribution Center', 'Worship Facility',
        'Supermarket / Grocery Store', 'Laboratory',
        'Refrigerated Warehouse', 'Restaurant'
    ];

    const handleChange = (e) => {
        const value = e.target.type === 'checkbox' ? (e.target.checked ? 1 : 0) : e.target.value;
        setFormData({ ...formData, [e.target.name]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Convert types for API
            const payload = {
                ...formData,
                NumberofFloors: parseInt(formData.NumberofFloors),
                NumberofBuildings: parseInt(formData.NumberofBuildings),
                Age: parseFloat(formData.Age),
                ENERGYSTARScore: formData.ENERGYSTARScore ? parseFloat(formData.ENERGYSTARScore) : null,
                Latitude: parseFloat(formData.Latitude),
                Longitude: parseFloat(formData.Longitude),
                Has_Parking: formData.Has_Parking ? 1 : 0,
                Has_Gas: formData.Has_Gas ? 1 : 0,
                Has_Steam: formData.Has_Steam ? 1 : 0,
                PropertyGFATotal: formData.PropertyGFATotal ? parseFloat(formData.PropertyGFATotal) : null
            };

            const res = await axios.post('http://127.0.0.1:8000/predict', payload);
            setPrediction(res.data.prediction_CO2);
        } catch (error) {
            console.error(error);
            alert("Erreur lors de la prédiction: " + (error.response?.data?.detail || error.message));
        }
    }

    return (
        <div className="page prediction-page">
            <h2>Prédiction CO₂</h2>
            <form onSubmit={handleSubmit} className="prediction-form">
                <div className="form-group">
                    <label>Surface Totale (sqft):</label>
                    <input type="number" name="PropertyGFATotal" value={formData.PropertyGFATotal} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Nombre d'étages:</label>
                    <input type="number" name="NumberofFloors" value={formData.NumberofFloors} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Nombre de bâtiments:</label>
                    <input type="number" name="NumberofBuildings" value={formData.NumberofBuildings} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Âge du bâtiment:</label>
                    <input type="number" name="Age" value={formData.Age} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Score ENERGY STAR (optionnel):</label>
                    <input type="number" name="ENERGYSTARScore" value={formData.ENERGYSTARScore} onChange={handleChange} />
                </div>

                <div className="form-group">
                    <label>Type de propriété:</label>
                    <select name="PrimaryPropertyType" value={formData.PrimaryPropertyType} onChange={handleChange}>
                        {propertyTypes.map(type => (
                            <option key={type} value={type}>{type}</option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Type de bâtiment (ex: NonResidential):</label>
                    <input type="text" name="BuildingType" value={formData.BuildingType} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Quartier (Neighborhood):</label>
                    <input type="text" name="Neighborhood" value={formData.Neighborhood} onChange={handleChange} required />
                </div>

                <div className="form-group">
                    <label>Latitude:</label>
                    <input type="number" step="0.0001" name="Latitude" value={formData.Latitude} onChange={handleChange} required />
                </div>
                <div className="form-group">
                    <label>Longitude:</label>
                    <input type="number" step="0.0001" name="Longitude" value={formData.Longitude} onChange={handleChange} required />
                </div>

                <div className="checkbox-group">
                    <label>
                        <input type="checkbox" name="Has_Parking" checked={formData.Has_Parking === 1 || formData.Has_Parking === true} onChange={handleChange} />
                        Parking ?
                    </label>
                    <label>
                        <input type="checkbox" name="Has_Gas" checked={formData.Has_Gas === 1 || formData.Has_Gas === true} onChange={handleChange} />
                        Gaz ?
                    </label>
                    <label>
                        <input type="checkbox" name="Has_Steam" checked={formData.Has_Steam === 1 || formData.Has_Steam === true} onChange={handleChange} />
                        Vapeur ?
                    </label>
                </div>

                <button type="submit">Prédire</button>
            </form>

            {prediction !== null && (
                <div className="result">
                    <h3>Prophétie : {prediction.toFixed(2)} tonnes d'émissions</h3>
                </div>
            )}
        </div>
    );
}

export default Prediction;
