import streamlit as st
import pandas as pd
import random

# Functie om de plantenlijst uit een CSV-bestand te laden met een puntkomma als scheidingsteken
@st.cache_data
def laad_plantenlijst():
    # Lees de CSV met de juiste delimiter
    planten_df = pd.read_csv('Data/Planten.csv', delimiter=';')
    return planten_df

# Plantenlijst inladen
plant_data_df = laad_plantenlijst()

# Controleer of de vereiste kolommen aanwezig zijn
vereiste_kolommen = ['Nummer', 'Nederlands', 'Wetenschappelijke naam', 'Extra info']
if not all(kolom in plant_data_df.columns for kolom in vereiste_kolommen):
    st.error(f"Het CSV-bestand moet de volgende kolommen bevatten: {', '.join(vereiste_kolommen)}")
    st.stop()

# Zorg ervoor dat 'Nummer' numeriek is en sorteer de DataFrame
plant_data_df['Nummer'] = pd.to_numeric(plant_data_df['Nummer'], errors='coerce')
plant_data_df.dropna(subset=['Nummer'], inplace=True)
plant_data_df['Nummer'] = plant_data_df['Nummer'].astype(int)
plant_data_df.sort_values('Nummer', inplace=True)

# Initialiseer de sessiestatus variabelen
if 'correcte_antwoorden' not in st.session_state:
    st.session_state.correcte_antwoorden = 0
if 'oefen_planten' not in st.session_state:
    st.session_state.oefen_planten = None
if 'oefen_index' not in st.session_state:
    st.session_state.oefen_index = 0
if 'reset_oefening' not in st.session_state:
    st.session_state.reset_oefening = False

# Voor de Expert mode
if 'expert_plant' not in st.session_state:
    st.session_state.expert_plant = None
if 'expert_beantwoord' not in st.session_state:
    st.session_state.expert_beantwoord = False
if 'expert_input' not in st.session_state:
    st.session_state.expert_input = ''

# Inject custom CSS for progress bar color and sidebar background color
st.markdown(f"""
    <style>
    .stProgress > div > div > div > div {{
        background-color: #00652d;
    }}
    /* Aanpassen van de achtergrondkleur van de zijbalk */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: #e6ede6;
    }}
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    [role=radiogroup]{
        gap: 1rem;
        font-size:18px;
    }
    
    
    </style>
    """,unsafe_allow_html=True)


# Voeg logo toe boven de instellingen in de zijbalk
st.sidebar.image("https://www.uw-tuingids.be/assets/websitedata/uwtuingids.be/img/logo.svg", use_column_width=True)
st.sidebar.title("Navigatie")

# Voeg een link toe voor de navigatie zonder "Overzicht alle planten"
keuze = st.sidebar.selectbox(
    "Maak uw keuze",
    ["Oefen planten", "Test kennis (Multiple choice)", "Test kennis (Expert)"]
)

# Vraag de gebruiker om een startnummer en eindnummer te selecteren in de zijbalk
min_nummer = plant_data_df['Nummer'].min()
max_nummer = plant_data_df['Nummer'].max()

st.sidebar.subheader("Selecteer plantbereik")
start_nummer = st.sidebar.number_input("Start bij plantnummer:", min_value=min_nummer, max_value=max_nummer, value=min_nummer, step=1, key='start_nummer')
eind_nummer = st.sidebar.number_input("Eindig bij plantnummer:", min_value=start_nummer, max_value=max_nummer, value=min(start_nummer + 9, max_nummer), step=1, key='eind_nummer')

# Haal de geselecteerde planten op en sla ze op in sessiestatus
gefilterde_plantenlijst = plant_data_df[(plant_data_df['Nummer'] >= start_nummer) & (plant_data_df['Nummer'] <= eind_nummer)].reset_index(drop=True)

if gefilterde_plantenlijst.empty:
    st.error("Geen planten gevonden in het opgegeven bereik. Pas het bereik aan in de zijbalk.")
    st.stop()

