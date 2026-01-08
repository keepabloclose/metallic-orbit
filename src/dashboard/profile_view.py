
import streamlit as st
from src.auth.user_manager import UserManager

def render_profile_view(user_manager: UserManager):
    st.header("👤 Mi Perfil")
    
    if "user" not in st.session_state:
        st.error("No usuario en sesión.")
        return

    user = st.session_state["user"]
    username = user.get("username")
    
    # Grid Layout
    col_info, col_config = st.columns([1, 1])
    
    # --- SECTION 1: Personal Data ---
    with col_info:
        st.subheader("Datos Personales")
        
        with st.form("profile_form"):
            new_name = st.text_input("Nombre", value=user.get("name", ""))
            new_surname = st.text_input("Apellidos", value=user.get("surname", ""))
            new_email = st.text_input("Correo Electrónico", value=user.get("email", ""))
            
            submitted = st.form_submit_button("Guardar Cambios")
            if submitted:
                success, msg = user_manager.update_profile(username, {
                    "name": new_name,
                    "surname": new_surname,
                    "email": new_email
                })
                if success:
                    st.success(msg)
                    st.session_state["user"] = user_manager.get_user(username) # Refresh session
                    st.rerun()
                else:
                    st.error(msg)
                    
        st.caption(f"Usuario: @{username}")
        st.caption(f"Miembro desde: {user.get('joined_at', 'Unknown')[:10]}")

    # --- SECTION 2: Configuration (Moved from Sidebar) ---
    with col_config:
        st.subheader("🛠️ Configuración de la App")
        st.info("Selecciona las competiciones y temporadas que deseas analizar.")
        
        current_prefs = user.get("preferences", {})
        
        # Leagues
        league_names = {
            'SP1': '🇪🇸 La Liga (ES)', 'SP2': '🇪🇸 La Liga 2 (ES)',
            'E0': '🇬🇧 Premier League (UK)', 'E1': '🇬🇧 Championship (UK)',
            'D1': '🇩🇪 Bundesliga (DE)', 'I1': '🇮🇹 Serie A (IT)',
            'F1': '🇫🇷 Ligue 1 (FR)', 'P1': '🇵🇹 Liga Portugal (PT)',
            'N1': '🇳🇱 Eredivisie (NL)'
        }
        all_leagues = list(league_names.keys())
        
        default_leagues = current_prefs.get("leagues", all_leagues)
        # Ensure defaults are valid keys
        default_leagues = [l for l in default_leagues if l in all_leagues]
        
        selected_leagues = st.multiselect(
            "Competiciones Activas",
            options=all_leagues,
            default=default_leagues,
            format_func=lambda x: league_names.get(x, x)
        )
        
        # Seasons
        all_seasons = ['2526', '2425', '2324']
        default_seasons = current_prefs.get("seasons", ['2526', '2425'])
        selected_seasons = st.multiselect(
            "Temporadas Históricas (para Modelo)",
            options=all_seasons,
            default=default_seasons
        )
        
        if st.button("💾 Guardar Configuración"):
            new_prefs = {
                "leagues": selected_leagues,
                "seasons": selected_seasons
            }
            success, msg = user_manager.update_profile(username, {"preferences": new_prefs})
            if success:
                st.success("Configuración actualizada.")
                st.session_state["user"] = user_manager.get_user(username)
                
                # Update global session state prefs too so they take effect immediately
                if 'user_prefs' in st.session_state:
                    st.session_state['user_prefs'] = new_prefs
                
                st.rerun()
            else:
                st.error(msg)
