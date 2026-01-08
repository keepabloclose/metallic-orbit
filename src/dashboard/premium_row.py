
import streamlit as st
import pandas as pd
from src.utils.logo_manager import LogoManager

# Create instance (singleton-like pattern essentially)
logo_manager = LogoManager()

def render_premium_match_row(match, predictor, patterns, forms_analyzer, navigate_callback, home_trends=None, away_trends=None, unique_key=None, extra_strategies=None, strategy_callback=None):
    """
    Renders a single match row in a 'Premium' dense layout.
    Mimics user's requested style: Date | Teams | Form | Stats | Trends | Odds
    """
    
    # 1. EXTRACT DATA
    home = match['HomeTeam']
    away = match['AwayTeam']
    time = match.get('Time', '00:00')
    div = match.get('Div', '')
    
    # Normalize names for Logo Lookup
    home_norm = predictor.normalize_name(home)
    away_norm = predictor.normalize_name(away)
    
    # Get Logos
    home_logo = logo_manager.get_team_logo(home_norm, div)
    away_logo = logo_manager.get_team_logo(away_norm, div)
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
    
    # Calculate Prediction Row (Found Missing Definition)
    pred_row = predictor.predict_match_safe(
        match['HomeTeam'], 
        match['AwayTeam'], 
        match_date=match.get('Date'),
        known_odds={k: v for k, v in match.items() if str(k).startswith('B365')}
    )
    
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
        # Colors: Green (Good/High), Orange (Low/Bad), Purple (Strategy)
        if sentiment == 'strategy':
            bg_col = "#faf5ff" # Purple-50
            txt_col = "#6b21a8" # Purple-800
            border = "#d8b4fe" # Purple-300
        else:
            bg_col = "#dcfce7" if sentiment == 'good' else "#ffedd5"
            txt_col = "#166534" if sentiment == 'good' else "#9a3412"
            border = "#86efac" if sentiment == 'good' else "#fdba74"
        
        # Override for negative semantics (only if not strategy)
        if sentiment != 'strategy':
            if "Under" in text or "recibe" in text.lower() or "-2.5" in text or "-3.5" in text:
                bg_col = "#ffedd5"
                txt_col = "#9a3412"
                border = "#fdba74"

        return f'<span style="background-color:{bg_col};color:{txt_col};border:1px solid {border};padding:1px 6px;border-radius:4px;font-size:0.75em;margin-right:4px;margin-bottom:2px;display:inline-block;">{text}</span>'

    # 3. TRENDS PRE-CALCULATION
    
    def enrich_text_with_odd(text, match_data):
        """Looks for key markets in text and appends odd if found."""
        # Clean text for parsing
        lower_txt = text.lower()
        odd_found = None
        
        # Over/Under X.X Patterns
        import re
        # Look for "+1.5", ">1.5", "over 1.5", "mas de 1.5"
        # Regex to capture the number: (1\.5|2\.5|3\.5|0\.5)
        match_over = re.search(r'(\+|>|Over|Más de|Mas de) ?([0-9]\.5)', text, re.IGNORECASE)
        if match_over:
            line = match_over.group(2) # "1.5"
            # Try both formats
            val = match_data.get(f"B365_Over{line}") or match_data.get(f"B365>{line}")
            if val and str(val).lower() != 'nan':
                odd_found = val
        
        # BTTS / Ambos Marcan
        if 'ambos' in lower_txt or 'btts' in lower_txt:
            val = match_data.get('B365_BTTS_Yes')
            if val and str(val) != 'nan':
                 odd_found = val
                 
        if odd_found:
            return f"{text} @ {odd_found}"
        return text

    trends_html = ""
    count = 0
    
    # 0. STRATEGIES (High Value) - Highlighted
    # 0. STRATEGIES (High Value) - Highlighted
    # Only render as HTML pills if NO callback is provided (otherwise rendered as buttons)
    if extra_strategies and not strategy_callback:
        for strat in extra_strategies:
            s_name = strat.get('suggestion', 'Estrategia')
            s_prob = strat.get('prob', 0)
            s_odd = strat.get('odd')
            
            # Format: Name (84%) [Odd]
            txt = f"★ {s_name} ({s_prob}%)"
            if s_odd and s_odd != 'N/A':
                txt += f" 💰{s_odd}"
                
            trends_html += get_trend_pill(txt, sentiment='strategy')
            count += 1 # Count strategies towards the total pill limit
    
    # 1. HOME TRENDS
    if home_trends:
        for t in home_trends[:2]:
            if count >= 4: break # Limit total pills
            display_text = enrich_text_with_odd(t['text'], match)
            trends_html += get_trend_pill(display_text, 'good')
            count += 1 
            
    # Process Away Trends
    if away_trends:
        for t in away_trends[:2]:
            display_text = enrich_text_with_odd(t['text'], match)
            trends_html += get_trend_pill(display_text, 'good')
            count += 1
            
    # ML Hint (Specific Logic kept but used enricher just in case?)
    # Actually, previous step hardcoded it. Let's make it consistent.
    if match.get('ML_Over25', 0) > 65 and count < 4:
         base_text = f"IA: +2.5 ({match['ML_Over25']}%)"
         display_text = enrich_text_with_odd(base_text, match)
         trends_html += get_trend_pill(display_text, 'good')

    # Append Risk pills to Trends (Risks handled inside get_trend_pill logic above)
    # trends_html += risk_html # REMOVED: Caused NameError

    # 4. RENDER LAYOUT
    # 4. RENDER LAYOUT
    with st.container(): # Removed border=True because the Update CSS already adds it to wrappers? OR keep it for card effect. Keep it.
        # Actually better to use CSS class for Density.
        
        # Columns: Time/Div (0.8) | Logos+Teams (3) | Form (1) | Stats (1.2) | Trends (4) | Odds+Action (2)
        c1, c2, c3, c4, c5, c6 = st.columns([0.8, 3, 1, 1.2, 4, 1.8], gap="small")
        
        with c1:
            # Merged for compactness
            st.markdown(f"<div style='line-height:1.2'><small style='color:#888'>{div}</small><br><b>{time}</b></div>", unsafe_allow_html=True)
            
        with c2:
            # Teams with Logos
            hl = home_logo if home_logo else default_logo
            al = away_logo if away_logo else default_logo
            
            st.markdown(f"""
            <div style="display:flex;align-items:center;margin-bottom:2px;">
                <img src="{hl}" onerror="this.src='{default_logo}'" style="width:20px;height:20px;margin-right:6px;object-fit:contain;">
                <span style="font-weight:600;font-size:1em;">{home}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <img src="{al}" onerror="this.src='{default_logo}'" style="width:20px;height:20px;margin-right:6px;object-fit:contain;">
                <span style="font-weight:600;font-size:1em;">{away}</span>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"<div style='margin-bottom:2px'>{get_form_html(form_h)}</div>{get_form_html(form_a)}", unsafe_allow_html=True)
            
        with c4:
             # Compact Stats
             # Goles / Pred (Small)
             pred_txt = "-"
             if pred_row:
                 p_h = pred_row.get('REG_HomeGoals', 0)
                 p_a = pred_row.get('REG_AwayGoals', 0)
                 pred_txt = f"{p_h:.0f}-{p_a:.0f}"
             
             st.markdown(f"""
             <div style='line-height:1.3;font-size:0.85em'>
             <span style='color:#666'>Goles:</span> <b>{g_h:.1f} / {g_a:.1f}</b><br>
             <span style='color:#666'>Pred:</span> <b style='color:#2563EB'>{pred_txt}</b>
             </div>
             """, unsafe_allow_html=True)
             
        with c5:
            # Trends (Compact)
            if not trends_html:
                st.markdown("<span style='color:#ccc;font-size:0.8em'>-</span>", unsafe_allow_html=True)
            # Interactive Strategies (Buttons)
            if extra_strategies and strategy_callback:
                for i, s in enumerate(extra_strategies):
                     b_key = f"strat_{unique_key}_{i}"
                     s_name = s.get('suggestion', 'Strat')
                     s_prob = s.get('prob', 0)
                     s_odd = s.get('odd')
                     
                     lbl = f"★ {s_name} ({s_prob}%)"
                     if s_odd and s_odd != 'N/A':
                          lbl += f" 💰{s_odd}"
                          
                     # Use small button or distinct style
                     if st.button(lbl, key=b_key, type="secondary", use_container_width=True):
                          strategy_callback(match, s)
                          
            st.markdown(trends_html, unsafe_allow_html=True)

        with c6:
            # Odds Grid (Super Compact)
            col_odds = """
            <div style="display:flex;gap:2px;font-size:0.75em;text-align:center;margin-bottom:4px;">
                <div style="background:#f1f5f9;padding:2px;border-radius:3px;flex:1;">1 <b style='color:#1e293b'>{o1}</b></div>
                <div style="background:#f1f5f9;padding:2px;border-radius:3px;flex:1;">X <b style='color:#1e293b'>{ox}</b></div>
                <div style="background:#f1f5f9;padding:2px;border-radius:3px;flex:1;">2 <b style='color:#1e293b'>{o2}</b></div>
            </div>
            """.replace("{o1}", str(odd_1)).replace("{ox}", str(odd_x)).replace("{o2}", str(odd_2))
            
            st.markdown(col_odds, unsafe_allow_html=True)

            b_key = f"btn_prem_{home}_{away}"
            if unique_key: b_key += f"_{unique_key}"
            
            # Action Button (Small)
            if st.button("Ver ➡️", key=b_key, help="Ver Análisis Completo", use_container_width=True):
                 navigate_callback(match)
