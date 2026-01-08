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
import importlib
import src.engine.features
import src.engine.ml_engine
import src.engine.predictor
import src.data.upcoming # Import module
import src.auth.user_manager 
import src.user.portfolio_manager # Add for reload checks 
import src.data.odds_api_client # Fix: Force reload odds client 

importlib.reload(src.engine.features)
importlib.reload(src.engine.ml_engine)
importlib.reload(src.engine.predictor)
importlib.reload(src.engine.predictor)
importlib.reload(src.user.portfolio_manager) # FORCE RELOAD PORTFOLIO
importlib.reload(src.data.odds_api_client) # FORCE RELOAD ODDS CLIENT
importlib.reload(src.auth.user_manager)
importlib.reload(src.auth.user_manager)
importlib.reload(src.data.upcoming) # FORCE RELOAD FixturesFetcher
import src.dashboard.premium_row
importlib.reload(src.dashboard.premium_row) # FORCE RELOAD UI Component


from src.engine.features import FeatureEngineer
from src.engine.patterns import PatternAnalyzer
# from src.auth.user_manager import UserManager # Moved below to ensure reload works

st.set_page_config(page_title="Sports Betting EV Analyzer", layout="wide")

# --- STATE INITIALIZATION ---
if 'view' not in st.session_state:
    st.session_state['view'] = 'main'

# --- AUTHENTICATION & USER MANAGEMENT ---
from src.auth.user_manager import UserManager
from src.dashboard.profile_view import render_profile_view
from src.dashboard.portfolio_view import render_portfolio_view, dialog_add_prediction
from src.dashboard.premium_row import render_premium_match_row
from src.engine.settlement import BetSettler # Import Settler

# Initialize Manager
user_manager = UserManager()