# Functie om een nieuwe vraag te initialiseren
def initialiseer_vraag():
    # Selecteer een willekeurige plant uit de gefilterde DataFrame
    geselecteerde_plant = gefilterde_plantenlijst.sample(1).iloc[0]
    vraagtype = random.choice(["Nederlandse naam", "Wetenschappelijke naam"])

    if vraagtype == "Nederlandse naam":
        # Vraag naar Nederlandse naam, toon de wetenschappelijke naam in de vraag
        juiste_antwoord = geselecteerde_plant["Nederlands"]
        vraag = f"Wat is de Nederlandse naam van '<i>{geselecteerde_plant['Wetenschappelijke naam']}</i>'?"
        # Genereer opties met alleen Nederlandse namen uit de gefilterde lijst
        opties = [juiste_antwoord]
        while len(opties) < 3:
            optie = gefilterde_plantenlijst.sample(1)["Nederlands"].values[0]
            if optie not in opties:
                opties.append(optie)

    else:
        # Vraag naar wetenschappelijke naam, toon de Nederlandse naam in de vraag
        juiste_antwoord = geselecteerde_plant["Wetenschappelijke naam"]
        vraag = f"Wat is de wetenschappelijke naam van '{geselecteerde_plant['Nederlands']}'?"
        # Genereer opties met alleen wetenschappelijke namen uit de gefilterde lijst
        opties = [juiste_antwoord]
        while len(opties) < 3:
            optie = gefilterde_plantenlijst.sample(1)["Wetenschappelijke naam"].values[0]
            if optie not in opties:
                opties.append(optie)

    random.shuffle(opties)

    # Opslaan van de vraag, opties en juiste antwoord in sessiestatus
    st.session_state.update({
        'geselecteerde_plant': geselecteerde_plant,
        'vraagtype': vraagtype,
        'vraag': vraag,
        'opties': ["Selecteer een optie"] + opties,
        'juiste_antwoord': juiste_antwoord,
        'beantwoord': False,
        'gekozen_optie': "Selecteer een optie",
        'radiobutton_disabled': False
    })

# Functie voor de quizmodus (Multiple choice)
def quiz_multiple_choice():
    # Initialiseer vraag bij eerste keer laden of na klikken op "Volgende plant"
    if "geselecteerde_plant" not in st.session_state or st.session_state.beantwoord:
        initialiseer_vraag()

    geselecteerde_plant = st.session_state.geselecteerde_plant
    opties = st.session_state.opties
    vraag = st.session_state.vraag

    st.title("Test kennis (Multiple choice)")

    # Toon de voortgangsbalk en de huidige reeks correcte antwoorden
    voortgang = st.session_state.correcte_antwoorden / len(gefilterde_plantenlijst)
    st.progress(voortgang)
    st.write(f"Reeks correcte antwoorden: {st.session_state.correcte_antwoorden} / {len(gefilterde_plantenlijst)}")

    # Toon de vraag
    st.markdown(f"<h4>{vraag}</h4>", unsafe_allow_html=True)

    # Optioneel: Toon afbeelding van de plant als er een 'Afbeelding' kolom is
    if 'Afbeelding' in gefilterde_plantenlijst.columns and pd.notnull(geselecteerde_plant.get('Afbeelding')):
        st.image(geselecteerde_plant['Afbeelding'], width=300)

    # Toon de radioknoppen en maak ze inactief zodra een keuze is gemaakt
    gebruikersantwoord = st.radio("Selecteer de juiste optie:", opties, key="radio", disabled=st.session_state.radiobutton_disabled)

    # Controleer of een optie is geselecteerd en geef direct feedback
    if gebruikersantwoord != "Selecteer een optie" and not st.session_state.beantwoord:
        st.session_state.radiobutton_disabled = True  # Radiobuttons inactief maken

        juiste_antwoord = st.session_state.juiste_antwoord

        if gebruikersantwoord == juiste_antwoord:
            st.success("🎉 Correct!")
            st.session_state.correcte_antwoorden += 1  # Verhoog het aantal correcte antwoorden
        else:
            st.error(f"❌ Fout! Het juiste antwoord was **{juiste_antwoord}**")
            st.session_state.correcte_antwoorden = 0  # Reset bij een fout antwoord

        st.session_state.beantwoord = True  # Markeer als beantwoord

    # Toon "Volgende plant"-knop na het selecteren van een antwoord
    if st.session_state.beantwoord:
        if st.button("Volgende plant"):
            initialiseer_vraag()
            st.session_state.radio = "Selecteer een optie"  # Reset de radiobutton selectie
            st.session_state.radiobutton_disabled = False  # Reactiveren van de radiobuttons
            st.session_state.beantwoord = False  # Reset beantwoord status

