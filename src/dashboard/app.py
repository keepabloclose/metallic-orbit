import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from datetime import datetime

# Add root to path so we can import src
sys.path.append(os.getcwd())

from src.data.loader import DataLoader
from src.data.upcoming import FixturesFetcher
from src.engine.predictor import Predictor
from src.data.cups import CupLoader 

from src.dashboard.match_view import render_match_details
import src.dashboard.match_view
import src.engine.predictor
import src.engine.features
import src.engine.ml_engine

# Force reload of features module to pick up definition changes
# import importlib
# importlib.reload(src.engine.features)
# importlib.reload(src.engine.ml_engine) # CRITICAL: Reload this first
# importlib.reload(src.engine.predictor)
# importlib.reload(src.dashboard.match_view)

from src.engine.features import FeatureEngineer
from src.engine.patterns import PatternAnalyzer

st.set_page_config(page_title="Sports Betting EV Analyzer", layout="wide")

# --- AUTHENTICATION ---
def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] == "test" and st.session_state["password"] == "pass":
            st.session_state["authenticated"] = True
            # del st.session_state["password"]  # Don't store password
            # del st.session_state["username"]
        else:
            st.session_state["authenticated"] = False
            st.error("😕 Usuario o contraseña incorrectos")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Show Login Form
    st.title("🔒 Acceso Restringido")
    st.text_input("Usuario", key="username")
    st.text_input("Contraseña", type="password", key="password")
    
    if st.button("Entrar"):
        password_entered()
        if st.session_state.get("authenticated"):
            st.rerun()
            
    return False

# Stop execution if not authenticated
if not check_password():
    st.stop()


def go_to_match(match_data):
    st.session_state['view'] = 'match_details'
    st.session_state['selected_match'] = match_data

@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_upcoming_cached(leagues):
    fetcher = FixturesFetcher()
    return fetcher.fetch_upcoming(leagues)

@st.cache_resource
def get_predictor(data):
    return Predictor(data)

@st.cache_data(ttl=3600) # Cache for 1 hour
def load_data(leagues, seasons, version=4): # Incremented version
    loader = DataLoader()
    df = loader.fetch_data(leagues, seasons)

    if df.empty:
        return df

    try:
        cup_loader = CupLoader()
        cup_schedule = cup_loader.fetch_all_cups()
    except Exception as e:
        print(f"Warning: Could not fetch cup data: {e}")
        cup_schedule = None

    # Calculate Features
    engineer = FeatureEngineer(df)
    df = engineer.add_rest_days(cup_schedule=cup_schedule) # Pass cup data
    df = engineer.add_rolling_stats(window=5)
    df = engineer.add_recent_form(window=5) # PPG Form
    df = engineer.add_opponent_difficulty(window=5) # NEW: Opponent Strength
    df = engineer.add_relative_strength()
    return df





st.title("⚽ Analizador de Valor en Apuestas Deportivas")

