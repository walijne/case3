import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import datetime
import plotly.express as px
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Set Page Configuration - this should be the first Streamlit call
st.set_page_config(page_title="Vluchtvertragingen Dashboard", layout="wide")

# Load DataFrames
df_vlieg_maatschappij = pd.read_csv('samengevoegde_luchtvaartmaatschappijen.csv')
df_vlucht = pd.read_csv('airports-extended-clean.csv', delimiter=';')
df_schema = pd.read_csv('schedule_airport.csv')

# Data Cleaning and Processing
df_schema.columns = df_schema.columns.str.strip().str.lower()  # Standardizing column names
df_vlucht.columns = df_vlucht.columns.str.strip().str.lower()  # Standardizing column names

# Extracting Airline code
df_schema['airline_code'] = df_schema['flt'].str.extract('([A-Za-z]+)')
df_schema['std'] = pd.to_datetime(df_schema['std'], dayfirst=True)

# Defining Seasons Based on Dates
def get_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Lente'
    elif month in [6, 7, 8]:
        return 'Zomer'
    elif month in [9, 10, 11]:
        return 'Herfst'

df_schema['season'] = df_schema['std'].apply(get_season)

# Calculating Delay Times
df_schema['sta_std_ltc'] = pd.to_datetime(df_schema['sta_std_ltc'])
df_schema['ata_atd_ltc'] = pd.to_datetime(df_schema['ata_atd_ltc'])
df_schema['diff'] = df_schema['ata_atd_ltc'] - df_schema['sta_std_ltc']
df_schema['diff_minutes'] = df_schema['diff'].dt.total_seconds() / 60

# Adding Delay Indicator (early by more than 15 mins or late by more than 30 mins)
df_schema['delayed'] = df_schema['diff_minutes'].apply(lambda x: 1 if x < -15 or x > 30 else 0)

# Extracting Hour for Further Analysis
df_schema['hour'] = df_schema['sta_std_ltc'].dt.hour

# Maak een lookup dictionary voor ICAO naar country
icao_to_country = df_vlucht.set_index('icao')['country'].to_dict()

# Map de 'org/des' kolom in df_schema naar landnamen
df_schema['country_name'] = df_schema['org/des'].map(icao_to_country)

# Streamlit Page Setup
st.title("Vluchtvertragingen Dashboard")

# Tabs Setup
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Vluchten Analyse", "Vertraging Voorspelling", "Wereld Kaart"])

# Tab 1: Overview and Information
with tab1:
    st.header("Overzicht en Informatie")
    st.write("""
    Dit dashboard biedt een uitgebreid overzicht van vluchtvertragingen, gate en baan analyses, en voorspellingen voor vertragingen.
    Gebruik de navigatie in de zijbalk om door de verschillende analyses te bladeren:

    - **Vluchten Analyse**: Bekijk trends in het aantal vluchten per maand en analyseer de beste bestemmingen per seizoen.
    - **Vertraging Voorspelling**: Analyseer vertragingen op start- en landingsbanen en maak voorspellingen voor vertragingen.
    - **Kaartweergave**: Bekijk een kaart van de luchthavens.
    """)
    st.image("https://wereldreis.net/wp-content/uploads/2019/04/vlucht-vertraagd-claim-1024x576.jpg", caption="Bron: https://www.wereldreis.net/reistips/vervoer/vliegen-en-vliegtickets/vlucht-vertraagd/", use_column_width=True)

# Tab 2: Flights Analysis
with tab2:
    st.header("Vluchten Analyse")

    # Average Delay Per Aircraft Type
    st.subheader("Top 5 Vliegtuigtypes met Hoogste Vertraging")
    
    # Groep de data op vliegtuigtype en bereken de gemiddelde vertraging per type
    df_avg_delay_per_type = df_schema.groupby('act')['diff_minutes'].mean().reset_index()
    
    # Sorteer op gemiddelde vertraging (diff_minutes) in aflopende volgorde en selecteer de top 5
    top5_aircraft_types = df_avg_delay_per_type.sort_values(by='diff_minutes', ascending=False).head(5)

    # Maak een staafdiagram van de top 5 vliegtuigtypes met de hoogste vertraging
    fig = px.bar(top5_aircraft_types, 
                 x='act', 
                 y='diff_minutes', 
                 labels={'diff_minutes': 'Gemiddelde Vertraging (minuten)', 'act': 'Vliegtuigtype'},
                 title='Top 5 Vliegtuigtypes met Hoogste Gemiddelde Vertraging')
    fig.update_layout(title_x=0.5)  # Titel in het midden

    # Toon de grafiek in Streamlit
    st.plotly_chart(fig)

