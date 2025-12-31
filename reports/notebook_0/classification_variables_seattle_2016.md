
## 1. Identification et localisation

Ces variables servent à identifier le bâtiment de manière unique et à le situer géographiquement.

| Variable | Type | Description |
| --- | --- | --- |
| **OSEBuildingID** | Numérique (ID) | Identifiant unique de la propriété. |
| **PropertyName** | Texte | Nom officiel du bâtiment. |
| **TaxParcelIdentificationNumber** | Texte | Identifiant fiscal de la parcelle (King County). |
| **Address** | Texte | Adresse physique. |
| **City** | Texte | Ville (Seattle). |
| **State** | Texte | État (WA). |
| **ZipCode** | Catégoriel | Code postal. |
| **CouncilDistrictCode** | Catégoriel | District municipal (1 à 7). |
| **Neighborhood** | Catégoriel | Zone de quartier définie par la ville. |
| **Latitude** | Numérique | Coordonnée géographique nord-sud. |
| **Longitude** | Numérique | Coordonnée géographique est-ouest. |

---

## 2. Caractéristiques morphologiques et temporelles

Variables décrivant la structure physique et l'âge du bâtiment.

| Variable | Type | Description |
| --- | --- | --- |
| **DataYear** | Temporel | Année de l'enregistrement (2016). |
| **YearBuilt** | Temporel | Année de construction ou de rénovation majeure. |
| **NumberofBuildings** | Numérique | Nombre de bâtiments sur le site. |
| **NumberofFloors** | Numérique | Nombre d'étages du bâtiment. |
| **PropertyGFATotal** | Numérique | Surface totale (Bâtiment + Parking) en pieds carrés. |
| **PropertyGFABuilding(s)** | Numérique | Surface brute hors parking. |
| **PropertyGFAParking** | Numérique | Surface totale des parkings. |

---

## 3. Typologie et usage des sols

Classification du bâtiment selon son activité principale et secondaire.

| Variable | Type | Description |
| --- | --- | --- |
| **BuildingType** | Catégoriel | Classification globale (ex: NonResidential, Campus). |
| **PrimaryPropertyType** | Catégoriel | Usage principal (>50%) selon Portfolio Manager. |
| **ListOfAllPropertyUseTypes** | Texte | Liste exhaustive de tous les usages sur le site. |
| **LargestPropertyUseType** | Catégoriel | Usage occupant la plus grande surface. |
| **LargestPropertyUseTypeGFA** | Numérique | Surface associée à l'usage le plus important. |
| **SecondLargestPropertyUseType** | Catégoriel | Deuxième usage par importance de surface. |
| **SecondLargestPropertyUseTypeGFA** | Numérique | Surface associée au deuxième usage. |
| **ThirdLargestPropertyUseType** | Catégoriel | Troisième usage par importance de surface. |
| **ThirdLargestPropertyUseTypeGFA** | Numérique | Surface associée au troisième usage. |

---

## 4. Performance et Certification

Indicateurs d'efficacité énergétique et labels environnementaux.

| Variable | Type | Description |
| --- | --- | --- |
| **ENERGYSTARScore** | Numérique (0-100) | Score de performance relative (EPA). |
| **YearsENERGYSTARCertified** | Texte | Historique des années de certification Energy Star. |

---

## 5. Intensité d'usage de l'Énergie (EUI)

Ratios de consommation par unité de surface, normalisés ou non (Indicateurs clés de performance).

| Variable | Type | Unité | Description |
| --- | --- | --- | --- |
| **SiteEUI(kBtu/sf)** | Numérique | kBtu/sq.ft | Énergie consommée sur site par pied carré. |
| **SiteEUIWN(kBtu/sf)** | Numérique | kBtu/sq.ft | EUI du site normalisé selon la météo. |
| **SourceEUI(kBtu/sf)** | Numérique | kBtu/sq.ft | Énergie à la source (inclut pertes réseau) par pied carré. |
| **SourceEUIWN(kBtu/sf)** | Numérique | kBtu/sq.ft | Source EUI normalisé selon la météo. |

---

## 6. Consommation Énergétique par source

Volumes de consommation bruts selon le type d'énergie.

| Variable | Type | Unité | Description |
| --- | --- | --- | --- |
| **SiteEnergyUse(kBtu)** | Numérique | kBtu | Consommation totale annuelle du site. |
| **SiteEnergyUseWN(kBtu)** | Numérique | kBtu | Consommation totale normalisée (météo). |
| **Electricity(kWh)** | Numérique | kWh | Consommation électrique brute. |
| **Electricity(kBtu)** | Numérique | kBtu | Consommation électrique convertie en kBtu. |
| **NaturalGas(therms)** | Numérique | therms | Consommation de gaz naturel brute. |
| **NaturalGas(kBtu)** | Numérique | kBtu | Consommation de gaz naturel convertie en kBtu. |
| **SteamUse(kBtu)** | Numérique | kBtu | Consommation de vapeur urbaine. |

---

## 7. Émissions de gaz à effet de serre 

Mesure de l'impact environnemental du bâtiment.

| Variable | Type | Unité | Description |
| --- | --- | --- | --- |
| **TotalGHGEmissions** | Numérique | Tonnes CO2e | Émissions totales de gaz à effet de serre. |
| **GHGEmissionsIntensity** | Numérique | kg CO2e/sq.ft | Émissions par unité de surface. |

---

## 8. qualité des données et conformité

Variables indiquant la fiabilité des informations et l'état réglementaire.

| Variable | Type | Description |
| --- | --- | --- |
| **DefaultData** | Booléen | Indique si des valeurs par défaut ont été utilisées. |
| **ComplianceStatus** | Catégoriel | Statut vis-à-vis de l'ordonnance de benchmarking. |
| **Outlier** | Catégoriel | Indique si la donnée est une valeur aberrante. |
| **Comments** | Texte | Remarques textuelles additionnelles (très peu rempli). |

---