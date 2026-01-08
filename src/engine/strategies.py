
def cond_home_dominant(row):
    """
    Local Dominante (Versión Pro):
    Local marca medias > 1.3 y tiene momentum (No pierde mucho).
    Factor Rival: Visitante ha encajado en 60% de sus salidas (CleanSheetRate <= 0.40).
    """
    home_strong = (row.get('HomeAvgGoalsFor', 0) > 1.25 and 
                   row.get('HomePPG', 0) > 1.35 and
                   row.get('HomeWinsLast5', 0) >= 1) # Relaxed to 1 win in 5
                   
    # Factor Rival
    visitor_weak_defense = (row.get('AwayCleanSheet_Rate', 1.0) <= 0.50) # Relaxed to 50%
    
    # 4.0 Check: Regression Risk
    # Relaxed Threshold
    regression_risk = row.get('HomeZScore_Goals', 0) > 3.5
    
    return home_strong and visitor_weak_defense and not regression_risk

def cond_goal_fest_strict(row):
    """
    Festival de Goles (>2.5) Pro 4.0 (Optimized):
    Frecuencia Over: > 50%.
    Poder Ofensivo Combinado > 2.2.
    """
    # Consistency
    consistent_over = (row.get('HomeOver25_Rate', 0) >= 0.50 and row.get('AwayOver25_Rate', 0) >= 0.50)
    
    # Combined Scoring Power - Relaxed to 2.2
    combined_poa = row.get('HomeAvgGoalsFor', 0) + row.get('AwayAvgGoalsFor', 0)
    
    # Momentum Check (New)
    momentum = row.get('HomeZScore_Goals', 0) > -0.8 # Relaxed
    
    # TRAP FILTERS Check (Keep these to avoid bad bets, but rely on user judgement)
    traps_active = (row.get('Trap_FearError', 0) + row.get('Trap_StyleClash', 0) + row.get('Trap_Fatigue', 0)) > 2 # Very relaxed, only blocking if MULTIPLE traps
    
    if traps_active: return False
    
    if not consistent_over: return False
    
    return combined_poa > 2.2 and momentum

def cond_btts_high(row):
    """
    Ambos Marcan (Alta Probabilidad) Pro 4.0:
    Consistencia BTTS > 45%.
    """
    consistent_btts = (row.get('HomeBTTS_Rate', 0) >= 0.45 and row.get('AwayBTTS_Rate', 0) >= 0.45)
    leaky = (row.get('HomeCleanSheet_Rate', 1.0) < 0.50 and row.get('AwayCleanSheet_Rate', 1.0) < 0.50)
    
    # Check Luck Filter: If Goals Z-Score >> xG Z-Score, they are lucky.
    h_lucky = (row.get('HomeZScore_Goals', 0) - row.get('HomeZScore_xG', 0)) > 2.0
    a_lucky = (row.get('AwayZScore_Goals', 0) - row.get('AwayZScore_xG', 0)) > 2.0
    
    if h_lucky or a_lucky: return False
    
    return consistent_btts and leaky

def cond_over_15_safe(row):
    """
    Seguro de Gol (>1.5) Pro 4.0:
    Suelo de Goles + CONSISTENCIA Z-SCORE.
    """
    combined_avg = row.get('HomeAvgGoalsFor', 0) + row.get('AwayAvgGoalsFor', 0)
    
    # Volatility Check (Stability) - Relaxed
    stable_std = (row.get('HomeStdDevGoals', 2.0) < 1.6 and row.get('AwayStdDevGoals', 2.0) < 1.6)
    
    # Z-Score Consistency Check - Relaxed
    h_z = row.get('HomeZScore_Goals', 0)
    a_z = row.get('AwayZScore_Goals', 0)
    consistent_z = (-1.5 < h_z < 3.0) and (-1.5 < a_z < 3.0)
    
    no_zeros = (row.get('HomeZeroZero_Count', 0) <= 1 and row.get('AwayZeroZero_Count', 0) <= 1) # Allow 1 zero-zero
    
    return (combined_avg > 1.9) and stable_std and no_zeros and consistent_z

# --- Defines ---

def cond_paper_tiger_away(row):
    """
    Cazando Tigres de Papel Pro (Lay Visitante):
    Visitante PPG < 1.1.
    """
    away_bad = (row.get('AwayPPG', 0) < 1.1)
    
    # Visitor struggles away
    visitor_leaky = row.get('AwayCleanSheet_Rate', 1.0) < 0.40 # Relaxed
    visitor_loses = row.get('AwayLossesLast5', 0) >= 2
    
    # Home Strong enough to punish
    home_score = row.get('HomeAvgGoalsFor', 0) > 1.2
    
    return away_bad and visitor_leaky and visitor_loses and home_score

