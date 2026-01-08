
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

def render_portfolio_view(user_manager, username):
    """
    Renders the 'My Predictions' page.
    """
    st.title("Mi Portafolio de Apuestas")
    
    pm = user_manager.portfolio_manager
    stats = pm.get_portfolio_stats(username)
    bets = pm.get_user_bets(username)
    
    # 1. TOP STATS ROW
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Beneficio Neto", f"{stats['total_profit']:.2f}€", delta=stats['total_profit'])
    k2.metric("ROI", f"{stats['roi']}%")
    k3.metric("Win Rate", f"{stats['win_rate']}%")
    k4.metric("Apostado", f"{stats['total_staked']:.2f}€")
    k5.metric("Retorno", f"{stats['total_returned']:.2f}€")
    k6.metric("Apuestas", f"{stats['settled_bets']} / {stats['total_bets']}")
    
    st.divider()

    # 2. LEAGUE BREAKDOWN
    with st.expander("📊 Estadísticas por Liga", expanded=False):
        if not bets:
             st.info("No hay datos suficientes.")
        else:
             df_all = pd.DataFrame(bets)
             if 'league' not in df_all.columns:
                 df_all['league'] = 'Unknown'
             
             # Fill NaN
             df_all['league'] = df_all['league'].fillna('Unknown')
             
             # Group Logic
             league_stats = []
             grouped = df_all.groupby('league')
             
             for league, group in grouped:
                 n_bets = len(group)
                 n_real = len(group[group['stake'] > 0])
                 n_preds = n_bets - n_real
                 
                 # Effectiveness (Settled only)
                 settled_g = group[group['status'].isin(['Won', 'Lost', 'Void'])]
                 n_settled = len(settled_g)
                 
                 win_rate = 0.0
                 roi = 0.0
                 
                 if n_settled > 0:
                     n_won = len(settled_g[settled_g['status'] == 'Won'])
                     win_rate = (n_won / n_settled) * 100
                     
                     # ROI (Real only)
                     real_settled = settled_g[settled_g['stake'] > 0]
                     if not real_settled.empty:
                         staked = real_settled['stake'].sum()
                         profit = real_settled['result_amount'].sum() if 'result_amount' in real_settled.columns else 0
                         # Fallback calc if result_amount missing (old bets)
                         if 'result_amount' not in real_settled.columns:
                             # simplistic fallback
                             profit = 0 
                             for _, r in real_settled.iterrows():
                                 if r['status'] == 'Won': profit += (r['stake']*r['odds'] - r['stake'])
                                 elif r['status'] == 'Lost': profit -= r['stake']
                         
                         roi = (profit / staked) * 100 if staked > 0 else 0
                 
                 league_stats.append({
                     "Liga": league,
                     "Apuestas (Real)": n_real,
                     "Predicciones": n_preds,
                     "Win Rate %": round(win_rate, 1),
                     "ROI %": round(roi, 1),
                     "Volumen": n_bets
                 })
             
             if league_stats:
                 st.dataframe(
                     pd.DataFrame(league_stats).set_index("Liga"),
                     use_container_width=True
                 )
    
    st.divider()
    
    # 2. TABS: Open vs History
    tab_open, tab_history = st.tabs(["🔓 Pendientes", "📜 Historial"])
    
    df = pd.DataFrame(bets)
    if df.empty:
        st.info("No tienes predicciones guardadas aún.")
        return

    # Ensure date sorting
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)

    with tab_open:
        open_bets = df[df['status'] == 'Pending']
        if not open_bets.empty:
            for idx, row in open_bets.iterrows():
                # Premium Card Style
                with st.container(border=True):
                    c_main, c_financial, c_actions = st.columns([3, 2, 1.5])
                    
                    with c_main:
                        # Header: Team vs Team
                        st.markdown(f"**⚽ {row['home_team']}** vs **{row['away_team']}**")
                        # Sub: Selection & Odds
                        st.caption(f"🎯 {row['selection']} @ **{row['odds']}** ({row['strategy']})")
                        # Date
                        st.caption(f"📅 {row['match_date']}")

                    with c_financial:
                        # Stake & Return
                        if row['stake'] > 0:
                            st.write(f"💵 **{row['stake']}€** ➝ **{row['potential_return']:.2f}€**")
                            st.caption("Invested / Potential")
                        else:
                            st.markdown("👁️ **Tracking**")
                            st.caption("Virtual Bet")

                    with c_actions:
                        # Check Eligibility
                        try:
                            match_dt = pd.to_datetime(str(row['match_date']))
                            is_future = match_dt > datetime.now()
                        except:
                            is_future = True

                        if is_future:
                            # Use icon buttons side-by-side
                            ca1, ca2 = st.columns(2)
                            with ca1:
                                if st.button("✏️", key=f"e_{row['id']}", help="Editar"):
                                    dialog_edit_bet(user_manager, username, row)
                            with ca2:
                                if st.button("🗑️", key=f"d_{row['id']}", help="Borrar"):
                                    pm.delete_bet(username, row['id'])
                                    st.rerun()
                        else:
                            # Settle Controls for Past Games
                            st.caption("Resolver")
                            cb1, cb2 = st.columns(2)
                            with cb1: 
                                if st.button("✅", key=f"w_{row['id']}", help="Ganada"):
                                    pm.update_bet_status(username, row['id'], 'Won')
                                    st.rerun()
                            with cb2: 
                                if st.button("❌", key=f"l_{row['id']}", help="Perdida"):
                                    pm.update_bet_status(username, row['id'], 'Lost')
                                    st.rerun()
        else:
             st.info("✨ Tu portafolio está vacío. ¡Añade predicciones desde 'Próximos Partidos'!")
            
    with tab_history:
        settled = df[df['status'].isin(['Won', 'Lost', 'Void'])]
        if not settled.empty:
            # Add Type Column for Display
            settled['type'] = settled['stake'].apply(lambda x: "💰 Apuesta" if x > 0 else "👁️ Predicción")
            st.dataframe(
                settled[['date', 'type', 'home_team', 'away_team', 'selection', 'odds', 'stake', 'status', 'result_amount']],
                use_container_width=True,
                hide_index=True
            )
        else:
             st.write("No hay historial.")