# Informatie over de Airbus A339 (A330-900neo)
    st.subheader("Airbus A339 - Langeafstandsvliegtuig")
    st.write("""
    De Airbus A339 (ook bekend als de A330-900neo) is een modern langeafstandsvliegtuig dat gebruikmaakt van de nieuwste technologieën om 
    brandstofefficiëntie te verbeteren. Het vliegtuig heeft grotere en efficiëntere vleugeltips, nieuwe Rolls-Royce-motoren, 
    en biedt meer comfort voor passagiers tijdens lange vluchten.
    """)
    st.image("https://www.condor.com/nl/fileadmin/dam/_processed_/2/2/csm_condor-a330neo-island_e8158c3abe.jpg",
             caption="Airbus A339 (A330-900neo) - Modern langeafstandsvliegtuig", use_column_width=True)

# Top 5 Vliegtuigtypes met de Minste Vertraging
    st.subheader("Top 5 Vliegtuigtypes met Minste Vertraging")
    
    # Sorteer op gemiddelde vertraging (diff_minutes) in oplopende volgorde en selecteer de top 5
    top5_aircraft_types_lowest_delay = df_avg_delay_per_type.sort_values(by='diff_minutes', ascending=True).head(5)

    # Maak een staafdiagram van de top 5 vliegtuigtypes met de minste vertraging
    fig_lowest = px.bar(top5_aircraft_types_lowest_delay, 
                        x='act', 
                        y='diff_minutes', 
                        labels={'diff_minutes': 'Gemiddelde Vertraging (minuten)', 'act': 'Vliegtuigtype'},
                        title='Top 5 Vliegtuigtypes met Minste Gemiddelde Vertraging')
    fig_lowest.update_layout(title_x=0.5)  # Titel in het midden

    # Toon de grafiek in Streamlit
    st.plotly_chart(fig_lowest)