def cond_cards_battle(row):
    """
    Batalla de Tarjetas Pro:
    Ref avg > 4.2.
    """
    ref_strict = row.get('RefAvgCards', 4.0) > 4.2
    
    # Fouls Check
    fouls_high = (row.get('HomeAvgFouls', 0) + row.get('AwayAvgFouls', 0)) > 24
    
    # Fallback if no fouls data (0) -> Use Card intensity
    if row.get('HomeAvgFouls', 0) == 0:
        fouls_high = (row.get('HomeAvgCardsFor', 0) + row.get('AwayAvgCardsFor', 0)) > 3.8
        
    return ref_strict and fouls_high

# --- NEW PATTERNS (Shots, Corners, Cards Enhanced) ---

def cond_high_shots_volume(row):
    """
    Lluvia de Tiros (>23):
    """
    h_s = row.get('HomeAvgShotsFor', 0) + row.get('AwayAvgShotsAgainst', 0)
    a_s = row.get('AwayAvgShotsFor', 0) + row.get('HomeAvgShotsAgainst', 0)
    
    # Average expected shots for Home and Away
    exp_shots_total = (h_s/2) + (a_s/2)
    return exp_shots_total > 23

def cond_high_sot_sniper(row):
    """
    Francotiradores (Tiros a Puerta > 8.5):
    """
    # Shots on Target
    h_st = row.get('HomeAvgShotsTargetFor', 0) + row.get('AwayAvgShotsTargetAgainst', 0)
    a_st = row.get('AwayAvgShotsTargetFor', 0) + row.get('HomeAvgShotsTargetAgainst', 0)
    
    exp_sot_total = (h_st/2) + (a_st/2)
    return exp_sot_total > 8.5

def cond_corner_fest(row):
    """
    Fiesta de Córners (>9.5):
    """
    # Corners
    h_c = row.get('HomeAvgCornersFor', 0) + row.get('AwayAvgCornersAgainst', 0)
    a_c = row.get('AwayAvgCornersFor', 0) + row.get('HomeAvgCornersAgainst', 0)
    
    exp_corners = (h_c/2) + (a_c/2)
    return exp_corners > 9.5

def cond_card_heavy_strict(row):
    """
    Carnicería (Tarjetas > 4.5):
    """
    ref_strict = row.get('RefAvgCards', 4.0) > 4.5
    team_aggr = (row.get('HomeAvgCardsFor', 0) + row.get('AwayAvgCardsFor', 0)) > 4.5
    return ref_strict and team_aggr 

# --- Targets defined for Backtesting ---

def target_home_win(row): return row['FTHG'] > row['FTAG']
def target_away_win(row): return row['FTAG'] > row['FTHG']
def target_over_25(row): return (row['FTHG'] + row['FTAG']) > 2.5
def target_over_15(row): return (row['FTHG'] + row['FTAG']) > 1.5
def target_btts(row): return (row['FTHG'] > 0) and (row['FTAG'] > 0)

# New Targets
def target_shots_25(row): return (row.get('HS',0) + row.get('AS',0)) > 25
def target_sot_9(row): return (row.get('HST',0) + row.get('AST',0)) > 9.5
def target_corn_10(row): return (row.get('HC',0) + row.get('AC',0)) > 10.5
def target_cards_55(row): 
    cards = row.get('HY',0) + row.get('AY',0) + row.get('HR',0) + row.get('AR',0)
    return cards > 5.5

# --- Registry ---

PREMATCH_PATTERNS = [
    ("Local Dominante (Estricto)", cond_home_dominant, target_home_win, "B365H"),
    ("Festival de Goles (>2.5)", cond_goal_fest_strict, target_over_25, "B365_Over2.5"),
    ("Seguro de Gol (>1.5)", cond_over_15_safe, target_over_15, "B365_Over1.5"), 
    ("Cazando Tigres de Papel (Lay Visitante)", cond_paper_tiger_away, target_home_win, "B365H"),
    ("Batalla de Tarjetas (>3.5)", cond_cards_battle, lambda r: (r.get('HY',0)+r.get('AY',0)+r.get('HR',0)+r.get('AR',0)) > 3.5, "B365_Cards_Over3.5"),
    ("Ambos Marcan (BTTS)", cond_btts_high, target_btts, "B365_BTTS_Yes"),
    
    # New Patterns (No Odds usually available, so no ROI calc)
    ("Lluvia de Tiros (>25)", cond_high_shots_volume, target_shots_25, None),
    ("Francotiradores (SoT > 9.5)", cond_high_sot_sniper, target_sot_9, None),
    ("Fiesta de Córners (>10.5)", cond_corner_fest, target_corn_10, None),
    ("Carnicería (Tarjetas > 5.5)", cond_card_heavy_strict, target_cards_55, None)
]