@st.dialog("Editar Apuesta")
def dialog_edit_bet(user_manager, username, bet_row):
    """
    Dialog to edit an existing bet (Stake only).
    """
    st.markdown(f"**{bet_row['home_team']} vs {bet_row['away_team']}**")
    st.caption(f"Selección: {bet_row['selection']}")
    
    current_stake = float(bet_row['stake'])
    new_stake = st.number_input("Nuevo Stake (€)", min_value=0.0, value=current_stake, step=5.0)
    
    if st.button("Actualizar", type="primary", use_container_width=True):
        updated = user_manager.portfolio_manager.update_bet(username, bet_row['id'], new_stake)
        if updated:
            st.success("Actualizado!")
            st.rerun()
        else:
            st.error("Error al actualizar. Quizás el evento ya empezó.")

@st.dialog("Guardar Predicción")
def dialog_add_prediction(user_manager, username, match_data, strategy_data):
    """
    Dialog implementation to add a bet.
    """
    st.caption(f"Evento: {match_data.get('HomeTeam')} vs {match_data.get('AwayTeam')}")
    st.markdown(f"### {strategy_data.get('suggestion')}")
    
    # Tracking Mode Checkbox
    is_tracking = st.checkbox("Solo Seguimiento (Sin Dinero)", value=False)
    
    c1, c2 = st.columns(2)
    with c1:
        if is_tracking:
            st.info("Modo Seguimiento Activo")
            stake = 0.0
        else:
            stake = st.number_input("Cantidad (€)", min_value=0.1, value=10.0, step=5.0)
            
    with c2:
        # Try to parse odds from string if needed, or use passed value
        raw_odd = strategy_data.get('odd')
        if not raw_odd or raw_odd == 'N/A':
            odds = st.number_input("Cuota", min_value=1.01, value=1.50)
        else:
            try:
                odds = float(raw_odd)
                st.metric("Cuota", odds)
            except:
                odds = st.number_input("Cuota", min_value=1.01, value=1.50)
                
    if st.button("Guardar", type="primary", use_container_width=True):
        # Call Backend
        pm = user_manager.portfolio_manager
        pm.add_bet(
            username=username,
            match_data=match_data,
            selection=strategy_data.get('suggestion'),
            stake=stake,
            odds=odds,
            strategy=strategy_data.get('pattern', 'Manual'),
            status="Pending"
        )
        st.success("Guardado!")
        st.session_state['trigger_confetti'] = True # Fun feedback
        st.rerun()