def init_auth():
    """Handles Login and Registration."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user"] = None

    if st.session_state["authenticated"]:
        return True

    # Show Login/Register
    st.title("🔒 Acceso Restringido")
    
    tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Usuario", key="login_user")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            submit_login = st.form_submit_button("Entrar")
            
            if submit_login:
                user = user_manager.authenticate(username, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user
                    # Load preferences into session for global access
                    st.session_state["user_prefs"] = user.get("preferences", {})
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    
    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("Usuario (Nick)", key="reg_user")
            new_pass = st.text_input("Contraseña", type="password", key="reg_pass")
            new_name = st.text_input("Nombre", key="reg_name")
            new_surname = st.text_input("Apellidos", key="reg_surname")
            new_mail = st.text_input("Email", key="reg_mail")
            
            submit_reg = st.form_submit_button("Crear Cuenta")
            
            if submit_reg:
                success, msg = user_manager.register(new_user, new_pass, new_name, new_surname, new_mail)
                if success:
                    st.success("Cuenta creada. Por favor inicia sesión.")
                else:
                    st.error(msg)
    
    return False

# Stop execution if not authenticated
if not init_auth():
    st.stop()




# --- DIALOG HANDLER (Global) ---
if 'active_prediction' in st.session_state and st.session_state['active_prediction']:
    item = st.session_state['active_prediction']
    dialog_add_prediction(user_manager, st.session_state['user']['username'], item['match'], item['strat'])
    del st.session_state['active_prediction'] 

# Callback for Match Rows
def on_strategy_click(match_data, strat_data):
    st.session_state['active_prediction'] = {
        'match': match_data,
        'strat': strat_data
    }
    st.rerun()


def go_to_match(match_data):
    st.session_state['view'] = 'match_details'
    st.session_state['selected_match'] = match_data

@st.cache_data(ttl=300) # Reduced to 5 mins
def fetch_upcoming_cached(leagues, _last_updated, cache_bust_v=10): # Increment to 10
    # _last_updated is a dummy arg to force cache invalidation when DB changes
    fetcher = FixturesFetcher()
    return fetcher.fetch_upcoming(leagues)

@st.cache_resource
def get_predictor(data, version=3):
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

    # --- GLOBAL NORMALIZATION AT SOURCE ---
    # Fixes Promoted/Relegated team history disconnects (e.g. Leicester vs Leicester City)
    from src.utils.normalization import NameNormalizer
    df['HomeTeam'] = df['HomeTeam'].apply(NameNormalizer.normalize)
    df['AwayTeam'] = df['AwayTeam'].apply(NameNormalizer.normalize)
    
    return df





# --- CONSTANTS ---
league_options = ['SP1', 'SP2', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1']
league_names = {
    'SP1': 'La Liga (España)', 'E0': 'Premier League', 'E1': 'Championship',
    'D1': 'Bundesliga', 'I1': 'Serie A', 'F1': 'Ligue 1',
    'P1': 'Liga Portugal', 'N1': 'Eredivisie', 'SP2': 'La Liga 2'
}

st.title("⚽ Analizador de Valor en Apuestas Deportivas")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    u = st.session_state.get('user', {})
    nick = u.get('username') if u else 'Guest'
    st.caption(f"👤 Hola, **{nick}**")
    
    st.header("Menú Principal")
    
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state['view'] = 'main'
        st.rerun()

    if st.button("📊 Mi Portafolio", use_container_width=True):
         st.session_state['view'] = 'portfolio'
         st.rerun()

    if st.button("💰 Balance", use_container_width=True):
         st.session_state['view'] = 'portfolio'
         st.rerun()

    if st.button("👥 Mi Perfil", use_container_width=True):
        st.session_state['view'] = 'profile'
        st.rerun()

    st.markdown("---")
    
    # Logout Button
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.rerun()

# Load User Preferences
user_prefs = st.session_state.get("user_prefs", {})
default_leagues = ['SP1', 'SP2', 'E0', 'E1', 'D1', 'I1', 'F1', 'P1', 'N1']
active_leagues = user_prefs.get("leagues", default_leagues)
active_seasons = user_prefs.get("seasons", ['2526', '2425'])

if not active_leagues:
    st.sidebar.warning("⚠️ No hay ligas seleccionadas. Ve a 'Mi Perfil' para configurar.")
    active_leagues = default_leagues # Fallback to prevent crash



# Call with version 4 (Bumped to force normalization refresh)
data = load_data(active_leagues, active_seasons, version=4)
# Initialize Predictor Globally for Match View using Cache
predictor = get_predictor(data)

st.sidebar.info(f"Cargados {len(data)} partidos.")

# --- ROUTING: PROFILE VIEW ---
if st.session_state['view'] == 'profile':
    render_profile_view(user_manager)
    st.stop()
    
# --- ROUTING: PORTFOLIO VIEW ---
if st.session_state['view'] == 'portfolio':
    # Auto-Settle on Load
    settled = BetSettler.settle_user_bets(user_manager, st.session_state['user']['username'], data)
    if settled > 0:
        st.toast(f"✅ {settled} apuestas han sido actualizadas automáticamente!")
        
    render_portfolio_view(user_manager, st.session_state['user']['username'])
    st.stop()

# ... (CSS section remains same)


st.markdown("""
<style>
    /* --- LAYOUT OPTIMIZATION --- */
    /* Reduce top padding and center content */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 98% !important;
    }
    
    /* Hide Streamlit Branding */
    /* Hide Streamlit Branding (Partial) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} */ /* Disabled to allow sidebar toggle */
    
    /* --- CARD STYLING (Containers) --- */
    /* Target Streamlit's native bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 8px !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        background-color: #FAFAFA !important; /* Subtle contrast */
        box-shadow: none !important;
        padding: 0.5rem !important; /* COMPACT PADDING */
    }
    
    /* Dark Mode Support for Containers */
    @media (prefers-color-scheme: dark) {
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            background-color: #1E1E1E !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
        }
    }

    /* --- BUTTONS (Flat Design) --- */
    .stButton button {
        box-shadow: none !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        background-color: #f0f2f6; /* Default gray */
        color: #31333F;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        border-color: #ccc !important;
        background-color: #e0e2e6 !important;
        color: #000;
    }
    /* Primary Action Button Accent */
    .stButton button:active, .stButton button:focus {
        background-color: #FF4B4B !important;
        color: white !important;
    }

    /* --- TYPOGRAPHY & METRICS --- */
    h1, h2, h3 {
        letter-spacing: -0.02em;
        font-weight: 700 !important;
    }
    
    /* Compact Metric */
    [data-testid="stMetric"] {
        background-color: transparent !important;
        padding: 0 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #666;
    }

    /* --- INPUTS --- */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
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
    st.rerun()

