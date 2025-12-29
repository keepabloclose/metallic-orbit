
import streamlit as st
import pandas as pd
from src.utils.logo_manager import LogoManager

# Create instance (singleton-like pattern essentially)
logo_manager = LogoManager()

def render_premium_match_row(match, predictor, patterns, forms_analyzer, navigate_callback, home_trends=None, away_trends=None):
    """
    Renders a single match row in a 'Premium' dense layout.
    Mimics user's requested style: Date | Teams | Form | Stats | Trends | Odds
    """
    
    # 1. EXTRACT DATA
    home = match['HomeTeam']
    away = match['AwayTeam']
    time = match.get('Time', '00:00')
    div = match.get('Div', '')
    
    # Get Logos
    home_logo = logo_manager.get_team_logo(home, div)
    away_logo = logo_manager.get_team_logo(away, div)
    default_logo = "https://cdn-icons-png.flaticon.com/512/53/53283.png"
    
    # Form
    form_h = forms_analyzer.get_recent_form(home) # e.g. "WWDLO"
    form_a = forms_analyzer.get_recent_form(away)
    
    # Stats
    g_h = match.get('HomeAvgGoalsFor', 0.0)
    g_a = match.get('AwayAvgGoalsFor', 0.0)
    s_h = match.get('HomeAvgShotsTargetFor', 0.0)
    s_a = match.get('AwayAvgShotsTargetFor', 0.0)
    
    # Odds
    odd_1 = match.get('B365H', '-')
    odd_x = match.get('B365D', '-')
    odd_2 = match.get('B365A', '-')
    
    # 2. MATCH LOGIC / HELPERS
    def get_form_html(form_str):
        html = ""
        for char in form_str[-5:]:
            color = "#ccc"
            if char == 'W': color = "#28a745"
            elif char == 'L': color = "#dc3545"
            html += f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:{color};margin-right:2px;"></span>'
        return html

    def get_trend_pill(text, sentiment='good'):
        # Colors: Green (Good/High), Orange (Low/Bad)
        bg_col = "#dcfce7" if sentiment == 'good' else "#ffedd5"
        txt_col = "#166534" if sentiment == 'good' else "#9a3412"
        border = "#86efac" if sentiment == 'good' else "#fdba74"
        
        # Override for negative semantics
        if "Under" in text or "recibe" in text.lower() or "-2.5" in text or "-3.5" in text:
             bg_col = "#ffedd5"
             txt_col = "#9a3412"
             border = "#fdba74"

        return f'<span style="background-color:{bg_col};color:{txt_col};border:1px solid {border};padding:1px 6px;border-radius:4px;font-size:0.75em;margin-right:4px;margin-bottom:2px;display:inline-block;">{text}</span>'

    # 3. TRENDS PRE-CALCULATION
    trends_html = ""
    count = 0
    if home_trends:
        for t in home_trends[:2]:
            trends_html += get_trend_pill(t['text'], 'good')
            count += 1 
    if away_trends:
        for t in away_trends[:2]:
            trends_html += get_trend_pill(t['text'], 'good')
            count += 1
            
    # ML Hint
    if match.get('ML_Over25', 0) > 65 and count < 4:
         trends_html += get_trend_pill(f"IA: +2.5 ({match['ML_Over25']}%)", 'good')

    # --- PRE-CALCULATION OF PREDICTION ---
    ref_name = match.get('Referee', None)
    pred_row = predictor.predict_match(match['HomeTeam'], match['AwayTeam'], referee=ref_name)
    
    # Check Risks / Traps
    risk_html = ""
    if pred_row:
        # 1. Z-Score (Regression Risk)
        z_h = pred_row.get('HomeZScore_Goals', 0)
        if z_h > 2.5:
             risk_html += get_trend_pill(f"⚠️ Racha Local (Z={z_h:.1f})", 'bad')
        elif z_h < -1.5:
             risk_html += get_trend_pill(f"📉 Crisis Local (Z={z_h:.1f})", 'bad')
             
        # 2. Trap Filters
        if pred_row.get('Trap_Fatigue', 0) > 0:
             risk_html += get_trend_pill("⚠️ Fatiga", 'bad')
        if pred_row.get('Trap_FearError', 0) > 0:
             risk_html += get_trend_pill("🛡️ Miedo Error", 'bad')
        if pred_row.get('Trap_StyleClash', 0) > 0:
             risk_html += get_trend_pill("🛡️ Estilos Def.", 'bad')
             
        # 3. Dominance (Good High)
        if pred_row.get('HomeDominance', 0) > 30: # 30 is roughly high
             risk_html += get_trend_pill("🔥 Dominio Local", 'good')

    # Append Risk pills to Trends
    trends_html += risk_html

    # 4. RENDER LAYOUT
    with st.container(border=True):
        # Columns: Time (1) | Teams (2.5) | Form (1.5) | Stats (1.5) | Trends (3.5) | Odds (2)
        c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 1.5, 1.5, 3.5, 2])
        
        with c1:
            st.caption(f"{div}") 
            st.markdown(f"**{time}**")
            
        with c2:
            # Teams with Logos
            hl = home_logo if home_logo else default_logo
            al = away_logo if away_logo else default_logo
            
            st.markdown(f"""
            <div style="display:flex;align-items:center;margin-bottom:4px;">
                <img src="{hl}" onerror="this.src='{default_logo}'" style="width:24px;height:24px;margin-right:8px;object-fit:contain;">
                <span style="font-weight:600;font-size:1.05em;">{home}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <img src="{al}" onerror="this.src='{default_logo}'" style="width:24px;height:24px;margin-right:8px;object-fit:contain;">
                <span style="font-weight:600;font-size:1.05em;">{away}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(get_form_html(form_h), unsafe_allow_html=True)
            st.markdown(get_form_html(form_a), unsafe_allow_html=True)
            
        with c4:
            st.caption("Goles / Pred")
            st.markdown(f"{g_h:.1f} / {g_a:.1f}")
            
            # Display Prediction Result (Pre-calculated)
            if pred_row:
                p_h = pred_row.get('PredictedHomeGoals', 0)
                p_a = pred_row.get('PredictedAwayGoals', 0)
                
                # Format: 🎯 2.1 - 1.0 (or rounded 2-1)
                st.markdown(f"**🎯 {p_h:.0f} - {p_a:.0f}**", help=f"Exacto: {p_h:.2f} - {p_a:.2f}")
            else:
                 st.markdown("-")
            
        with c5:
            st.caption("Tendencias / Riesgos")
            
            # 4.0 EVOLUTION VISUALS
            # We use pred_row calculated in previous column (Scope issue? No, we need to ensure it's calculated before or move calculation up)
            # Actually, `pred_row` is local to c4 scope in current code. 
            # Better to move prediction UP before columns.
            pass # See Instruction below for full replace logic to fix scope
            
            # --- MOVED PREDICTION UP ---
            st.markdown(trends_html if trends_html else "<span style='color:#ccc;font-size:0.8em'>-</span>", unsafe_allow_html=True)

        with c6:
            # Odds Grid
            st.markdown(f"""
            <div style="display:flex;gap:4px;font-size:0.8em;font-weight:bold;">
                <div style="background:#f0f0f0;padding:4px;border-radius:4px;color:#333;">1 <br>{odd_1}</div>
                <div style="background:#f0f0f0;padding:4px;border-radius:4px;color:#333;">X <br>{odd_x}</div>
                <div style="background:#f0f0f0;padding:4px;border-radius:4px;color:#333;">2 <br>{odd_2}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            b_key = f"btn_prem_{home}_{away}"
            if st.button("Ver Predicción ➡️", key=b_key):
                 navigate_callback(match)
