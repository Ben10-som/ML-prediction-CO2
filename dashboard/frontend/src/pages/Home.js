import { Link } from 'react-router-dom';
import { Globe, Zap, TrendingDown } from 'lucide-react';
import './Home.css';

function Home() {
    return (
        <div className="home-page">
            <section className="hero">
                <h1>Seattle Carbon AI</h1>
                <p>Planifiez l'avenir durable de Seattle grâce à l'Intelligence Artificielle.</p>
                <div className="hero-actions">
                    <Link to="/dashboard" className="btn-primary"> Analyser les données</Link>
                    <Link to="/prediction" className="btn-secondary"> Lancer une prédiction</Link>
                </div>
            </section>

            <section className="features-grid">
                <div className="feature-card">
                    <div className="icon">
                        <Globe size={48} color="#7c3aed" />
                    </div>
                    <h3>Analyse Complète</h3>
                    <p>Visualisez les émissions de GES sur une carte thermique interactive.</p>
                </div>
                <div className="feature-card">
                    <div className="icon">
                        <Zap size={48} color="#f59e0b" />
                    </div>
                    <h3>Prévisions Précises</h3>
                    <p>Estimez la consommation énergétique de futurs bâtiments.</p>
                </div>
                <div className="feature-card">
                    <div className="icon">
                        <TrendingDown size={48} color="#10b981" />
                    </div>
                    <h3>Réduction d'Impact</h3>
                    <p>Identifiez les leviers pour réduire l'empreinte carbone.</p>
                </div>
            </section>
        </div>
    );
}

export default Home;