def go_to_match(match_data):
    st.session_state['selected_match'] = match_data
    st.session_state['view'] = 'match_details'
    st.rerun()

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
            # League Selection (Sub-selection of Sidebar)
            selected_leagues_tab1 = st.multiselect(
                "Competiciones", 
                active_leagues, 
                default=active_leagues, 
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
        
        # SSG / HYBRID DATA LOADING (Backend First)
        # ------------------------------------------------------------------
        import json
        import os
        CACHE_FILE = "data_cache/dashboard_data.json"
        backend_matches = None

        if os.path.exists(CACHE_FILE):
             try:
                 with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                     bk_data = json.load(f)
                     if bk_data and 'matches' in bk_data:
                         st.toast(f"⚡ Datos cargados del Backend ({bk_data['metadata']['last_updated']})")
                         backend_matches = pd.DataFrame(bk_data['matches'])
             except Exception as e:
                 # st.error(f"Error loading backend: {e}")
                 pass

        if backend_matches is not None and not backend_matches.empty:
            upcoming = backend_matches
        else:
            # Fallback to Live Fetch
            try:
                 db_ts = os.path.getmtime('data_cache/odds_database.csv')
            except:
                 db_ts = 0
            upcoming = fetch_upcoming_cached(selected_leagues_tab1, db_ts, cache_bust_v=17)
        
        upcoming = upcoming.copy() # SAFETY COPY
        
        # --- DATE FILTERING ---
        if not upcoming.empty and len(date_range) == 2:
                start_date, end_date = date_range
                
                try:
                    upcoming = upcoming.reset_index(drop=True) # Reset Index logic
                    
                    # Robust Date Parsing using Timestamps
                    # 1. Ensure 'Date' is datetime64 (No dayfirst=True for ISO)
                    upcoming['Date'] = pd.to_datetime(upcoming['Date'], errors='coerce')
                    
                    # 2. Extract Date String for Filtering (YYYY-MM-DD) - Most Robust
                    upcoming['DateFilter'] = upcoming['Date'].dt.strftime('%Y-%m-%d')
                    
                    # 3. Convert filter bounds to Strings
                    start_str = start_date.strftime('%Y-%m-%d')
                    end_str = end_date.strftime('%Y-%m-%d')
                    
                    # 4. Filter
                    if start_str == end_str:
                        # Exact Day Match
                        upcoming = upcoming[upcoming['DateFilter'] == start_str]
                    else:
                        # Range Match
                        upcoming = upcoming[
                            (upcoming['DateFilter'] >= start_str) & 
                            (upcoming['DateFilter'] <= end_str)
                        ]
                    
                except Exception as e:
                    st.error(f"Error filtrando por fecha: {e}")
                    # If filter fails, better to show empty than confusing Data Explosion
                    upcoming = upcoming.iloc[0:0] 



        if not upcoming.empty:
                st.success(f"Encontrados {len(upcoming)} partidos en el rango seleccionado.")
                
                # ----------------------------------
                
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
                                # Look for specific B365_Over2.5 or B365>2.5
                                odd_val = row.get('B365_Over2.5') or row.get('B365>2.5')
                                if pd.isna(odd_val): odd_val = row.get('Avg>2.5')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Seguro" in name:
                                prob = 85
                                suggestion = "Más de 1.5 Goles"
                                # Look for specific B365_Over1.5 or B365>1.5
                                odd_val = row.get('B365_Over1.5') or row.get('B365>1.5')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"
                                # REMOVED: Confusing Ref O2.5 fallback
                                # else:
                                #    pass

                            elif "Choque" in name:
                                prob = 80
                                suggestion = "Victoria Local (Forma)"
                                odd_val = row.get('B365H') or row.get('AvgH')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Tarjetas" in name:
                                # DYNAMIC CARDS STRATEGY
                                # Estimate cards based on Ref + Team Aggression
                                ref_cards = row.get('Ref_AvgCards', 4.0)
                                team_cards = (row.get('HomeAvgCards', 2.0) + row.get('AwayAvgCards', 2.0)) / 2
                                est_cards = (ref_cards + team_cards) / 2
                                
                                # Decide Line
                                if est_cards >= 4.8:
                                    suggestion = "Más de 4.5 Tarjetas"
                                    line = 4.5
                                elif est_cards >= 3.8:
                                    suggestion = "Más de 3.5 Tarjetas" 
                                    line = 3.5
                                else:
                                    suggestion = "Más de 3.5 Tarjetas (Riesgo)"
                                    line = 3.5
                                    prob = 55 # Lower confidence
                                
                                prob = min(85, int(est_cards * 15))
                                
                                # Dynamic Lookup
                                odd_val = row.get(f'B365_Cards_Over{line}')
                                if pd.notna(odd_val): specific_odd = f"{odd_val} (O{line})"

                            elif "Córner" in name:
                                # DYNAMIC CORNERS STRATEGY
                                tot_corners = row.get('HomeAvgCornersFor', 5) + row.get('AwayAvgCornersFor', 4)
                                
                                if tot_corners > 10.5:
                                    suggestion = "Más de 10.5 Córners"
                                    line = 10.5
                                elif tot_corners > 9.5:
                                    suggestion = "Más de 9.5 Córners"
                                    line = 9.5
                                else:
                                    suggestion = "Más de 8.5 Córners"
                                    line = 8.5
                                
                                prob = min(80, int(tot_corners * 8))
                                
                                odd_val = row.get(f'B365_Corners_Over{line}')
                                if pd.notna(odd_val): specific_odd = f"{odd_val} (O{line})"

                            elif "Visitante" in name:
                                prob = 60
                                suggestion = "Victoria Visitante o X2"
                                odd_val = row.get('B365A') or row.get('AvgA')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"

                            elif "Ambos Marcan" in name:
                                prob = 80
                                suggestion = "Ambos Marcan (Sí)"
                                odd_val = row.get('B365_BTTS_Yes') or row.get('B365GG')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"
                            
                            # NEW: TEAM GOALS
                            elif "Goleador Local" in name or ("Local" in name and row.get('HomeAvgGoalsFor', 0) > 1.8):
                                prob = 75
                                suggestion = "Local: Más de 1.5 Goles"
                                odd_val = row.get('B365_HomeTeam_Goals_Over1.5')
                                if pd.notna(odd_val): specific_odd = f"{odd_val}"
                            
                            elif "Goleador Visitante" in name or ("Visitante" in name and row.get('AwayAvgGoalsFor', 0) > 1.8):
                                prob = 70
                                suggestion = "Visitante: Más de 1.5 Goles"
                                odd_val = row.get('B365_AwayTeam_Goals_Over1.5')
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
                    # Extract known odds from upcoming match data to prevent synthetic overwrite
                    current_odds = {k: v for k, v in match.items() if str(k).startswith('B365')}
                    
                    # Enhanced Prediction (Pass full context to avoid 0-0/Mismatch)
                    row = predictor.predict_match_safe(
                        match['HomeTeam'], 
                        match['AwayTeam'], 
                        match_date=match.get('Date'),
                        referee=match.get('Referee'),
                        known_odds=current_odds # PASS KNOWN ODDS!
                    )
                    
                    # Prepare display data even if prediction fails
                    display_row = match.to_dict()
                    if row:
                        display_row.update(row)
                        display_row['HasStats'] = True
                    else:
                        display_row['HasStats'] = False
                        
                    matches_data.append(display_row) # For Explorer
                    
                    if row:
                        # CRITICAL FIX: Merge 'match' data (which has the Odds) into 'row' (Prediction)
                        # Predictor returns stats/probs, but 'match' has the B365 columns from upcoming.py
                        # FORCE OVERWRITE for B365 columns to ensure we display Real Odds, not Synthetic
                        for k, v in match.to_dict().items():
                            if k.startswith('B365') and pd.notna(v):
                                row[k] = v
                            elif k not in row:
                                row[k] = v
                                
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
                            'SP1': '🇪🇸', 'SP2': '🇪🇸', 'E0': '🇬🇧', 'E1': '🇬🇧', 'D1': '🇩🇪', 'I1': '🇮🇹', 'F1': '🇫🇷', 'P1': '🇵🇹', 'N1': '🇳🇱'
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
                                    
                                # DEDUPLICATION: Check if this suggestion exists
                                existing_suggestions = [p['suggestion'] for p in unique_matches[key]['patterns']]
                                if row['suggestion'] not in existing_suggestions:
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
                                    
                                    # Use Shared Component for Consistency & Compactness
                                    render_premium_match_row(
                                        row, 
                                        predictor, 
                                        None, 
                                        trends_analyzer_forms, 
                                        go_to_match, 
                                        home_trends=None, # Don't overload with generic trends if we have specific strategies
                                        away_trends=None,
                                        unique_key=f"hv_{row['HomeTeam']}_{row['AwayTeam']}",
                                        extra_strategies=patterns,
                                        strategy_callback=on_strategy_click
                                    )
                                    
                                    # st.divider() # Component adds border/padding, usually enough.



                                        


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
                
                import importlib
                import src.dashboard.premium_row
                importlib.reload(src.dashboard.premium_row)
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
                    
                    # DEDUPLICATE (Robustness)
                    md_df = md_df.drop_duplicates(subset=['HomeTeam', 'AwayTeam', 'Date'])
                    
                    # 2. Render Loop
                    # Group by League for cleaner UI?
                    if 'Div' in md_df.columns:
                        grouped = md_df.groupby('Div')
                        
                        flags_map_emoji = {
                            'SP1': '🇪🇸', 'SP2': '🇪🇸', 'E0': '🇬🇧', 'E1': '🇬🇧', 'D1': '🇩🇪', 'I1': '🇮🇹', 'F1': '🇫🇷', 'P1': '🇵🇹', 'N1': '🇳🇱'
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
                            'SP2': "https://media.api-sports.io/football/leagues/141.png", # La Liga 2
                            'E1': "https://media.api-sports.io/football/leagues/40.png"    # Championship
                        }
                        default_logo = "https://cdn-icons-png.flaticon.com/512/53/53283.png"

                        for div, group in grouped:
                            league_name = league_names.get(div, div)
                            flag = flags_map_emoji.get(div, '')
                            logo = league_logos.get(div, default_logo)
                            
                            # Custom Header (Minimalist Strip)
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
                            
                            for idx, m_row in group.iterrows():
                                # Convert Series to Dict
                                m_dict = m_row.to_dict()
                                
                                # SCAN TRENDS ON THE FLY
                                h_norm = predictor.normalize_name(m_dict['HomeTeam'])
                                a_norm = predictor.normalize_name(m_dict['AwayTeam'])
                                
                                h_trends = scanner.scan(h_norm, data, context='home')
                                a_trends = scanner.scan(a_norm, data, context='away')
                                
                                # Pass dependencies
                                render_premium_match_row(
                                    m_dict, 
                                    predictor, 
                                    None, 
                                    trends_analyzer_forms,
                                    go_to_match,
                                    home_trends=h_trends,
                                    away_trends=a_trends,
                                    unique_key=f"{div}_{idx}", # Unique ID
                                    strategy_callback=on_strategy_click
                                )
                    else:
                        # Fallback no Div grouping
                        st.caption("Partidos Varios")
                        for _, m_row in md_df.iterrows():
                            # SCAN TRENDS
                            h_norm = predictor.normalize_name(m_row['HomeTeam'])
                            a_norm = predictor.normalize_name(m_row['AwayTeam'])
                            
                            h_trends = scanner.scan(h_norm, data, context='home')
                            a_trends = scanner.scan(a_norm, data, context='away')
                            
                            render_premium_match_row(
                                m_row.to_dict(), 
                                predictor, 
                                None, 
                                trends_analyzer_forms, 
                                go_to_match, 
                                home_trends=h_trends, 
                                away_trends=a_trends,
                                strategy_callback=on_strategy_click
                            )
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
        selected_league_h2h = st.selectbox("Seleccionar Competición", active_leagues, format_func=lambda x: league_names.get(x, x), key="h2h_league_select")
    
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

            # Deep dive (Moved inside to prevent KeyError if empty)
            st.divider()
            pattern_select = st.selectbox("Seleccionar Patrón para Inspeccionar", summary['pattern_name'].unique())
            if pattern_select:
                st.dataframe(details[pattern_select])

        else:
            st.warning("No se encontraron coincidencias para las estrategias seleccionadas.")

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
                leagues = list(fix_fetcher.LEAGUE_URLS.keys())
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
            # Load Backend Data First (User Request for periodic updates)
            import json
            import os # Added import for os
            backend_data = None
            CACHE_FILE = "data_cache/dashboard_data.json"
            
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                        backend_data = json.load(f)
                except: pass
            
            used_backend = False
            matches_pool = pd.DataFrame() # Initialize

            if backend_data:
                last_u = backend_data['metadata']['last_updated']
                st.info(f"⚡ Usando datos pre-calculados del Backend (Actualizado: {last_u})")
                
                # Convert to DataFrame for filtering
                raw_matches = backend_data['matches']
                if raw_matches:
                    df_backend = pd.DataFrame(raw_matches)
                     # Filter by Date Range
                    try:
                        df_backend['DateObj'] = pd.to_datetime(df_backend['Date'], dayfirst=True).dt.date
                        mask = (df_backend['DateObj'] >= start_date) & (df_backend['DateObj'] <= end_date)
                        matches_pool = df_backend[mask]
                        used_backend = True
                    except Exception as e:
                        st.error(f"Error filtrando datos backend: {e}")
            
            # Fallback to Live Calculation if Backend failed or empty
            if not used_backend:
                st.warning("⚠️ Datos backend no disponibles. Escaneando en vivo (puede ser más lento)...")
                # Fetch ALL leagues or User selection? Default to All for strategies to be useful
                # We reuse the cached fetcher
                now_str_hour = datetime.datetime.now().strftime('%Y-%m-%d-%H')
                upcoming_strat = fetch_upcoming_cached(sidebar_leagues if 'sidebar_leagues' in locals() else leagues, now_str_hour)
                
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
                
                # Predictor needed for Avg Stats lookups if NOT using backend (or specifically for normalization?)
                # If using backend, 'Stats' are already in the row.
                if not used_backend:
                    if 'predictor' not in locals():
                         predictor = get_predictor(data) # Assumes 'data' is global from top of script

                    debug_mismatches = []
                    # Cache history teams for fast lookup
                    history_teams = set(predictor.history['HomeTeam'].unique()) | set(predictor.history['AwayTeam'].unique())

                for idx, match_row in matches_pool.iterrows():
                    # If Backend: data is already enriched
                    if used_backend:
                        # Direct check of 'active_strategies' list
                        active = match_row.get('active_strategies', [])
                        for strat_name in active:
                            if strat_name in strategy_results:
                                # Prepare Result Object
                                strategy_results[strat_name].append({
                                    'Date': match_row['Date'],
                                    'Time': match_row.get('Time', '00:00'),
                                    'Home': match_row['HomeTeam'],
                                    'Away': match_row['AwayTeam'],
                                    'Div': match_row.get('Div', ''),
                                    'Stats': match_row.to_dict() # Full context is the row itself
                                })
                        continue

                    # ELSE: LIVE CALCULATION
                    try:
                        # Optimization: Predictor uses memory lookup, fast enough for <100 matches.
                        ref_name = match_row.get('Referee', None)
                        
                        # DEBUG: Verify teams exist in history
                        h_norm = predictor.normalize_name(match_row['HomeTeam'])
                        a_norm = predictor.normalize_name(match_row['AwayTeam'])
                        
                        is_known = (h_norm in history_teams) and (a_norm in history_teams)
                        if not is_known:
                            debug_mismatches.append(f"{match_row['HomeTeam']} ({h_norm}) vs {match_row['AwayTeam']} ({a_norm})")
                        
                        analysis_row = predictor.predict_match_safe(match_row['HomeTeam'], match_row['AwayTeam'], referee=ref_name)
                        
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
                        # print(f"Error {e}")
                        pass

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
                                            
                                            # Custom Betting Card UI
                                            # Stats Row
                                            stats_cols = st.columns(2)
                                            with stats_cols[0]:
                                                if "Goles" in pat_name or ">2.5" in pat_name or "1.5" in pat_name:
                                                     g_proj = m['Stats'].get('HomeAvgGoalsFor',0) + m['Stats'].get('AwayAvgGoalsFor',0)
                                                     st.metric("⚽ Proy.", f"{g_proj:.2f}")
                                                else:
                                                     st.metric("🏠 Local PPG", f"{m['Stats'].get('HomePPG',0):.2f}")
                                            
                                            with stats_cols[1]:
                                                if "Goles" in pat_name:
                                                     st.metric("🛡️ Def. Avg", f"{(m['Stats'].get('HomeAvgGoalsAgainst',0)+m['Stats'].get('AwayAvgGoalsAgainst',0))/2:.2f}")
                                                else:
                                                     st.metric("✈️ Visita PPG", f"{m['Stats'].get('AwayPPG',0):.2f}")

                                            st.markdown("---")
                                            
                                            # ODDS ROW (The requested fix)
                                            odds = m['Stats']
                                            
                                            # Helper to format
                                            def fmt_odd(val):
                                                return f"{val:.2f}" if (val and val > 1) else "-"

                                            # 1X2
                                            o_cols = st.columns(3)
                                            with o_cols[0]: st.markdown(f"**1:** `{fmt_odd(odds.get('B365H'))}`")
                                            with o_cols[1]: st.markdown(f"**X:** `{fmt_odd(odds.get('B365D'))}`")
                                            with o_cols[2]: st.markdown(f"**2:** `{fmt_odd(odds.get('B365A'))}`")
                                            
                                            # Extra Markets
                                            e_cols = st.columns(2)
                                            with e_cols[0]: st.caption(f"**>2.5**: `{fmt_odd(odds.get('B365>2.5'))}`")
                                            with e_cols[1]: st.caption(f"**BTTS**: `{fmt_odd(odds.get('B365_BTTS_Yes'))}`")
                                            
                                            # Action Button
                                            if st.button("➕ Añadir", key=f"btn_add_{i}_{pat_name}_{m['Home']}"):
                                                on_strategy_click(m['Stats'], {'name': pat_name})
                                            
                    if not found_any:
                        st.warning("No se encontraron coincidencias para ninguna estrategia en este rango de fechas.")
                    
                    if debug_mismatches:
                        with st.expander(f"⚠️ Debug: {len(debug_mismatches)} Partidos con Datos Faltantes (Nombres)", expanded=False):
                            st.write("Estos equipos no se encontraron en la base de datos histórica con su nombre actual.")
                            st.dataframe(pd.DataFrame(debug_mismatches, columns=["Partido (Nombre -> Normalizado)"]), hide_index=True)
                        
                else:
                    st.warning("No hay partidos en el rango de fechas seleccionado.")
            else:
                st.error("No se pudieron cargar partidos próximos (Error de Red o Sin Datos).")
