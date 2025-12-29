def cond_home_dominant(row):
    """
    Local Dominante (Versión Pro):
    Local marca medias > 1.6 y tiene momentum (No pierde mucho).
    Factor Rival: Visitante ha encajado en 80% de sus salidas (CleanSheetRate < 0.2).
    """
    home_strong = (row.get('HomeAvgGoalsFor', 0) > 1.6 and 
                   row.get('HomePPG', 0) > 1.6 and
                   row.get('HomeWinsLast5', 0) >= 3)
                   
    # Factor Rival
    visitor_weak_defense = (row.get('AwayCleanSheet_Rate', 1.0) <= 0.2)
    
    # 4.0 Check: Regression Risk
    # If Home Z-Score is excessively high (> 2.5), they are overperforming and due for a crash.
    regression_risk = row.get('HomeZScore_Goals', 0) > 2.5
    
    return home_strong and visitor_weak_defense and not regression_risk

def cond_goal_fest_strict(row):
    """
    Festival de Goles (>2.5) Pro 4.0 (Optimized):
    Frecuencia Over: > 66%.
    Poder Ofensivo Combinado > 3.0 (Subido de 2.8).
    Momentum: Z-Score Local Positivo (No en crisis).
    """
    # Consistency
    consistent_over = (row.get('HomeOver25_Rate', 0) >= 0.66 and row.get('AwayOver25_Rate', 0) >= 0.66)
    
    # Combined Scoring Power - TIGHTENED to 3.0
    combined_poa = row.get('HomeAvgGoalsFor', 0) + row.get('AwayAvgGoalsFor', 0)
    
    # Momentum Check (New)
    # Ensure Home team is not in a scoring slump (Z > -0.2)
    momentum = row.get('HomeZScore_Goals', 0) > -0.2
    
    # TRAP FILTERS Check
    traps_active = (row.get('Trap_FearError', 0) + row.get('Trap_StyleClash', 0) + row.get('Trap_Fatigue', 0)) > 0
    
    if traps_active: return False
    
    if not consistent_over: return False
    
    return combined_poa > 3.0 and momentum

def cond_btts_high(row):
    """
    Ambos Marcan (Alta Probabilidad) Pro 4.0:
    Consistencia BTTS > 55%.
    """
    consistent_btts = (row.get('HomeBTTS_Rate', 0) >= 0.55 and row.get('AwayBTTS_Rate', 0) >= 0.55)
    leaky = (row.get('HomeCleanSheet_Rate', 1.0) < 0.35 and row.get('AwayCleanSheet_Rate', 1.0) < 0.35)
    
    # Check Luck Filter: If Goals Z-Score >> xG Z-Score, they are lucky.
    h_lucky = (row.get('HomeZScore_Goals', 0) - row.get('HomeZScore_xG', 0)) > 1.5
    a_lucky = (row.get('AwayZScore_Goals', 0) - row.get('AwayZScore_xG', 0)) > 1.5
    
    if h_lucky or a_lucky: return False
    
    return consistent_btts and leaky

def cond_over_15_safe(row):
    """
    Seguro de Gol (>1.5) Pro 4.0:
    Suelo de Goles + CONSISTENCIA Z-SCORE.
    Z-Score debe estar en rango "Normal" (-0.5 a 1.0).
    """
    combined_avg = row.get('HomeAvgGoalsFor', 0) + row.get('AwayAvgGoalsFor', 0)
    
    # Volatility Check (Stability)
    stable_std = (row.get('HomeStdDevGoals', 2.0) < 1.3 and row.get('AwayStdDevGoals', 2.0) < 1.3)
    
    # Z-Score Consistency Check
    h_z = row.get('HomeZScore_Goals', 0)
    a_z = row.get('AwayZScore_Goals', 0)
    consistent_z = (-1.0 < h_z < 2.0) and (-1.0 < a_z < 2.0)
    
    no_zeros = (row.get('HomeZeroZero_Count', 0) == 0 and row.get('AwayZeroZero_Count', 0) == 0)
    
    return (combined_avg > 2.2) and stable_std and no_zeros and consistent_z

# --- Defines ---

def cond_paper_tiger_away(row):
    """
    Cazando Tigres de Papel Pro (Lay Visitante):
    Visitante PPG < 0.9.
    Filtro Estricto: Visitante pierde > 60% fuera (LossesLast5 >= 3).
    Defensa coladero: Encaja en > 85% partidos (CleanSheet < 0.15).
    """
    away_bad = (row.get('AwayPPG', 0) < 0.9)
    
    # Visitor struggles away - TIGHTENED
    visitor_leaky = row.get('AwayCleanSheet_Rate', 1.0) < 0.15 # Tightened from 0.2
    visitor_loses = row.get('AwayLossesLast5', 0) >= 3
    
    # Home Strong enough to punish
    home_score = row.get('HomeAvgGoalsFor', 0) > 1.4
    
    return away_bad and visitor_leaky and visitor_loses and home_score

def cond_cards_battle(row):
    """
    Batalla de Tarjetas Pro:
    Ref avg > 4.5 STRICT.
    Tension: Avg Fouls combined > 26 (High intensity).
    """
    ref_strict = row.get('RefAvgCards', 4.0) > 4.5
    
    # Fouls Check (if data available, else fallback to cards intensity)
    fouls_high = (row.get('HomeAvgFouls', 0) + row.get('AwayAvgFouls', 0)) > 26
    
    # Fallback if no fouls data (0) -> Use Card intensity
    if row.get('HomeAvgFouls', 0) == 0:
        fouls_high = (row.get('HomeAvgCardsFor', 0) + row.get('AwayAvgCardsFor', 0)) > 4.0
        
    return ref_strict and fouls_high

# --- Targets defined for Backtesting ---

def target_home_win(row): return row['FTHG'] > row['FTAG']
def target_away_win(row): return row['FTAG'] > row['FTHG']
def target_over_25(row): return (row['FTHG'] + row['FTAG']) > 2.5
def target_over_15(row): return (row['FTHG'] + row['FTAG']) > 1.5
def target_btts(row): return (row['FTHG'] > 0) and (row['FTAG'] > 0)

# --- Registry ---

PREMATCH_PATTERNS = [
    ("Local Dominante (Estricto)", cond_home_dominant, target_home_win, "B365H"),
    ("Festival de Goles (>2.5)", cond_goal_fest_strict, target_over_25, "B365>2.5"),
    ("Seguro de Gol (>1.5)", cond_over_15_safe, target_over_15, "B365>1.5"), 
    ("Cazando Tigres de Papel (Lay Visitante)", cond_paper_tiger_away, target_home_win, "B365H"),
    ("Batalla de Tarjetas (>3.5)", cond_cards_battle, lambda r: (r['HY']+r['AY']+r['HR']+r['AR']) > 3.5, "B365>3.5"),
    ("Ambos Marcan (BTTS)", cond_btts_high, target_btts, "B365GG")
]