# Top 5 Vliegtuigtypes met Minste Vertraging - Informatie over de Embraer E135
    st.subheader("Embraer ERJ 135 - Regionaal Vliegtuig")
    st.write("""
    De Embraer ERJ 135 (E135) is een klein regionaal vliegtuig dat vaak wordt gebruikt voor korte en middellange afstanden.
    Het heeft een capaciteit van ongeveer 37 passagiers en is ideaal voor regionale routes die gebruik maken van kleinere luchthavens.
    De E135 wordt vaak geprezen vanwege zijn betrouwbaarheid en brandstofefficiëntie, en vliegt meestal van en naar minder drukke luchthavens, 
    waardoor de kans op vertragingen lager is.
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/4a/CE_01_Embraer_ERJ_135LR_E135_-_BAF_%2824886877766%29.jpg",
             caption="Embraer ERJ 135 (E135) - Klein Regionaal Vliegtuig", use_column_width=True)


# Tab 3: Delay Predictions with Gauge Chart and Smooth Line Plot for Weekly Delay
with tab3:
    st.header("Vertraging Voorspelling")

    # Maak een lookup dictionary voor ICAO naar land
    icao_to_country = df_vlucht.set_index('icao')['country'].to_dict()

    # Voeg een kolom 'country' toe aan df_schema door gebruik te maken van de icao_to_country mapping
    df_schema['country'] = df_schema['org/des'].map(icao_to_country)

    # Probability of Delay Analysis
    geselecteerd_land = st.selectbox("Selecteer Land", df_schema['country'].dropna().unique())

    # Filter de dataset voor het geselecteerde land
    land_data = df_schema[df_schema['country'] == geselecteerd_land]

    maand = st.selectbox("Selecteer Maand", list(datetime.date(1900, i, 1).strftime('%B') for i in range(1, 13)))
    maand_nummer = list(datetime.date(1900, i, 1).strftime('%B') for i in range(1, 13)).index(maand) + 1
    land_data_maand = land_data[land_data['std'].dt.month == maand_nummer]
    
    if not land_data_maand.empty:
        vertraagde_vluchten_count = land_data_maand['delayed'].sum()
        totaal_vluchten = land_data_maand.shape[0]
        vertraging_kans = (vertraagde_vluchten_count / totaal_vluchten) * 100 if totaal_vluchten > 0 else 0

        # Gauge Chart for Delay Probability with Updated Threshold
        import plotly.graph_objects as go

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=vertraging_kans,
            title={'text': f"Kans op vertraging voor vluchten naar/vanuit {geselecteerd_land} in {maand}"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "red" if vertraging_kans > 20 else "green"},
                'steps': [
                    {'range': [0, 20], 'color': "lightgreen"},
                    {'range': [20, 100], 'color': "lightcoral"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20  # Threshold aangepast naar 20%
                }
            }
        ))
        st.plotly_chart(fig)
    else:
        st.write("Geen data beschikbaar voor de geselecteerde combinatie van land en maand.")

    # Vertragingen per Seizoen
    st.subheader("Gemiddelde Vertraging per Seizoen")
    
    # Groeperen op seizoen en de gemiddelde vertraging berekenen
    df_avg_delay_per_season = df_schema.groupby('season')['diff_minutes'].mean().reset_index()

    # Maak een staafdiagram van de gemiddelde vertraging per seizoen
    fig_season = px.bar(df_avg_delay_per_season,
                        x='season',
                        y='diff_minutes',
                        labels={'season': 'Seizoen', 'diff_minutes': 'Gemiddelde Vertraging (minuten)'},
                        title='Gemiddelde Vertraging per Seizoen')
                        
    fig_season.update_layout(title_x=0.5)  # Titel in het midden

    # Toon de grafiek in Streamlit
    st.plotly_chart(fig_season)

    # Beste Seizoen om te Reizen - Top 5 Bestemmingen per Geselecteerd Seizoen
    st.subheader("Top 5 Bestemmingen met de Minste Vertraging per Seizoen")

    # Groeperen per Land en Seizoen, en Gemiddelde Vertraging Berekenen
    df_avg_delay_season = df_schema.groupby(['country', 'season'])['diff_minutes'].mean().reset_index()

    # Seizoen Selectie voor Top 5
    geselecteerd_seizoen = st.selectbox("Selecteer Seizoen voor Top 5 Bestemmingen", ['Winter', 'Lente', 'Zomer', 'Herfst'])

    # Filter de dataset op basis van het geselecteerde seizoen
    season_data = df_avg_delay_season[df_avg_delay_season['season'] == geselecteerd_seizoen]

    # Sorteer op vertraging en selecteer de top 5 bestemmingen met de minste vertraging
    top_5_destinations = season_data.nsmallest(5, 'diff_minutes')

    # Visualiseer de Top 5 Bestemmingen met een Balkgrafiek
    if not top_5_destinations.empty:
        fig_top5 = px.bar(top_5_destinations,
                          x='country',
                          y='diff_minutes',
                          labels={'country': 'Bestemming', 'diff_minutes': 'Gemiddelde Vertraging (minuten)'},
                          title=f'Top 5 Bestemmingen om te Reizen in de {geselecteerd_seizoen}')
        fig_top5.update_layout(title_x=0.5)

        # Toon de grafiek in Streamlit
        st.plotly_chart(fig_top5)
    else:
        st.write("Geen gegevens beschikbaar voor het geselecteerde seizoen.")

    # Visualiseer Vertraging per Seizoen voor een Geselecteerd Land
    st.subheader("Vertraging per Seizoen voor Geselecteerd Land")

    # Selecteer een Land voor Detailanalyse
    geselecteerd_land_voor_seizoen = st.selectbox("Selecteer een Land voor Seizoensvertragingen", df_schema['country'].dropna().unique(), key="land_seizoen")

    if geselecteerd_land_voor_seizoen:
        # Filter Data voor het Geselecteerde Land
        country_season_data = df_avg_delay_season[df_avg_delay_season['country'] == geselecteerd_land_voor_seizoen]

        # Maak een Balkgrafiek voor Vertraging per Seizoen voor het Geselecteerde Land
        fig_season = px.bar(country_season_data,
                            x='season',
                            y='diff_minutes',
                            labels={'season': 'Seizoen', 'diff_minutes': 'Gemiddelde Vertraging (minuten)'},
                            title=f'Gemiddelde Vertraging per Seizoen voor {geselecteerd_land_voor_seizoen}')
        fig_season.update_layout(title_x=0.5)

        # Toon de Grafiek in Streamlit
        st.plotly_chart(fig_season)

    # Tab 4: Wereld Kaart en Interactieve Kaart met Bestemmingen
# Tab 4: Wereld Kaart en Interactieve Kaart met Bestemmingen
with tab4:
    # Toevoeging van Interactieve Kaart met Bestemmingen
    st.header("Wereld Kaart - Interactieve Marker Weergave")

    @st.cache_data
    def csv_loader(csv):
        if csv == 'Continent':
            df = pd.read_csv('continent_kans.csv', index_col=0)
            df = df.rename(columns={'Continent': 'Name'})
        elif csv == 'Vliegveld':
            df = pd.read_csv('vliegveld_kans.csv', index_col=0)
        elif csv == 'Land':
            df = pd.read_csv('land_kans.csv', index_col=0)
            df = df.rename(columns={'Country': 'Name'})
        return df

    def make_map(df, scope):
        m = folium.Map(location=[30, 10], zoom_start=2.2, tiles="cartodb positron")
        df = df[df['datum'] == scope]
        for _, row in df.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                icon=folium.Icon(color=row['te laat']),
                popup=f'Gemiddelde vliegtijd is \n {int(row["uur"])}:{int(row["minuut"])}:{int(row["seconde"])}',
                tooltip=f"<b>{row['Name']}</b>"
            ).add_to(m)
        return m

    # Keuzes voor kaart visualisatie
    col1, col2 = st.columns(2)
    with col1:
        type_kaart = st.radio("Kaart type", ('Continent', 'Land', 'Vliegveld'))
    with col2:
        seizoen = st.radio('Seizoen', ('Lente', 'Zomer', 'Herfst', 'Winter'))

    # Folium kaart in de Streamlit app
    map_data = csv_loader(type_kaart)
    st_folium(make_map(map_data, seizoen), width='100%', height=600)

    st.header("Wereld Kaart - Beste Seizoen om te Reizen per Land")

    # Maak een lookup dictionary voor ICAO naar land
    icao_to_country = df_vlucht.set_index('icao')['country'].to_dict()

    # Voeg een kolom 'country' toe aan df_schema door gebruik te maken van de icao_to_country mapping
    df_schema['country'] = df_schema['org/des'].map(icao_to_country)

    # Groeperen per Land en Seizoen, en Gemiddelde Vertraging Berekenen
    df_avg_delay_season = df_schema.groupby(['country', 'season'])['diff_minutes'].mean().reset_index()

    # Zoek het Seizoen met de Minste Vertraging per Land
    best_season_per_country = df_avg_delay_season.loc[df_avg_delay_season.groupby('country')['diff_minutes'].idxmin()]

    # Vervang de seizoenen door Engelse termen voor de visualisatie
    best_season_per_country['season'] = best_season_per_country['season'].replace({
        'Winter': 'Winter',
        'Lente': 'Spring',
        'Zomer': 'Summer',
        'Herfst': 'Autumn'
    })

    # Visualisatie met een Wereldkaart (Choropleth)
    st.write("""
    Deze wereldkaart toont voor elk land het beste seizoen om te reizen, gebaseerd op de minste vertragingen.
    """)

    # Maak een Choropleth Wereldkaart voor de Beste Seizoenen
    fig = px.choropleth(best_season_per_country,
                        locations='country',
                        locationmode='country names',
                        color='season',
                        title='Beste Seizoen om te Reizen per Land',
                        labels={'season': 'Beste Seizoen'},
                        color_discrete_map={
                            'Winter': 'lightskyblue',
                            'Spring': 'lightgreen',
                            'Summer': 'yellow',
                            'Autumn': 'orange'
                        })

    fig.update_layout(title_x=0.5, geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'))

    # Toon de Wereldkaart in Streamlit
    st.plotly_chart(fig)