# Functie voor de expert mode
def expert_mode():
    st.title("Test kennis (Expert)")

    # Initialiseer vraag bij eerste keer laden of na beantwoorden
    if "geselecteerde_plant" not in st.session_state or st.session_state.beantwoord:
        initialiseer_vraag()
        st.session_state.expert_input = ''  # Reset het invoerveld

    geselecteerde_plant = st.session_state.geselecteerde_plant
    vraag = st.session_state.vraag
    juiste_antwoord = st.session_state.juiste_antwoord

    # Toon de voortgangsbalk en de huidige reeks correcte antwoorden
    voortgang = st.session_state.correcte_antwoorden / len(gefilterde_plantenlijst)
    st.progress(voortgang)
    st.write(f"Reeks correcte antwoorden: {st.session_state.correcte_antwoorden} / {len(gefilterde_plantenlijst)}")

    # Toon de vraag
    st.markdown(f"<h4>{vraag}</h4>", unsafe_allow_html=True)

    # Optioneel: Toon afbeelding van de plant als er een 'Afbeelding' kolom is
    if 'Afbeelding' in gefilterde_plantenlijst.columns and pd.notnull(geselecteerde_plant.get('Afbeelding')):
        st.image(geselecteerde_plant['Afbeelding'], width=300)

    # Invoerveld voor het antwoord
    def check_antwoord():
        gebruikersantwoord = st.session_state.expert_input.strip()
        juiste_antwoord_norm = juiste_antwoord.strip().lower()
        gebruikersantwoord_norm = gebruikersantwoord.strip().lower()

        if gebruikersantwoord_norm == juiste_antwoord_norm:
            st.success("🎉 Correct!")
            st.session_state.correcte_antwoorden += 1
        else:
            st.error(f"❌ Fout! Het juiste antwoord was **{juiste_antwoord}**")
            st.session_state.correcte_antwoorden = 0

        st.session_state.beantwoord = True  # Markeer als beantwoord
        # Na evaluatie direct een nieuwe vraag initialiseren
        st.session_state.expert_input = ''  # Reset het invoerveld
        st.session_state.beantwoord = False
        initialiseer_vraag()

    st.text_input("Typ uw antwoord en druk op Enter:", value=st.session_state.expert_input, key='expert_input', on_change=check_antwoord)

# Aangepaste oefenmodus voor planten
def oefen_planten():
    st.title("Oefen planten")

    # Gebruik de gefilterde plantenlijst uit de sessiestatus
    geselecteerde_planten = gefilterde_plantenlijst

    # Controleer of er planten zijn geselecteerd
    if geselecteerde_planten.empty:
        st.warning("Geen planten gevonden in het opgegeven bereik.")
        return

    # Initialiseer of reset de oefening
    if st.session_state.reset_oefening or st.session_state.oefen_planten is None or not geselecteerde_planten.equals(st.session_state.oefen_planten):
        st.session_state.oefen_planten = geselecteerde_planten
        st.session_state.oefen_index = 0
        st.session_state.reset_oefening = False



    # Haal de huidige plant op na het verwerken van de knoppen
    huidige_plant = st.session_state.oefen_planten.iloc[st.session_state.oefen_index]

    # Toon de plantinformatie
    st.write(f"Plant {st.session_state.oefen_index + 1} van {len(st.session_state.oefen_planten)}")

    # Optioneel: Toon afbeelding van de plant als er een 'Afbeelding' kolom is
    if 'Afbeelding' in gefilterde_plantenlijst.columns and pd.notnull(huidige_plant.get('Afbeelding')):
        st.image(huidige_plant['Afbeelding'], use_column_width=True)

    # Toon de plantnamen met verbeterde opmaak
    st.markdown(f"<h2 style='color: #00652d;'>{huidige_plant['Nederlands']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-style: italic; color: #2b7a78;'>{huidige_plant['Wetenschappelijke naam']}</h3>", unsafe_allow_html=True)

    # Toon 'Extra info' indien beschikbaar
    extra_info = huidige_plant.get('Extra info')
    if pd.notnull(extra_info) and extra_info.strip():
        st.info(f"{extra_info}")

    # Navigatieknoppen onder de plantnamen
    col_nav = st.columns(3)
    with col_nav[0]:
        if st.button("Vorige plant"):
            if st.session_state.oefen_index > 0:
                st.session_state.oefen_index -= 1
    #with col_nav[1]:
    #    if st.button("Herstart oefening"):
    #        st.session_state.oefen_index = 0
    with col_nav[1]:
        if st.button("Volgende plant"):
            if st.session_state.oefen_index < len(st.session_state.oefen_planten) - 1:
                st.session_state.oefen_index += 1
            else:
                st.session_state.oefen_index = 0  # Terug naar het begin



# Toon de gewenste pagina afhankelijk van de selectie
if keuze == "Oefen planten":
    oefen_planten()
elif keuze == "Test kennis (Multiple choice)":
    quiz_multiple_choice()
elif keuze == "Test kennis (Expert)":
    expert_mode()
