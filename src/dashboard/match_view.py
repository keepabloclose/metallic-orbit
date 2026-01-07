
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.engine.trends import TrendsAnalyzer

def render_match_details(match_info, predictor):
    """
    Renders the detailed view for a specific match.
    
    Args:
        match_info (dict): Dictionary usually containing 'Date', 'HomeTeam', 'AwayTeam', etc.
        predictor (Predictor): Instance of the predictor engine to fetch stats.
    """
    home_team = match_info.get('HomeTeam')
    away_team = match_info.get('AwayTeam')
    date = match_info.get('Date')
    
    st.markdown(f"## 🏟️ Detalle del Partido")
    
    if st.button("⬅️ Volver al Panel Principal", key="back_btn_top"):
        st.session_state['view'] = 'main'
        st.session_state['selected_match'] = None
        st.rerun()
    
    # 1. Header Section
    col1, col2, col3 = st.columns([1, 0.5, 1])
    with col1:
        st.markdown(f"<h2 style='text-align: center;'>{home_team}</h2>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
        st.caption(f"<div style='text-align: center;'>{date}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<h2 style='text-align: center;'>{away_team}</h2>", unsafe_allow_html=True)

    st.divider()

    # --- DEBUG SECTION (Temporary) ---
    with st.expander("🛠️ DEBUG: Datos de Predicción (Captura esto si falla)"):
        st.write("Home Team:", home_team)
        st.write("Away Team:", away_team)
        
        try:
            h_stats = predictor.get_latest_stats(home_team)
            a_stats = predictor.get_latest_stats(away_team)
            st.write("Stats Local:", h_stats)
            st.write("Stats Visitante:", a_stats)
            
            # Manual Re-Predict trace
            if h_stats and a_stats:
                row_debug = {
                    'HomeTeam': home_team, 'AwayTeam': away_team,
                    'HomePPG': h_stats.get('PPG'), 'AwayPPG': a_stats.get('PPG'),
                    'HomeAttackStrength': h_stats.get('AttackStrength'),
                    'AwayAttackStrength': a_stats.get('AttackStrength'),
                    'HomeRestDays': h_stats.get('RestDays'),
                }
                
                # Dynamic Strength Calc Check
                eps = 0.01
                h_att = h_stats.get('AvgShotsTargetFor', 0) / (a_stats.get('AvgShotsTargetAgainst', 0) + eps)
                st.write(f"Calculated HomeAttackStrength: {h_att}")
                
                st.write("Row Debug Partial:", row_debug)
                
                if hasattr(predictor.ml_engine, 'predict_row'):
                     full_row = predictor.predict_match_safe(home_team, away_team)
                     st.write("Full Prediction Output:", full_row)
                     st.write("Model Features:", getattr(predictor.ml_engine, 'feature_cols', 'Unknown'))
                     st.write("Model Trained?", getattr(predictor.ml_engine, 'is_trained', 'Unknown'))
        except Exception as e:
            st.error(f"Debug Crash: {e}")

    # --- RE-PREDICT FOR CONSISTENCY ---
    # To ensure the Details View matches the latest model state and isn't using stale data directly from the list view,
    # we regenerate the prediction here.
    
    # Try to clean referee
    ref_name = match_info.get('Referee', None)
    
    # Predict
    fresh_row = predictor.predict_match_safe(home_team, away_team, match_date=date, referee=ref_name)
    
    if fresh_row:
        # Merge fresh predictions into match_info (keeping meta data like Time/Div)
        match_info.update(fresh_row)
        
        # Update vars for display
        p_home = match_info.get('ML_HomeWin', 0)
        p_draw = match_info.get('ML_Draw', 0)
        p_away = match_info.get('ML_AwayWin', 0)
    else:
        st.warning("No se pudo regenerar la predicción (Datos insuficientes). Mostrando datos cacheados si existen.")


    # --- AI PREDICTIONS ---
    with st.container(border=True):
        st.subheader("🧠 Predicciones de Inteligencia Artificial")
        
        if p_home + p_draw + p_away > 0:
            c_ai1, c_ai2 = st.columns([2, 1])
            
            with c_ai1:
                # Win Probabilities Chart
                probs_df = pd.DataFrame({
                    'Resultado': [home_team, 'Empate', away_team],
                    'Probabilidad': [p_home, p_draw, p_away],
                    'Color': ['#1f77b4', '#7f7f7f', '#ff7f0e'] # Blue, Grey, Orange
                })
                
                fig = px.bar(
                    probs_df, x='Probabilidad', y='Resultado', orientation='h', text='Probabilidad',
                    color='Resultado', color_discrete_sequence=['#1f77b4', '#7f7f7f', '#ff7f0e']
                )
                fig.update_layout(showlegend=False, height=200, margin=dict(l=0, r=0, t=20, b=0))
                fig.update_traces(texttemplate='%{text}%', textposition='inside')
                st.plotly_chart(fig, use_container_width=True)
                
            with c_ai2:
                st.markdown("### 🎯 Marcador Exacto")
                pred_h_goals = int(match_info.get('REG_HomeGoals', 0))
                pred_a_goals = int(match_info.get('REG_AwayGoals', 0))
                
                st.metric(label="Predicción", value=f"{pred_h_goals} - {pred_a_goals}", help="Goles Esperados (Modelo de Regresión)")
                
                # --- HELPER: ENRICH ODDS ---
                def enrich_text_with_odd(text, match_data):
                    """Looks for key markets in text and appends odd if found."""
                    lower_txt = text.lower()
                    odd_found = None
                    
                    # Over/Under X.X Patterns (+1.5, >1.5, Over 1.5)
                    import re
                    match_over = re.search(r'(\+|>|Over|Más de|Mas de) ?([0-9]\.5)', text, re.IGNORECASE)
                    if match_over:
                        line = match_over.group(2) # "1.5"
                        key = f"B365_Over{line}"
                        val = match_data.get(key)
                        if val and str(val) != 'nan':
                            odd_found = val
                    
                    # BTTS
                    if 'ambos' in lower_txt or 'btts' in lower_txt:
                        val = match_data.get('B365_BTTS_Yes')
                        if val and str(val) != 'nan':
                                odd_found = val
                                
                    if odd_found:
                        return f"{text} (@ {odd_found})"
                    return text

                # --- AI SUGGESTIONS WITH ODDS ---
                
                # 1. Over 2.5 Logic
                if match_info.get('ML_Over25'):
                    base_text = "🔥 Alta Probabilidad de +2.5 Goles"
                    final_text = enrich_text_with_odd(base_text, match_info)
                    st.info(final_text)

                # 2. BTTS Logic
                if match_info.get('ML_BTTS_Yes') or ((match_info.get('ML_Over25', 0) > 75) and (match_info.get('B365_BTTS_Yes'))):
                        base_text = "⚽ Ambos Marcan (Yes)"
                        final_text = enrich_text_with_odd(base_text, match_info)
                        st.success(final_text)

        else:
            st.info("Predicciones de IA no disponibles para este partido (Faltan datos históricos pareados).")

    # 2. Comparison Stats (Promedios)
    with st.container(border=True):
        st.subheader("📊 Comparativa de Estadísticas (Promedios)")
        
        # Filter selection
        filter_option = st.radio("Filtrar últimos partidos:", [5, 10, 20, "Temporada"], index=0, horizontal=True)
        window = 5 if filter_option == 5 else 10 if filter_option == 10 else 20 if filter_option == 20 else 50 # 50 as 'Season' approx
        
        # Fetch stats (using predictor's history)
        if predictor.history is None or predictor.history.empty:
            st.error("No hay datos históricos disponibles para calcular estadísticas.")
            # return # Don't return, just skip this block properly
        else:
            # Helper to calculate averages
            def get_avg_stats(team, n_games):
                matches = predictor.history[
                    (predictor.history['HomeTeam'] == team) | 
                    (predictor.history['AwayTeam'] == team)
                ].sort_values('Date', ascending=False)
                
                # If we have a current match date, filter to only show matches BEFORE this one
                if 'Date' in match_info:
                        matches = matches[matches['Date'] < match_info.get('Date')]
                
                matches = matches.head(n_games)
                
                if matches.empty:
                    return None
                    
                stats = {'Goles': 0, 'Tiros': 0, 'Córners': 0, 'Tarjetas': 0}
                count = len(matches)
                
                for _, m in matches.iterrows():
                    if m['HomeTeam'] == team:
                        stats['Goles'] += m['FTHG']
                        stats['Tiros'] += m.get('HST', 0) + m.get('HS', 0) 
                        stats['Córners'] += m.get('HC', 0)
                        stats['Tarjetas'] += m.get('HY', 0) + m.get('HR', 0)
                    else:
                        stats['Goles'] += m['FTAG']
                        stats['Tiros'] += m.get('AST', 0) + m.get('AS', 0)
                        stats['Córners'] += m.get('AC', 0)
                        stats['Tarjetas'] += m.get('AY', 0) + m.get('AR', 0)
                
                return {k: round(v / count, 2) for k, v in stats.items()}

            home_stats = get_avg_stats(home_team, window)
            away_stats = get_avg_stats(away_team, window)

            if home_stats and away_stats:
                # Create comparison table
                comp_data = {
                    'Métrica': ['Goles (Prom)', 'Tiros (Prom)', 'Córners (Prom)', 'Tarjetas (Prom)'],
                    home_team: [home_stats['Goles'], home_stats['Tiros'], home_stats['Córners'], home_stats['Tarjetas']],
                    away_team: [away_stats['Goles'], away_stats['Tiros'], away_stats['Córners'], away_stats['Tarjetas']]
                }
                df_comp = pd.DataFrame(comp_data)
                st.dataframe(df_comp, use_container_width=True, hide_index=True)
                
                # Simple Bar Chart
                fig = go.Figure(data=[
                    go.Bar(name=home_team, x=df_comp['Métrica'], y=df_comp[home_team]),
                    go.Bar(name=away_team, x=df_comp['Métrica'], y=df_comp[away_team])
                ])
                fig.update_layout(barmode='group', title=f"Promedios - Últimos {window} Partidos")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No hay suficientes datos para calcular estadísticas de los últimos {window} partidos.")

    # 3. Head to Head (H2H)
    with st.container(border=True):
        st.subheader("⚔️ Historial H2H")
        
        from src.engine.h2h import H2HManager
        # Predictor history (if available) contains the data
        h2h_engine = H2HManager(predictor.history if not predictor.history.empty else pd.DataFrame())
        
        h2h_matches = h2h_engine.get_h2h_matches(home_team, away_team)
        
        if not h2h_matches.empty:
            summary = h2h_engine.get_h2h_summary(home_team, away_team)
            
            col_h1, col_h2, col_h3 = st.columns(3)
            col_h1.metric(f"Victorias {home_team}", summary['HomeWins'])
            col_h2.metric("Empates", summary['Draws'])
            col_h3.metric(f"Victorias {away_team}", summary['AwayWins'])
            
            # Formatted Display
            df_display = h2h_engine.format_for_display(h2h_matches)
            
            # Highlight winner
            st.dataframe(
                df_display.style.apply(lambda x: ['background-color: #d4edda' if x['Res'] == 'H' and x['Local'] == home_team else ('background-color: #f8d7da' if x['Res'] == 'A' and x['Local'] == home_team else '') for i in x], axis=1),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"No hay enfrentamientos previos registrados entre {home_team} y {away_team}.")

    # 4. League Standings
    with st.container(border=True):
        st.subheader("🏆 Clasificación de la Liga")
        league_code = match_info.get('Div')
        
        if league_code:
            league_matches = predictor.history[predictor.history['Div'] == league_code]
            
            if not league_matches.empty:
                # Filter for Current Season Logic
                if 'Season' in league_matches.columns:
                    max_season = league_matches['Season'].max()
                    st.caption(f"Mostrando clasificación: Temporada {max_season}")
                    league_matches = league_matches[league_matches['Season'] == max_season]
                else:
                        # Fallback: Last 365 Days
                        st.warning("Columna 'Season' no encontrada. Filtrando por últimos 12 meses.")
                        if 'Date' in league_matches.columns:
                            cutoff = pd.Timestamp.now() - pd.Timedelta(days=365)
                            league_matches['DateObj'] = pd.to_datetime(league_matches['Date'])
                            league_matches = league_matches[league_matches['DateObj'] > cutoff]
            
                points = {}
                goals_diff = {}
                played = {}
                
                for _, m in league_matches.iterrows():
                    h, a, res, hg, ag = m['HomeTeam'], m['AwayTeam'], m['FTR'], m['FTHG'], m['FTAG']
                    
                    for t in [h, a]:
                        if t not in points: points[t] = 0
                        if t not in goals_diff: goals_diff[t] = 0
                        if t not in played: played[t] = 0
                        played[t] += 1
                    
                    goals_diff[h] += (hg - ag)
                    goals_diff[a] += (ag - hg)
                    
                    if res == 'H':
                        points[h] += 3
                    elif res == 'A':
                        points[a] += 3
                    else:
                        points[h] += 1
                        points[a] += 1
                
                # Create DF
                standings_data = []
                for team in points:
                    standings_data.append({
                        'Equipo': team,
                        'PJ': played[team],
                        'Pts': points[team],
                        'DG': goals_diff[team]
                    })
                
                df_standings = pd.DataFrame(standings_data).sort_values(['Pts', 'DG'], ascending=False).reset_index(drop=True)
                df_standings.index += 1 # Rank 1-based
                
                # Highlight current teams
                def highlight_teams(s):
                    is_selected = s['Equipo'] in [home_team, away_team]
                    return ['background-color: #ffffb3; color: black' if is_selected else '' for _ in s]

                st.dataframe(df_standings.style.apply(highlight_teams, axis=1), use_container_width=True)
            else:
                st.warning(f"No hay datos suficientes de la liga '{league_code}' (Matches Found: {len(league_matches)}) para calcular la clasificación.")
        else:
            st.info("Información de liga (Div) no disponible en los metadatos del partido.")

    # 5. Trends (Dynamic)
    with st.container(border=True):
        st.subheader("🔥 Tendencias Recientes")
        trends_engine = TrendsAnalyzer(predictor.history)
        
        # Calculate Trends
        trends = trends_engine.get_match_trends(home_team, away_team)
        
        t_col1, t_col2 = st.columns(2)
        
        import re
        
        def render_trend_item(t):
            # Parse "L{x}/{y}"
            match = re.search(r"L(\d+)/(\d+)", t)
            if match:
                num, den = int(match.group(1)), int(match.group(2))
                ratio = num / den
                # User Rule: Show only "True" (Strong) trends.
                # We treat >= 0.8 as Strong (e.g. 4/5, 5/5, 8/10).
                # 7/10 (0.7) would be hidden.
                if ratio >= 0.8:
                    final_text = enrich_text_with_odd(t, match_info)
                    st.markdown(f"• :green[{final_text}]")
                    return True
            return False

        with t_col1:
            st.markdown(f"**{home_team}**")
            has_trends = False
            if trends['Home']:
                for t in trends['Home']:
                    if render_trend_item(t):
                        has_trends = True
            
            if not has_trends:
                st.caption("No se detectaron tendencias (Global > 80%).")
                
        with t_col2:
            st.markdown(f"**{away_team}**")
            has_trends = False
            if trends['Away']:
                for t in trends['Away']:
                    if render_trend_item(t):
                        has_trends = True

            if not has_trends:
                st.caption("No se detectaron tendencias (Global > 80%).")
    
    if st.button("⬅️ Volver a Explorar"):
        st.session_state['view'] = 'main'
        st.session_state['selected_match'] = None
        st.rerun()