# Sidebar - Configuration
st.sidebar.header("Configuración")
# Added N1 (Netherlands), B1 (Belgium), E1 (Championship) to cover expanded fixtures
league_options = ['SP1', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1']
league_names = {
    'SP1': 'La Liga (España)',
    'E0': 'Premier League (Inglaterra)',
    'E1': 'Championship (Inglaterra)',
    'D1': 'Bundesliga (Alemania)',
    'I1': 'Serie A (Italia)',
    'F1': 'Ligue 1 (Francia)',
    'P1': 'Liga Portugal',
    'N1': 'Eredivisie'
}
leagues = st.sidebar.multiselect(
    "Ligas", 
    league_options, 
    default=['SP1', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1'], 
    format_func=lambda x: league_names.get(x, x)
)
# User Request: Default last 5 seasons
seasons = st.sidebar.multiselect("Temporadas", ['2526', '2425', '2324', '2223', '2122', '2021'], default=['2526', '2425', '2324', '2223', '2122'])

if st.sidebar.button("Recargar Datos"):
    st.cache_data.clear()
    st.rerun()

@st.cache_resource
def get_predictor(data):
    return Predictor(data)

# Call with version 3 to match definition and bust cache
data = load_data(leagues, seasons, version=3)
# Initialize Predictor Globally for Match View using Cache
predictor = get_predictor(data)

st.sidebar.info(f"Cargados {len(data)} partidos.")

# ... (CSS section remains same)

# ... (Routing logic remains same)


st.markdown("""
<style>
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .mini-card {
        border-radius: 8px;
        padding: 8px 4px;
        text-align: center;
        color: #1e1e1e; /* Force dark text for contrast */
        margin-bottom: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .mini-card-header {
        font-weight: bold;
        font-size: 0.85em;
        margin-bottom: 2px;
    }
    .mini-card-sub {
        font-size: 0.75em;
        color: #444;
    }
    .mini-card-val {
        font-weight: 900;
        font-size: 1.2em;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)


# Tabs
# --- NAVIGATION STATE MANAGEMENT ---
if 'view' not in st.session_state:
    st.session_state['view'] = 'main'
if 'selected_match' not in st.session_state:
    st.session_state['selected_match'] = None

# ROUTING LOGIC
if st.session_state['view'] == 'match_details' and st.session_state['selected_match']:
    render_match_details(st.session_state['selected_match'], predictor)
    st.stop() # Stop rendering the rest of the dashboard


def go_to_main():
    st.session_state['view'] = 'main'

def go_to_match(match_data):
    st.session_state['selected_match'] = match_data
    st.session_state['view'] = 'match_details'

# --- MAIN CONTROLLER ---
if st.session_state['view'] == 'match_details':
    # This should be handled by the route check at top, but just in case
    if st.session_state['selected_match']:
        render_match_details(st.session_state['selected_match'], predictor)
        st.stop()
    else:
        go_to_main()

# ==========================================
# === STANDARD DASHBOARD (Main View) ===
# ==========================================



# Filter Sidebar (Keep existing)
# ... (Sidebar code stays inherently available)

# LOAD DATA check
if data.empty:
    st.warning("No hay datos cargados.")
    st.stop()

# Tabs
# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🚀 Predicciones en Vivo", "📈 Analizador de Partidos (H2H)", "⚖️ Análisis Arbitral", "🧪 Backtesting", "🔥 Tendencias", "📊 Estadísticas", "🎯 Estrategias AI"])



# --- TAB 1: Live Predictions ---
with tab1:
    st.header("Próximos Partidos y Sugerencias")
    
    # --- FILTERS UI ---
    with st.expander("🛠️ Filtros: Fecha y Competición", expanded=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            import datetime
            # --- DATE NAVIGATION (Minimalist) ---
            if 'current_date' not in st.session_state:
                st.session_state.current_date = datetime.date.today()
                
            # Date Utils
            cur_date = st.session_state.current_date
            
            # Navigation Row
            st.markdown("---")
            c_prev, c_display, c_next, c_today = st.columns([1, 4, 1, 2])
            
            with c_prev:
                if st.button("◀", key="nav_prev", use_container_width=True):
                    st.session_state.current_date -= datetime.timedelta(days=1)
                    st.rerun()
                    
            with c_next:
                if st.button("▶", key="nav_next", use_container_width=True):
                    st.session_state.current_date += datetime.timedelta(days=1)
                    st.rerun()
                    
            with c_display:
                # Format: "sab, 27 dic"
                weekdays = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
                months = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
                
                wd = weekdays[cur_date.weekday()]
                day = cur_date.day
                mon = months[cur_date.month - 1]
                
                display_str = f"📅 {wd}, {day} {mon}"
                if cur_date == datetime.date.today():
                    display_str += " (Hoy)"
                    
                st.markdown(f"<h3 style='text-align: center; margin: 0;'>{display_str}</h3>", unsafe_allow_html=True)

            with c_today:
                 if st.button("Hoy", key="nav_today"):
                     st.session_state.current_date = datetime.date.today()
                     st.rerun()

            # Filter Data by Single Date (Minimalist View usually focuses on one day)
            # But we can keep range logic if needed, but UI implies single day focus.
            search_date = st.session_state.current_date
            # The 'data' DataFrame's 'Date' column needs to be datetime objects for comparison
            # Assuming 'data' has a 'Date' column that can be converted to datetime.date
            # This line should be applied to the 'upcoming' DataFrame after fetching.
            # For now, we'll just set date_range for the upcoming fetcher.
            date_range = [search_date, search_date] # Simulate single day range
            
            # Hide sidebar date picker or sync it?
            # For now, we override the sidebar filter logic completely for Tab 1.
            st.markdown("---")
            
        with f_col2:
            # League Selection (Sub-selection of Sidebar)
            selected_leagues_tab1 = st.multiselect(
                "Competiciones", 
                leagues, 
                default=leagues, 
                format_func=lambda x: league_names.get(x, x),
                key="tab1_leagues_filter"
            )
            

            
    # AUTO-LOAD: User wants matches to load immediately without clicking
    # We use a session state flag or just run it if we haven't yet?
    # Actually, running it every rerun might be heavy if not cached.
    # But user explicit request: "partidos deberian estar cargados a la vez que la web".
    # We will run it if it's the first run or if filters changed.
    # For simplicity validation: We just run it. St.cache_data inside fetcher or here would be ideal but fetcher handles it.
    
    run_analysis = True # Always run on load
    
    if run_analysis:
        # Spinner only for initial fetch if needed, but keeping it smooth
        # with st.spinner("Analizando partidos del día..."): (Optional, might annoy on every interaction)
        
        # Force reload imports (Dev mode legacy, can be removed for prod speed)
        # from src.data.upcoming import FixturesFetcher
        
        # Use Cached Fetcher
        upcoming = fetch_upcoming_cached(selected_leagues_tab1)
        
        # --- DATE FILTERING ---
        if not upcoming.empty and len(date_range) == 2:
                start_date, end_date = date_range
                # Convert 'Date' column to datetime objects for comparison
                # Date format usually 'dd/mm/yyyy' from football-data/fixtures
                try:
                    upcoming['DateObj'] = pd.to_datetime(upcoming['Date'], dayfirst=True).dt.date
                    upcoming = upcoming[
                        (upcoming['DateObj'] >= start_date) & 
                        (upcoming['DateObj'] <= end_date)
                    ]
                except Exception as e:
                    st.warning(f"Error parseando fechas: {e}. Se muestran todos los resultados.")

        if not upcoming.empty:
                st.success(f"Encontrados {len(upcoming)} partidos en el rango seleccionado.")
                
                predictor = get_predictor(data)
                predictions = []
                
                # Import Patterns
                from src.engine.strategies import PREMATCH_PATTERNS

                # Advanced Pattern Evaluator using Centralized Strategies
                def evaluate_match_potential(row):
                    preds = []
                    
                    for name, cond_func, _, type_str in PREMATCH_PATTERNS:
                        if cond_func(row):
                            # Calculate specific probabilities/suggestions based on pattern type
                            prob = 0
                            suggestion = name
                            specific_odd = "N/A" # Default if odds not found
                            
                            # Custom logic for display nuances
                            if "Local Dominante" in name:
                                prob = min(95, int(row.get('HomePPG', 1.5) * 35))
                                suggestion = "Victoria Local (Alta Confianza)"
                                # Try Home Win Odds
                                odd_val = row.get('B365H') or row.get('AvgH')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Festival" in name:
                                avg_goals = row.get('HomeAvgGoalsFor',0) + row.get('AwayAvgGoalsFor',0)
                                prob = min(90, int(avg_goals * 20))
                                suggestion = "Más de 2.5 Goles"
                                # Try Over 2.5 Odds (Commonly 'B365>2.5' or 'Avg>2.5' in football-data)
                                # Note: upcoming.py might strictly return what fixturedownload gives.
                                # fixturedownload usually doesn't have O/U odds in the basic CSV, but let's try.
                                odd_val = row.get('B365>2.5') or row.get('Avg>2.5')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Seguro" in name:
                                prob = 85
                                suggestion = "Más de 1.5 Goles"
                                odd_val = row.get('B365>2.5') # Proxy if >1.5 missing
                                if pd.notna(odd_val): specific_odd = f"{odd_val} (Ref O2.5)" # Clearer label

                            elif "Choque" in name:
                                prob = 80
                                suggestion = "Victoria Local (Forma)"
                                odd_val = row.get('B365H') or row.get('AvgH')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Tarjetas" in name:
                                prob = 65
                                suggestion = "Over 4.5 Tarjetas"
                                # No standard column for card odds in simple feeds

                            elif "Visitante" in name:
                                prob = 60
                                suggestion = "Victoria Visitante o X2"
                                odd_val = row.get('B365A') or row.get('AvgA')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            else:
                                prob = 70
                                # Generic mapping check
                                if "Local" in name:
                                     odd_val = row.get('B365H') or row.get('AvgH')
                                     if pd.notna(odd_val): specific_odd = f"{odd_val}"
                                elif "Visitante" in name:
                                     odd_val = row.get('B365A') or row.get('AvgA')
                                     if pd.notna(odd_val): specific_odd = f"{odd_val}"
                            
                            preds.append({
                                'pattern': name,
                                'suggestion': suggestion,
                                'prob': prob,
                                'type': 'pattern_match',
                                'stats': row,
                                'odd': specific_odd # Add to result
                            })

                    return preds

                matches_data = []
                count_preds = 0
                
                # Instantiate TrendsAnalyzer for Form Lookups
                from src.engine.trends import TrendsAnalyzer
                trends_analyzer_forms = TrendsAnalyzer(data)

                # Process all matches first
                all_preds = []
                for idx, match in upcoming.iterrows():
                    row = predictor.predict_match(match['HomeTeam'], match['AwayTeam'])
                    
                    # Prepare display data even if prediction fails
                    display_row = match.to_dict()
                    if row:
                        display_row.update(row)
                        display_row['HasStats'] = True
                    else:
                        display_row['HasStats'] = False
                        
                    matches_data.append(display_row) # For Explorer
                    
                    if row:
                        patterns = evaluate_match_potential(row)
                        for p in patterns:
                            all_preds.append({
                                'HomeTeam': match['HomeTeam'],
                                'AwayTeam': match['AwayTeam'],
                                'Div': match['Div'],
                                'Date': match['Date'],
                                'Time': match.get('Time', 'N/A'),
                                **p,
                                **row # CRITICAL FIX: Unpack full prediction stats so they are available at top level for UI and Navigation
                            })

                # Display Logic
                if all_preds:
                    preds_df = pd.DataFrame(all_preds)
                    
                    if 'Div' in preds_df.columns:
                        grouped_preds = preds_df.groupby('Div')
                        
                        flags_map_emoji = {
                            'SP1': '🇪🇸', 'E0': '🇬🇧', 'D1': '🇩🇪', 'I1': '🇮🇹', 'F1': '🇫🇷', 'P1': '🇵🇹', 'N1': '🇳🇱'
                        }
                        
                        for div, group in grouped_preds:
                            league_name = league_names.get(div, div)
                            flag_emoji = flags_map_emoji.get(div, '⚽')
                            
                            # Deduplicate by Match (Home, Away, Date)
                            # We aggregate patterns and take the max prob
                            unique_matches = {}
                            for _, row in group.iterrows():
                                key = (row['HomeTeam'], row['AwayTeam'], row['Date'])
                                if key not in unique_matches:
                                    unique_matches[key] = {
                                        'meta': row,
                                        'patterns': []
                                    }
                                unique_matches[key]['patterns'].append({
                                    'suggestion': row['suggestion'],
                                    'prob': row['prob'],
                                    'pattern': row['pattern'],
                                    'odd': row.get('odd', 'N/A')
                                })
                            
                            with st.expander(f"{flag_emoji} {league_name} ({len(unique_matches)} partidos con oportunidades)", expanded=True):
                                for key, data_item in unique_matches.items():
                                    count_preds += 1
                                    row = data_item['meta']
                                    patterns = data_item['patterns']
                                    
                                    # Sort patterns by probability desc
                                    patterns = sorted(patterns, key=lambda x: x['prob'], reverse=True)
                                    best_pattern = patterns[0]
                                    
                                    with st.container(border=True):
                                        c1, c2, c3 = st.columns([3, 2, 2])
                                        
                                        with c1:
                                            match_label = f"{row['HomeTeam']} vs {row['AwayTeam']}"
                                            st.subheader(match_label)
                                            st.caption(f"📅 {row['Date']} | ⏰ {row['Time']}")
                                            
                                        with c2:
                                            # DYNAMIC METRICS based on Best Pattern
                                            st.markdown("**Métricas Clave:**")
                                            stats = row.get('stats', {})
                                            
                                            bp_name = best_pattern['suggestion']
                                            
                                            # Default / Init
                                            m_col1, m_col2 = st.columns(2)
                                            
                                            # Customize based on pattern keywords
                                            if "Local" in bp_name or "Victoria" in bp_name or "Choque" in bp_name or "Visitante" in bp_name:
                                                # Show Result Streak
                                                form_h = trends_analyzer_forms.get_recent_form(row['HomeTeam'])
                                                form_a = trends_analyzer_forms.get_recent_form(row['AwayTeam'])
                                                
                                                m_col1.metric("Forma 🏠 (L5)", form_h)
                                                m_col2.metric("Forma ✈️ (L5)", form_a)
                                                
                                            elif "Córner" in bp_name:
                                                # Corners: For / Against
                                                h_for = stats.get('HomeAvgCornersFor', 0)
                                                h_ag = stats.get('HomeAvgCornersAgainst', 0)
                                                a_for = stats.get('AwayAvgCornersFor', 0)
                                                a_ag = stats.get('AwayAvgCornersAgainst', 0)
                                                
                                                m_col1.metric(f"{row['HomeTeam']}", f"{h_for:.1f} / {h_ag:.1f} (C/Enc)")
                                                m_col2.metric(f"{row['AwayTeam']}", f"{a_for:.1f} / {a_ag:.1f} (C/Enc)")


                                            elif "Goles" in bp_name or "Over" in bp_name or "Seguro" in bp_name or "BTTS" in bp_name:
                                                # Goals: Scored / Conceded
                                                h_gf = stats.get('HomeAvgGoalsFor', 0)
                                                h_ga = stats.get('HomeAvgGoalsAgainst', 0)
                                                a_gf = stats.get('AwayAvgGoalsFor', 0)
                                                a_ga = stats.get('AwayAvgGoalsAgainst', 0)
                                                
                                                m_col1.metric("🏠 Goles (F/C)", f"{h_gf:.1f} / {h_ga:.1f}")
                                                m_col2.metric("✈️ Goles (F/C)", f"{a_gf:.1f} / {a_ga:.1f}")
                                            
                                            # Quote Display
                                            st.markdown("---")
                                            q_col1, q_col2 = st.columns(2)
                                            quote_val = row.get('odd')
                                            
                                            if quote_val:
                                                # Check if it's real (heuristic: not None)
                                                if isinstance(quote_val, (int, float)) and quote_val > 1.01:
                                                    q_col1.markdown(f"**Cuota:** `{quote_val}` 💰")
                                                else:
                                                    q_col1.caption("Cuota no disp.")
                                            else:
                                                q_col1.caption("Cuota no disp.")
                                                
                                            # Confidence Bar
                                            st.progress(min(int(best_pattern['prob'] * 100), 100))
                                            st.caption("Confianza del Modelo")

                                            
                                            # Odds Section (General)
                                            st.markdown("**Cuotas (1X2):**")
                                            odds_h = row.get('B365H') or row.get('AvgH')
                                            odds_d = row.get('B365D') or row.get('AvgD')
                                            odds_a = row.get('B365A') or row.get('AvgA')
                                            
                                            if pd.notna(odds_h):
                                                c_o1, c_o2, c_o3 = st.columns(3)
                                                c_o1.metric("1", f"{odds_h}")
                                                c_o2.metric("X", f"{odds_d}")
                                                c_o3.metric("2", f"{odds_a}")
                                            else:
                                                st.caption("Cuota no disponible todavía")
                                            
                                        with c3:
                                            # AI PREDICTION (ML Engine)
                                            # 1. SHOW PATTERNS (The "Why")
                                            for p in patterns:
                                                color = "green" if p['prob'] > 75 else "orange"
                                                odd_display = f" - 💰 {p['odd']}" if p.get('odd') and p['odd'] != 'N/A' else ""
                                                st.markdown(f":{color}[**{p['suggestion']}**] ({p['prob']}%){odd_display}")
                                            
                                            st.divider()

                                            # 2. SHOW AI PREDICTIONS (Context)
                                            st.markdown("**🧠 Predicción IA:**")
                                            
                                            # Correct Score (Always try to show)
                                            pred_h_goals = int(row.get('REG_HomeGoals', 0))
                                            pred_a_goals = int(row.get('REG_AwayGoals', 0))
                                            st.markdown(f"**🎯 Marcador:** `{pred_h_goals} - {pred_a_goals}`")

                                            # Win Probs
                                            p_home = row.get('ML_HomeWin', 0)
                                            p_draw = row.get('ML_Draw', 0)
                                            p_away = row.get('ML_AwayWin', 0)

                                            if p_home + p_draw + p_away > 0:
                                                 st.progress(p_home, text=f"🏠 {row['HomeTeam']} {p_home}%")
                                                 # st.progress(p_draw, text=f"🤝 Empate {p_draw}%") # Optional for space
                                                 st.progress(p_away, text=f"✈️ {row['AwayTeam']} {p_away}%")
                                            
                                            # BUTTON TO GO TO MATCH VIEW
                                            m_data = row.to_dict()
                                            b_key = f"btn_match_{row['HomeTeam']}_{row['AwayTeam']}_group"
                                            st.button("Ver Partido ➡️", key=b_key, on_click=go_to_match, args=(m_data,))

                                        


                if count_preds == 0:
                    st.info("No se detectaron patrones de 'Alto Valor' (Filtros Estrictos). Revisa el explorador abajo.")
                else:
                    st.success(f"Detectadas {count_preds} oportunidades destacadas.")
                # CSS for Vertical Alignment and Compactness
                st.markdown("""
                <style>
                    /* Vertically center column content */
                    [data-testid="stHorizontalBlock"] {
                        align-items: center;
                    }
                    /* Compact buttons */
                    .stButton button {
                        padding: 0.25rem 0.75rem;
                        font-size: 0.8rem;
                    }
                </style>
                """, unsafe_allow_html=True)

                st.subheader("📋 Cartelera del Día (Vista Premium)")
                
                from src.dashboard.premium_row import render_premium_match_row
                from src.engine.trends_scanner import TrendScanner
                
                # Initialize Scanner
                scanner = TrendScanner()

                if matches_data:
                    # 1. Sort Data: Date -> Div -> Time
                    md_df = pd.DataFrame(matches_data)
                    md_df['Date'] = pd.to_datetime(md_df['Date'])
                    
                    # ROBUST SORT
                    sort_keys = ['Date']
                    if 'Div' in md_df.columns: sort_keys.append('Div')
                    if 'Time' in md_df.columns: sort_keys.append('Time')
                    
                    md_df = md_df.sort_values(by=sort_keys)
                    
                    # 2. Render Loop
                    # Group by League for cleaner UI?
                    if 'Div' in md_df.columns:
                        grouped = md_df.groupby('Div')
                        
                        flags_map_emoji = {
                            'SP1': '🇪🇸', 'E0': '🇬🇧', 'D1': '🇩🇪', 'I1': '🇮🇹', 'F1': '🇫🇷', 'P1': '🇵🇹', 'N1': '🇳🇱'
                        }
                        
                        # Use API-Sports Logos (High Reliability)
                        league_logos = {
                            'E0': "https://media.api-sports.io/football/leagues/39.png",   # Premier League
                            'SP1': "https://media.api-sports.io/football/leagues/140.png", # La Liga
                            'I1': "https://media.api-sports.io/football/leagues/135.png",  # Serie A
                            'D1': "https://media.api-sports.io/football/leagues/78.png",   # Bundesliga
                            'F1': "https://media.api-sports.io/football/leagues/61.png",   # Ligue 1
                            'N1': "https://media.api-sports.io/football/leagues/88.png",   # Eredivisie
                            'P1': "https://media.api-sports.io/football/leagues/94.png",   # Liga Portugal
                        }
                        default_logo = "https://cdn-icons-png.flaticon.com/512/53/53283.png"

                        for div, group in grouped:
                            league_name = league_names.get(div, div)
                            flag = flags_map_emoji.get(div, '')
                            logo = league_logos.get(div, default_logo)
                            
                            # Custom Header (Minimalist Strip)
                            st.markdown(f"""
                            <div style="
                                display: flex; 
                                align-items: center; 
                                background-color: #f8f9fa; 
                                padding: 10px 16px; 
                                border-radius: 8px; 
                                margin: 20px 0 10px 0; 
                                border-left: 5px solid #ff4b4b;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                            ">
                                <img src="{logo}" onerror="this.src='{default_logo}'" style="width: 32px; height: 32px; margin-right: 12px; object-fit: contain;">
                                <span style="font-weight: 700; font-size: 1.25em; color: #31333F;">{league_name}</span>
                                <span style="margin-left: 10px; font-size: 1.5em;">{flag}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            for _, m_row in group.iterrows():
                                # Convert Series to Dict
                                m_dict = m_row.to_dict()
                                
                                # SCAN TRENDS ON THE FLY
                                h_trends = scanner.scan(m_dict['HomeTeam'], data, context='home')
                                a_trends = scanner.scan(m_dict['AwayTeam'], data, context='away')
                                
                                # Pass dependencies
                                render_premium_match_row(
                                    m_dict, 
                                    predictor, 
                                    None, 
                                    trends_analyzer_forms,
                                    go_to_match,
                                    home_trends=h_trends,
                                    away_trends=a_trends
                                )
                    else:
                        # Fallback no Div grouping
                        st.caption("Partidos Varios")
                        for _, m_row in md_df.iterrows():
                            # SCAN TRENDS
                            h_trends = scanner.scan(m_row['HomeTeam'], data, context='home')
                            a_trends = scanner.scan(m_row['AwayTeam'], data, context='away')
                            
                            render_premium_match_row(m_row.to_dict(), predictor, None, trends_analyzer_forms, go_to_match, home_trends=h_trends, away_trends=a_trends)
                else:
                    st.info("No hay partidos para la fecha seleccionada.")


# --- TAB 2: Match Analyzer (H2H) ---
with tab2:
    st.header("Analizador Cara a Cara y Forma")
    
    # Filter teams by selected league to prevent "Alaves vs Aston Villa" unless user selects multiple leagues
    # We should probably let user select a League first for this view
    
    col_league, col1, col2 = st.columns(3)
    
    with col_league:
        # Added key to prevent reset
        selected_league_h2h = st.selectbox("Seleccionar Competición", leagues, format_func=lambda x: league_names.get(x, x), key="h2h_league_select")
    
    # Filter data for team list
    league_data = data[data['Div'] == selected_league_h2h]
    if not league_data.empty:
        latest_season = league_data['Season'].max()
        # Show teams from the latest season only
        league_teams = sorted(league_data[league_data['Season'] == latest_season]['HomeTeam'].unique())
        st.caption(f"Mostrando equipos de la temporada: {latest_season} (Última disponible)")
    else:
        league_teams = []
    
    with col1:
        # Added key
        team_home = st.selectbox("Equipo Local", league_teams, key="h2h_home_team")
    with col2:
        # Filter opponents to same league usually
        # Added key
        team_away = st.selectbox("Equipo Visitante", league_teams, index=1 if len(league_teams) > 1 else 0, key="h2h_away_team")
        
    if team_home and team_away:
        # Period Selector
        period = st.radio("Periodo", ["Partido Completo", "1ª Parte", "2ª Parte"], horizontal=True, key="h2h_period")
        
        # Recent Form Charts
        st.subheader(f"Forma Reciente ({period})")
        
        # Context-aware Metric Options
        if period == "Partido Completo":
            metric_options = {
                'Goles (H/A)': ('FTHG', 'FTAG'),
                'Tiros a Puerta': ('HST', 'AST'),
                'Córners': ('HC', 'AC'),
                'Faltas': ('HF', 'AF'), 
                'Tarjetas (Y+R)': ('Cards', 'Cards') 
            }
        else:
             # Restricted metrics for Halves (Data usually only has Goals)
             metric_options = {
                'Goles (H/A)': ('HTHG', 'HTAG') if period == '1ª Parte' else ('HomeGoals2H', 'AwayGoals2H'),
             }
             
        selected_metric_label = st.selectbox("Seleccionar Métrica", list(metric_options.keys()), key="h2h_metric_select")
        
        # Get Home Team History
        home_games = data[(data['HomeTeam'] == team_home) | (data['AwayTeam'] == team_home)].sort_values('Date').tail(10)
        away_games = data[(data['HomeTeam'] == team_away) | (data['AwayTeam'] == team_away)].sort_values('Date').tail(10)
        
        # Prepare Data for Plot
        def get_team_metric(row, team, metric_label, period):
            # 1H/2H Special Logic (Goals Only)
            if period != "Partido Completo":
                 # Determine if Home or Away role
                 is_home = (row['HomeTeam'] == team)
                 
                 # 1H Goals
                 if period == "1ª Parte":
                     return row['FTHG'] if is_home else row['FTAG'] # Wait, this uses FT. Fix to HTHG.
                     # Actually check if HTHG exists
                     if 'HTHG' not in row: return 0
                     return row['HTHG'] if is_home else row['HTAG']
                     
                 # 2H Goals
                 elif period == "2ª Parte":
                     if 'HTHG' not in row or 'FTHG' not in row: return 0
                     
                     g_ft = row['FTHG'] if is_home else row['FTAG']
                     g_ht = row['HTHG'] if is_home else row['HTAG']
                     return max(0, g_ft - g_ht)

            # Full Period Logic
            if metric_label == 'Tarjetas (Y+R)':
                # Sum Yellow + Red
                if row['HomeTeam'] == team:
                    return row.get('HY',0) + row.get('HR',0)
                else:
                    return row.get('AY',0) + row.get('AR',0)
            
            # Standard Tuple Mapping
            if metric_label in metric_options:
                col_home, col_away = metric_options[metric_label]
                if row['HomeTeam'] == team:
                    return row.get(col_home, 0)
                else:
                    return row.get(col_away, 0)
            return 0
            
        home_games['Value'] = home_games.apply(lambda x: get_team_metric(x, team_home, selected_metric_label, period), axis=1)
        away_games['Value'] = away_games.apply(lambda x: get_team_metric(x, team_away, selected_metric_label, period), axis=1)
        
        fig = px.line()
        fig.add_scatter(x=home_games['Date'], y=home_games['Value'], name=team_home, mode='lines+markers')
        fig.add_scatter(x=away_games['Date'], y=away_games['Value'], name=team_away, mode='lines+markers')
        fig.update_layout(title=f"Evolución de {selected_metric_label} (Últimos 10) - {period}")
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison of Season Stats (Like Match View but here)
        st.subheader("Comparativa Global (Temporada Actual)")
        
        def get_season_stats(team_name):
            matches = data[(data['HomeTeam'] == team_name) | (data['AwayTeam'] == team_name)]
            if matches.empty: return None
            
            # Stats depend on period too? Ideally yes, but let's stick to Full Match for this table to avoid complexity overload
            # Or disable table if not full match? 
            # User request was "quiero que me permita ver tambien si se puede para filtrar por priemra y segunda parte, esto tambien aplicarlo al apartado de estadisticas"
            # It's better to show N/A or just Goals for 1H/2H in the table.
            
            stats = {}
            
            if period == "Partido Completo":
                 stats = {
                    'Goles Fav': matches.apply(lambda x: x['FTHG'] if x['HomeTeam'] == team_name else x['FTAG'], axis=1).mean(),
                    'Goles Con': matches.apply(lambda x: x['FTAG'] if x['HomeTeam'] == team_name else x['FTHG'], axis=1).mean(),
                    'Córners': matches.apply(lambda x: x['HC'] if x['HomeTeam'] == team_name and 'HC' in x else (x['AC'] if 'AC' in x else 0), axis=1).mean(),
                    'Tarjetas': matches.apply(lambda x: (x['HY'] + x['HR']) if x['HomeTeam'] == team_name and 'HY' in x else (x['AY'] + x['AR']), axis=1).mean(),
                    'Tiros Puerta': matches.apply(lambda x: x['HST'] if x['HomeTeam'] == team_name and 'HST' in x else (x['AST'] if 'AST' in x else 0), axis=1).mean()
                }
            elif period == "1ª Parte":
                # Only Goals
                 stats = {
                    'Goles Fav (1H)': matches.apply(lambda x: x.get('HTHG',0) if x['HomeTeam'] == team_name else x.get('HTAG',0), axis=1).mean(),
                    'Goles Con (1H)': matches.apply(lambda x: x.get('HTAG',0) if x['HomeTeam'] == team_name else x.get('HTHG',0), axis=1).mean(),
                }
            elif period == "2ª Parte":
                 stats = {
                    'Goles Fav (2H)': matches.apply(lambda x: (x.get('FTHG',0)-x.get('HTHG',0)) if x['HomeTeam'] == team_name else (x.get('FTAG',0)-x.get('HTAG',0)), axis=1).mean(),
                    'Goles Con (2H)': matches.apply(lambda x: (x.get('FTAG',0)-x.get('HTAG',0)) if x['HomeTeam'] == team_name else (x.get('FTHG',0)-x.get('HTHG',0)), axis=1).mean(),
                }
            
            return stats

        s_home = get_season_stats(team_home)
        s_away = get_season_stats(team_away)
        
        if s_home and s_away:
            # Create a nice dataframe for comparison
            # Transpose to have Metrics as rows, Teams as columns
            comp_df = pd.DataFrame([s_home, s_away], index=[team_home, team_away]).T
            comp_df.columns = [team_home, team_away]
            st.table(comp_df.style.format("{:.2f}"))
        
        # H2H Matches (USING NEW ENGINE)
        st.subheader("Últimos Enfrentamientos Directos (Historial Completo)")
        
        from src.engine.h2h import H2HManager
        h2h_manager = H2HManager(data)
        
        h2h_matches = h2h_manager.get_h2h_matches(team_home, team_away)
        
        if not h2h_matches.empty:
            summary = h2h_manager.get_h2h_summary(team_home, team_away)
            
            # Display Summary Metrics
            c_sum1, c_sum2, c_sum3 = st.columns(3)
            c_sum1.metric(f"Victorias {team_home}", summary['HomeWins'])
            c_sum2.metric("Empates", summary['Draws'])
            c_sum3.metric(f"Victorias {team_away}", summary['AwayWins'])
            
            # Display Formatted Table
            df_display = h2h_manager.format_for_display(h2h_matches)
            
            st.dataframe(
                df_display.style.apply(lambda x: ['background-color: #d4edda' if x['Res'] == 'H' and x['Local'] == team_home else ('background-color: #f8d7da' if x['Res'] == 'A' and x['Local'] == team_home else '') for i in x], axis=1),
                use_container_width=True,
                hide_index=True
            )
            st.caption("📝 Historial completo cargado desde la base de datos.")
            
        else:
            st.info(f"No hay enfrentamientos previos registrados entre {team_home} y {team_away} en la base de datos actual.")
            st.caption("Nota: Asegúrese de que las temporadas pasadas están seleccionadas en la barra lateral.")

# --- TAB 3: Referee Analyzer ---
with tab3:
    st.header("Análisis Arbitral")
    
    from src.engine.referee import RefereeAnalyzer
    
    ref_analyzer = RefereeAnalyzer(data)
    ref_summary = ref_analyzer.get_summary()
    
    if not ref_summary.empty:
        # Group by League logic
        leagues_available = ref_summary['Div'].unique() if 'Div' in ref_summary.columns else []
        
        if len(leagues_available) > 0:
            selected_ref_league = st.selectbox("Filtrar Árbitros por Liga", leagues_available, format_func=lambda x: league_names.get(x, x))
            ref_summary_filtered = ref_summary[ref_summary['Div'] == selected_ref_league]
        else:
            ref_summary_filtered = ref_summary
            
        st.subheader("Estadísticas de Árbitros (Mín. 5 Partidos)")
        
        # Rename columns for Spanish
        ref_summary_display = ref_summary_filtered.rename(columns={
            'Matches': 'Partidos',
            'AvgYellows': 'Media Amarillas',
            'AvgReds': 'Media Rojas',
            'AvgFouls': 'Media Faltas',
            'HomeFoulsAvg': 'Faltas Local',
            'AwayFoulsAvg': 'Faltas Visitante'
        })
        
        st.dataframe(ref_summary_display.style.format("{:.2f}", subset=['Media Amarillas', 'Media Rojas', 'Media Faltas', 'Faltas Local', 'Faltas Visitante']))
        
        # Referee Detail
        # Defensive check: Referee might be in index or column
        if 'Referee' in ref_summary_filtered.columns:
            ref_col = ref_summary_filtered['Referee']
        else:
            ref_col = ref_summary_filtered.index.get_level_values(0) if isinstance(ref_summary_filtered.index, pd.MultiIndex) else ref_summary_filtered.index
            
        referee_list = sorted([str(x) for x in ref_col.unique() if pd.notna(x)])
        selected_ref = st.selectbox("Detalle del Árbitro", referee_list)
        
        if selected_ref:
            ref_matches = ref_analyzer.get_referee_matches(selected_ref)
            st.subheader(f"Partidos arbitrados por {selected_ref}")
            st.dataframe(ref_matches[['Date', 'Div', 'HomeTeam', 'AwayTeam', 'HY', 'AY', 'HR', 'AR', 'HF', 'AF', 'FTHG', 'FTAG']])
    else:
        st.warning("No hay datos de árbitros disponibles.")

# --- TAB 4: Backtesting ---
with tab4:
    st.header("Resultados de Backtesting")
    
    if st.button("Ejecutar Backtest"):
        analyzer = PatternAnalyzer(data)
        
        # IMPORT LATEST STRATEGIES (PRO VERSIONS)
        # We use the centralized definitions to ensure consistency with the Predictor/Signals
        from src.engine.strategies import PREMATCH_PATTERNS
        
        # Mapping Pattern List to format scan_patterns expects
        # scan_patterns expects list of tuples: (name, cond_func, target_func, odds_col)
        # PREMATCH_PATTERNS in strategies.py is exactly this format.
        
        patterns = PREMATCH_PATTERNS
        
        # Execute Scan
        summary, details = analyzer.scan_patterns(patterns)
        
        # Format Results for Display
        if not summary.empty:
            # Rename columns matches -> Partidos, successes -> Aciertos, probability -> Tasa Acierto
            summary_display = summary.rename(columns={
                'pattern_name': 'Estrategia',
                'matches': 'Partidos',
                'successes': 'Aciertos',
                'probability': 'Tasa Acierto %',
                'roi': 'ROI (Retorno)',
                'avg_odds': 'Cuota Media',
                'EV': 'Valor Esperado (EV)'
            })
            
            # Additional formatting
            # Convert Probability to % 0-100
            # Note: The dataframe might modify the original if not copied, but here it's fine
            
            # Reorder columns
            cols_order = ['Estrategia', 'Partidos', 'Aciertos', 'Tasa Acierto %', 'Cuota Media', 'ROI (Retorno)', 'Valor Esperado (EV)']
            # Filter cols that exist
            cols_order = [c for c in cols_order if c in summary_display.columns]
            
            summary_display = summary_display[cols_order]
            
            st.dataframe(
                summary_display.style.format({
                    'Tasa Acierto %': '{:.1%}',
                    'ROI (Retorno)': '{:.1%}',
                    'Cuota Media': '{:.2f}',
                    'Valor Esperado (EV)': '{:.2f}'
                }).background_gradient(subset=['Tasa Acierto %', 'ROI (Retorno)'], cmap='RdYlGn'),
                use_container_width=True
            )
        else:
            st.warning("No se encontraron coincidencias para las estrategias seleccionadas.")
        
        # Deep dive
        pattern_select = st.selectbox("Seleccionar Patrón para Inspeccionar", summary['pattern_name'].unique())
        if pattern_select:
            st.dataframe(details[pattern_select])

# --- TAB 5: Trends & Streaks (Match View Style) ---
with tab5:
    st.header("🔥 Tendencias y Rachas")
    st.info("Vista diaria de partidos con tendencias detalladas (L5/6, BTTS, Córners).")
    
    # Reload logic to pick up engine changes
    try:
        import importlib
        import src.engine.trends
        importlib.reload(src.engine.trends)
        from src.engine.trends import TrendsAnalyzer
    except Exception as e:
        st.error(f"Error reload streaks: {e}")
        from src.engine.trends import TrendsAnalyzer

    # Date Filter & Search
    with st.container(border=True):
        col_date, col_search = st.columns([1, 2])
        with col_date:
            min_date = datetime.date.today()
            selected_date_trends = st.date_input("Filtrar por Fecha", min_date, key="date_trends")
        with col_search:
            search_query_trends = st.text_input("Filtrar por Equipo o Competición", placeholder="Ej: Sporting CP, Premier League", key="search_trends")
            
    # Disable TLS warnings if any
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Logic Block
    try:     
        if not data.empty:
            with st.spinner("Buscando partidos y analizando tendencias..."):
                trends_analyzer = TrendsAnalyzer(data)
                fix_fetcher = FixturesFetcher()
                upcoming_daily = fix_fetcher.fetch_upcoming(leagues)
                
                # Filter by Date
                upcoming_daily['DateObj'] = pd.to_datetime(upcoming_daily['Date']).dt.date
                day_fixtures = upcoming_daily[upcoming_daily['DateObj'] == selected_date_trends]
                
                # Filter by Search
                if search_query_trends:
                    q = search_query_trends.lower()
                    day_fixtures = day_fixtures[
                        day_fixtures['HomeTeam'].str.lower().str.contains(q) | 
                        day_fixtures['AwayTeam'].str.lower().str.contains(q) |
                        day_fixtures['Div'].str.lower().str.contains(q)
                    ]
            
            if not day_fixtures.empty:
                st.success(f"Partidos: {len(day_fixtures)}")
                
                # Group by Div
                grouped = day_fixtures.groupby('Div')
                flags_map_trends = {'SP1': '🇪🇸', 'E0': '🇬🇧', 'D1': '🇩🇪', 'I1': '🇮🇹', 'F1': '🇫🇷', 'P1': '🇵🇹', 'N1': '🇳🇱'}
                
                for div, matches in grouped:
                    league_name = league_names.get(div, div)
                    flag = flags_map_trends.get(div, '⚽')
                    
                    with st.expander(f"{flag} {league_name} ({len(matches)} partidos)", expanded=True):
                        for _, match in matches.iterrows():
                            h_team = match['HomeTeam']
                            a_team = match['AwayTeam']
                            
                            # Calculate Trends
                            trends_match = trends_analyzer.get_match_trends(h_team, a_team)
                            trends_h = trends_match['Home']
                            trends_a = trends_match['Away']
                            
                            # UI Layout: Match Header + 2 Cols
                            with st.container(border=True):
                                # Helper for logos (using simple emoji or flagcdn later if needed)
                                st.markdown(f"#### 🏟️ {h_team} vs {a_team}")
                                match_time = match.get('Time', 'N/A')
                                st.caption(f"🕒 {match_time} | 📍 {league_name}")
                                
                                c_h, c_a = st.columns(2)
                                
                                with c_h:
                                    st.markdown(f"**{h_team}**")
                                    trend_count = 0
                                    if trends_h:
                                        for t in trends_h:
                                            # Strict Pattern Match L{x}/{y}
                                            import re
                                            match = re.search(r"L(\d+)/(\d+)", t)
                                            is_strong = False
                                            if match:
                                                num, den = int(match.group(1)), int(match.group(2))
                                                if num/den >= 0.8:
                                                    is_strong = True
                                            
                                            if is_strong:
                                                st.markdown(f"- :green[{t}]")
                                                trend_count += 1
                                    
                                    if trend_count == 0:
                                        st.caption("Sin tendencias fuertes (>80%)")
                                        
                                with c_a:
                                    st.markdown(f"**{a_team}**")
                                    trend_count = 0
                                    if trends_a:
                                        for t in trends_a:
                                            import re
                                            match = re.search(r"L(\d+)/(\d+)", t)
                                            is_strong = False
                                            if match:
                                                num, den = int(match.group(1)), int(match.group(2))
                                                if num/den >= 0.8:
                                                    is_strong = True
                                            
                                            if is_strong:
                                                st.markdown(f"- :green[{t}]")
                                                trend_count += 1
                                    
                                    if trend_count == 0:
                                        st.caption("Sin tendencias fuertes (>80%)")
                                
                                # H2H Mini-Section (Optional, as per screenshot)
                                st.divider()
                                st.caption("⚔️ H2H:")
                                # (Could add basic H2H stats here if needed)
                                st.markdown(f"<span style='color:grey; font-size:0.8em'>Enfrentamientos previos no disponibles en vista rápida.</span>", unsafe_allow_html=True)

            else:
                 st.info(f"No hay partidos para la fecha {selected_date_trends} con los filtros actuales.")
        else:
             st.warning("Cargando datos...")
        
    except Exception as e:
        st.error(f"Error en Tendencias: {e}")
        import traceback
        st.code(traceback.format_exc())

# --- TAB 6: Team Statistics Search (The 'Buscador') ---
with tab6:
    st.header("📊 Buscador de Estadísticas de Equipos")
    st.markdown("Filtra y encuentra equipos que cumplan condiciones estadísticas específicas.")
    
    try:
        import importlib
        import src.engine.trends
        importlib.reload(src.engine.trends)
        from src.engine.trends import TrendSearcher
        
        if not data.empty:
            trend_engine = TrendSearcher(data)
            
            # --- SEARCH FILTERS UI ---
            with st.container(border=True):
                st.subheader("Filtros de Búsqueda")
                
                # Global Filters Row
                c_head1, c_head2 = st.columns(2)
                with c_head1:
                    st.radio("Buscar en:", ["Equipos", "Jugadores (Próximamente)"], horizontal=True, index=0, disabled=True, key="stat_scope")
                with c_head2:
                    period_stats = st.radio("Periodo", ["Partido Completo", "1ª Parte", "2ª Parte"], horizontal=True, key="stats_period")

                st.markdown("---")
                
                # Filters
                c1, c2, c3, c4 = st.columns(4)
                
                with c1:
                    # Dynamic Options based on Period
                    # If 1H/2H, only show Goals-related
                    if period_stats == "Partido Completo":
                        stat_options = {
                            'Tiros totales': 'Tiros',
                            'Tiros a puerta': 'Tiros a Puerta',
                            'Faltas cometidas': 'Faltas',
                            'Tarjetas amarillas': 'Tarjetas Amarillas',
                            'Tarjetas rojas': 'Tarjetas Rojas',
                            'Goles': 'Goles',
                            'Goles Recibidos': 'Goles Recibidos',
                            'Córners': 'Córners',
                            'Más de 0.5 goles': 'Over05',
                            'Más de 1.5 goles': 'Over15',
                            'Más de 2.5 goles': 'Over25',
                            'Ambos equipos marcan': 'BTTS'
                        }
                    else:
                        # Restricted list for Halves
                        stat_options = {
                            'Goles': 'Goles',
                            'Goles Recibidos': 'Goles Recibidos',
                            'Más de 0.5 goles': 'Over05',
                            'Más de 1.5 goles': 'Over15' # > 1.5 in a half is rare but possible
                        }
                        
                    selected_stat_label = st.selectbox("Estadística", list(stat_options.keys()), key="stat_sel")
                    selected_stat = stat_options[selected_stat_label]

                    
                with c2:
                    operator = st.selectbox("Condición", [">", ">=", "<"], index=1, key="stat_op") 
                    
                with c3:
                    threshold = st.number_input("Valor (Umbral)", min_value=0.0, value=1.5, step=0.5, key="stat_th")
                    
                with c4:
                    window_size = st.selectbox("Últimos Partidos", [2, 3, 5, 10], index=1, key="stat_win")
                    
                # Search Button
                if st.button("Buscar Equipos", type="primary", use_container_width=True, key="stat_btn"):
                    # Map Period name to Trends engine code
                    period_code = "Full"
                    if period_stats == "1ª Parte": period_code = "1H"
                    elif period_stats == "2ª Parte": period_code = "2H"
                    
                    results_df = trend_engine.search_teams(selected_stat, operator, threshold, window_size, period=period_code)
                    
                    # Perform Search
                    results = trend_engine.search_teams(
                        stat_type=selected_stat, 
                        operator=operator, 
                        value=threshold, 
                        last_n_matches=window_size
                    )
                    
                    if not results.empty:
                        st.success(f"Encontrados **{len(results)} equipos**.")
                        
                        try:
                            for div, group in results.groupby('Div'):
                                league_name = league_names.get(div, div)
                                
                                with st.expander(f"{league_name} ({len(group)})", expanded=True):
                                    cols = st.columns(3)
                                    for idx, row in group.iterrows():
                                        with cols[idx % 3]:
                                            with st.container(border=True):
                                                st.markdown(f"### {row['Team']}")
                                                st.metric(f"Media {selected_stat}", f"{row['Value']}", f"Últimos {window_size}")
                                                
                                                # Mini-Cards
                                                st.caption("Historial:")
                                                matches_to_show = row.get('LastMatches', [])[::-1]
                                                if matches_to_show:
                                                    cols_matches = st.columns(len(matches_to_show))
                                                    for idx_m, m in enumerate(matches_to_show):
                                                        with cols_matches[idx_m]:
                                                            # Safe Access to Result
                                                            res = m.get('Result', 'D')
                                                            bg = "#d4edda" if res == 'W' else "#f8d7da" if res == 'L' else "#e2e3e5"
                                                            bc = "#c3e6cb" if res == 'W' else "#f5c6cb" if res == 'L' else "#d6d8db"
                                                            
                                                            val = list(m.values())[-1]
                                                            opp = m.get('Opponent', '???')[:3].upper()
                                                            d_str = pd.to_datetime(m.get('Date', '2000-01-01')).strftime('%d/%m')
                                                            venue_icon = "🏠" if m.get('Venue') == 'Home' else "✈️"
                                                            
                                                            # Render with CSS Classes
                                                            st.markdown(f"""
                                                            <div class="mini-card" style="background-color: {bg}; border: 1px solid {bc};">
                                                                <div class="mini-card-header">{opp}</div>
                                                                <div class="mini-card-sub">{d_str} {venue_icon}</div>
                                                                <div class="mini-card-val">{val}</div>
                                                            </div>
                                                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error renderizando resultados: {e}")
                            st.write(results.head()) # Show data for debug
                    else:
                        st.warning("No se encontraron resultados.")
        else:
            st.warning("Cargando datos...")
    except Exception as e:
        st.error(e)

# --- TAB 7: AI Strategies Explorer ---
with tab7:
    st.header("🎯 Explorador de Estrategias AI")
    st.markdown("Descubre qué partidos cumplen con nuestros **Patrones Predictivos** en los próximos días.")
    
    # 1. Filters (Time Range)
    with st.container(border=True):
        st.subheader("🛠️ Configuración de Rastreo")
        
        c_filter1, c_filter2 = st.columns([2, 1])
        with c_filter1:
            time_option = st.radio(
                "Rango de Tiempo:",
                ["Próximo Día (24h)", "Próximos 7 Días", "Próximos 15 Días", "Fecha Específica"],
                horizontal=True,
                index=1
            )
            
        with c_filter2:
            st.info(f"Modo Seleccionado: {time_option}")

    # 2. Date Logic
    import datetime
    today = datetime.date.today()
    start_date = today
    end_date = today
    
    if "7 Días" in time_option:
        end_date = today + datetime.timedelta(days=7)
    elif "15 Días" in time_option:
        end_date = today + datetime.timedelta(days=15)
    elif "Fecha Específica" in time_option:
        spec_date = st.date_input("Selecciona Fecha", today)
        start_date = spec_date
        end_date = spec_date
    else: # Next Day
        end_date = today + datetime.timedelta(days=1)
        
    st.caption(f"📅 Analizando partidos desde **{start_date}** hasta **{end_date}**.")
    
    # 3. Fetch Data (Broad Search)
    if st.button("🔄 Escanear Estrategias", type="primary", use_container_width=True):
        with st.spinner("Escaneando calendario y aplicando patrones..."):
            # Fetch ALL leagues or User selection? Default to All for strategies to be useful
            # We reuse the cached fetcher
            upcoming_strat = fetch_upcoming_cached(sidebar_leagues if 'sidebar_leagues' in locals() else leagues)
            
            if not upcoming_strat.empty:
                # Filter by Date Range
                try:
                    upcoming_strat['DateObj'] = pd.to_datetime(upcoming_strat['Date'], dayfirst=True).dt.date
                    mask = (upcoming_strat['DateObj'] >= start_date) & (upcoming_strat['DateObj'] <= end_date)
                    matches_pool = upcoming_strat[mask]
                except Exception as e:
                    st.error(f"Error filtrando fechas: {e}")
                    matches_pool = pd.DataFrame()
                
                if not matches_pool.empty:
                    st.success(f"Analizando {len(matches_pool)} partidos programados...")
                    
                    # 4. Pattern Matching Engine
                    from src.engine.strategies import PREMATCH_PATTERNS
                    
                    # Dictionary to store matches per pattern
                    strategy_results = {name: [] for name, _, _, _ in PREMATCH_PATTERNS}
                    pattern_docs = {name: func.__doc__ for name, func, _, _ in PREMATCH_PATTERNS}
                    
                    # Predictor needed for Avg Stats lookups
                    # We might need to initialize it differently or assume 'data' is loaded globally
                    if 'predictor' not in locals():
                         predictor = get_predictor(data) # Assumes 'data' is global from top of script

                    for idx, match_row in matches_pool.iterrows():
                        # We need full stats context (prediction row) for strategies to work
                        # The strategies expect 'HomeAvgGoalsFor' etc. 
                        # We use predictor to enrich the row
                        try:
                            # This is expensive inside a loop if N is large!
                            # Optimization: Predictor uses memory lookup, fast enough for <100 matches.
                            # We pass Referee now (if available in upcoming feed)
                            ref_name = match_row.get('Referee', None)
                            analysis_row = predictor.predict_match(match_row['HomeTeam'], match_row['AwayTeam'], referee=ref_name)
                            
                            # Check each pattern
                            for name_pat, cond_func, _, _ in PREMATCH_PATTERNS:
                                # Prepare row for strategy check (features map)
                                if cond_func(analysis_row):
                                    # Add match to list
                                    strategy_results[name_pat].append({
                                        'Date': match_row['Date'],
                                        'Time': match_row.get('Time', '00:00'),
                                        'Home': match_row['HomeTeam'],
                                        'Away': match_row['AwayTeam'],
                                        'Div': match_row.get('Div', ''),
                                        'Stats': analysis_row # Keep context for display
                                    })
                        except Exception as e:
                            pass # Skip match if data missing
                            
                    # 5. Render Results (Cards)
                    st.markdown("---")
                    
                    found_any = False
                    for pat_name, matches_found in strategy_results.items():
                        count = len(matches_found)
                        
                        # Header with Count
                        header_icon = "✅" if count > 0 else "⚪"
                        
                        with st.expander(f"{header_icon} {pat_name} ({count} partidos)", expanded=(count > 0)):
                            # Docstring / Explanation
                            doc = pattern_docs.get(pat_name, "Sin definición.")
                            st.info(f"📋 **Definición**: {doc}")
                            
                            if count > 0:
                                found_any = True
                                # Display Matches nicely
                                cols = st.columns(3)
                                for i, m in enumerate(matches_found):
                                    with cols[i % 3]:
                                        with st.container(border=True):
                                            st.markdown(f"**{m['Home']}** vs **{m['Away']}**")
                                            st.caption(f"📅 {m['Date']} 🕒 {m['Time']} | {m['Div']}")
                                            
                                            # Key Metric Highlight based on Pattern Name
                                            if "Goles" in pat_name or ">2.5" in pat_name or "1.5" in pat_name:
                                                 g_proj = m['Stats'].get('HomeAvgGoalsFor',0) + m['Stats'].get('AwayAvgGoalsFor',0)
                                                 st.metric("Goles Proy. (Comb)", f"{g_proj:.2f}")
                                            elif "Local" in pat_name:
                                                 st.metric("PPG Local", f"{m['Stats'].get('HomePPG',0):.2f}")
                                            elif "Visitante" in pat_name:
                                                 st.metric("PPG Visita", f"{m['Stats'].get('AwayPPG',0):.2f}")
                                            
                    if not found_any:
                        st.warning("No se encontraron coincidencias para ninguna estrategia en este rango de fechas.")
                        
                else:
                    st.warning("No hay partidos en el rango de fechas seleccionado.")
            else:
                st.error("No se pudieron cargar partidos próximos (Error de Red o Sin Datos).")
