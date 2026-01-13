import { useState } from 'react';
import axios from 'axios';
import {
    Calculator, Building2, MapPin, Search, Ruler, Activity, CheckCircle, AlertCircle,
    Zap, Flame, Warehouse, RotateCcw
} from 'lucide-react';
import './Prediction.css';

function Prediction() {
    const [formData, setFormData] = useState({
        NumberofFloors: '',
        NumberofBuildings: '',
        Age: '',
        ENERGYSTARScore: '',
        PrimaryPropertyType: 'Small- and Mid-Sized Office',
        BuildingType: 'NonResidential',
        Neighborhood: 'DOWNTOWN',
        Latitude: '',
        Longitude: '',
        Has_Parking: false,
        Has_Gas: false,
        Has_Steam: false,
        PropertyGFATotal: ''
    });
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const propertyTypes = [
        'Small- and Mid-Sized Office', 'Large Office', 'Medical Office',
        'Hotel', 'Retail Store', 'Supermarket / Grocery Store', 'Restaurant',
        'K-12 School', 'University', 'Hospital', 'Worship Facility',
        'Warehouse', 'Distribution Center', 'Refrigerated Warehouse', 'Self-Storage Facility',
        'Mixed Use Property', 'Laboratory', 'Other'
    ];

    const neighborhoods = [
        'BALLARD', 'CENTRAL', 'DELRIDGE', 'DOWNTOWN', 'EAST',
        'GREATER DUWAMISH', 'LAKE UNION', 'MAGNOLIA / QUEEN ANNE',
        'NORTHEAST', 'NORTHWEST', 'SOUTHEAST', 'SOUTHWEST'
    ];

    const handleChange = (e) => {
        const value = e.target.type === 'checkbox' ? (e.target.checked ? 1 : 0) : e.target.value;
        setFormData({ ...formData, [e.target.name]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setPrediction(null);

        try {
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
            setError(error.response?.data?.detail || error.message);
        } finally {
            setLoading(false);
        }
    }

    const resetForm = () => {
        setPrediction(null);
        setError(null);
        setFormData({
            NumberofFloors: '', NumberofBuildings: '', Age: '', ENERGYSTARScore: '',
            PrimaryPropertyType: 'Small- and Mid-Sized Office', BuildingType: 'NonResidential',
            Neighborhood: 'DOWNTOWN', Latitude: '', Longitude: '', Has_Parking: false, Has_Gas: false, Has_Steam: false, PropertyGFATotal: ''
        });
    }

    return (
        <div className="page prediction-page container">
            <div className="prediction-header">
                <div>
                    <h2><Calculator size={28} className="icon-title" /> Estimateur de CO₂</h2>
                    <p>Prédisez l'empreinte carbone future de vos bâtiments grâce au Machine Learning.</p>
                </div>
            </div>

            <div className="prediction-content">

                {/* FORMULAIRE */}
                <div className="form-card">
                    <form onSubmit={handleSubmit}>

                        <div className="form-section-title">
                            <Building2 size={18} /> Caractéristiques Structurelles
                        </div>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>Surface Totale (sqft)</label>
                                <div className="input-icon-wrapper">
                                    <Ruler size={16} />
                                    <input type="number" name="PropertyGFATotal" value={formData.PropertyGFATotal} onChange={handleChange} placeholder="Ex: 50000" required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Nombre d'étages</label>
                                <div className="input-icon-wrapper">
                                    <Building2 size={16} />
                                    <input type="number" name="NumberofFloors" value={formData.NumberofFloors} onChange={handleChange} placeholder="Ex: 5" required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Âge du bâtiment (ans)</label>
                                <div className="input-icon-wrapper">
                                    <Activity size={16} />
                                    <input type="number" name="Age" value={formData.Age} onChange={handleChange} placeholder="Ex: 10" required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>Nb Bâtiments</label>
                                <div className="input-icon-wrapper">
                                    <Warehouse size={16} />
                                    <input type="number" name="NumberofBuildings" value={formData.NumberofBuildings} onChange={handleChange} placeholder="Ex: 1" required />
                                </div>
                            </div>
                        </div>

                        <div className="form-section-title">
                            <Search size={18} /> Typologie & Localisation
                        </div>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>Type de Propriété</label>
                                <select name="PrimaryPropertyType" value={formData.PrimaryPropertyType} onChange={handleChange}>
                                    {propertyTypes.map(type => <option key={type} value={type}>{type}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Quartier</label>
                                <div className="input-icon-wrapper">
                                    <MapPin size={16} />
                                    <select name="Neighborhood" value={formData.Neighborhood} onChange={handleChange}>
                                        {neighborhoods.map(hood => <option key={hood} value={hood}>{hood}</option>)}
                                    </select>
                                </div>
                            </div>

                            {/* Lat/Lon grouped */}
                            <div className="form-group">
                                <label>Latitude</label>
                                <input type="number" step="0.0001" name="Latitude" value={formData.Latitude} onChange={handleChange} placeholder="47.6..." required />
                            </div>
                            <div className="form-group">
                                <label>Longitude</label>
                                <input type="number" step="0.0001" name="Longitude" value={formData.Longitude} onChange={handleChange} placeholder="-122.3..." required />
                            </div>
                        </div>

                        <div className="form-section-title">
                            <Zap size={18} /> Énergie & Services
                        </div>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>Score EnergyStar</label>
                                <input type="number" name="ENERGYSTARScore" value={formData.ENERGYSTARScore} onChange={handleChange} placeholder="0-100" />
                            </div>
                            {/* Checkboxes */}
                            <div className="checkbox-row">
                                <label className={`checkbox-label ${formData.Has_Parking ? 'checked' : ''}`}>
                                    <input type="checkbox" name="Has_Parking" checked={formData.Has_Parking} onChange={handleChange} />
                                    Parking
                                </label>
                                <label className={`checkbox-label ${formData.Has_Gas ? 'checked' : ''}`}>
                                    <input type="checkbox" name="Has_Gas" checked={formData.Has_Gas} onChange={handleChange} />
                                    <Flame size={14} className={formData.Has_Gas ? 'icon-flame' : ''} /> Gaz
                                </label>
                                <label className={`checkbox-label ${formData.Has_Steam ? 'checked' : ''}`}>
                                    <input type="checkbox" name="Has_Steam" checked={formData.Has_Steam} onChange={handleChange} />
                                    Vapeur
                                </label>
                            </div>
                        </div>

                        <div className="form-actions">
                            <button type="submit" className="btn-predict" disabled={loading}>
                                {loading ? 'Calcul en cours...' : <><Zap size={18} /> Lancer la Prédiction</>}
                            </button>
                            <button type="button" className="btn-reset" onClick={resetForm} disabled={loading}>
                                <RotateCcw size={18} />
                            </button>
                        </div>
                    </form>
                </div>

                {/* RESULTAT */}
                <div className="result-card-container">
                    {prediction !== null ? (
                        <div className="result-card success">
                            <div className="result-header">
                                <CheckCircle size={32} color="#10b981" />
                                <h3>Résultat Estimé</h3>
                            </div>
                            <div className="result-value">
                                <span className="number">{prediction.toFixed(1)}</span>
                                <span className="unit">Tonnes de CO₂</span>
                            </div>
                            <p className="result-desc">
                                Émissions annuelles estimées pour ce profil de bâtiment.
                                <br />Ceci est une prédiction basée sur le modèle ML entraîné.
                            </p>
                        </div>
                    ) : error ? (
                        <div className="result-card error">
                            <AlertCircle size={32} color="#ef4444" />
                            <h3>Erreur</h3>
                            <p>{error}</p>
                        </div>
                    ) : (
                        <div className="result-card placeholder">
                            <Activity size={48} color="#cbd5e1" />
                            <p>Remplissez le formulaire et lancez le calcul pour voir les estimations ici.</p>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}

export default Prediction;
