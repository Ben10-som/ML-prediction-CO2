import './Home.css';

function Home() {
    return (
        <div className="page">
            <h1>Bienvenue sur la plateforme de prédiction CO₂ à Seattle</h1>

            <p>
                Seattle, située dans l'État de Washington aux États-Unis, est une grande ville dynamique connue pour son
                industrie technologique, son port actif et son urbanisme dense. Comme de nombreuses métropoles modernes,
                elle est confrontée à des enjeux environnementaux majeurs, notamment la qualité de l'air et les émissions
                de dioxyde de carbone (CO₂).
            </p>

            <p>
                Cette plateforme permet d'importer et d'analyser les données historiques de Seattle afin de prédire les
                émissions de CO₂ des bâtiments. Grâce à des modèles de machine learning avancés, vous pouvez visualiser
                les tendances, anticiper les impacts environnementaux et soutenir la prise de décisions éclairées pour
                réduire l'empreinte carbone de la ville.
            </p>

            <p>
                Utilisez le menu de navigation pour accéder aux pages de prédiction, consulter l'historique des résultats,
                suivre les métriques du modèle et vérifier l'état de l'API.
            </p>
        </div>
    );
}

export default Home;
