
def cond_home_dominant(row):
    """
    Local Dominante (Versión Pro):
    Local marca medias > 1.5 y tiene momentum (No pierde mucho).
    Factor Rival: Visitante ha encajado en 65% de sus salidas (CleanSheetRate < 0.35).
    """
    home_strong = (row.get('HomeAvgGoalsFor', 0) > 1.5 and 
                   row.get('HomePPG', 0) > 1.5 and
                   row.get('HomeWinsLast5', 0) >= 2) # Relaxed from 3
                   
    # Factor Rival
    visitor_weak_defense = (row.get('AwayCleanSheet_Rate', 1.0) <= 0.35) # Relaxed from 0.2
    
    # 4.0 Check: Regression Risk
    # If Home Z-Score is excessively high (> 2.5), they are overperforming and due for a crash.
    regression_risk = row.get('HomeZScore_Goals', 0) > 2.8 # Relaxed from 2.5
    
    return home_strong and visitor_weak_defense and not regression_risk

def cond_goal_fest_strict(row):
    """
    Festival de Goles (>2.5) Pro 4.0 (Optimized):
    Frecuencia Over: > 60%.
    Poder Ofensivo Combinado > 2.5 (Relaxed from 3.0).
    Momentum: Z-Score Local Positivo (No en crisis).
    """
    # Consistency
    consistent_over = (row.get('HomeOver25_Rate', 0) >= 0.60 and row.get('AwayOver25_Rate', 0) >= 0.60)
    
    # Combined Scoring Power - TIGHTENED to 3.0 -> Relaxed to 2.5
    combined_poa = row.get('HomeAvgGoalsFor', 0) + row.get('AwayAvgGoalsFor', 0)
    
    # Momentum Check (New)
    # Ensure Home team is not in a scoring slump (Z > -0.2)
    momentum = row.get('HomeZScore_Goals', 0) > -0.5 # Relaxed
    
    # TRAP FILTERS Check
    traps_active = (row.get('Trap_FearError', 0) + row.get('Trap_StyleClash', 0) + row.get('Trap_Fatigue', 0)) > 0
    
    if traps_active: return False
    
    if not consistent_over: return False
    
    return combined_poa > 2.5 and momentum

def cond_btts_high(row):
    """
    Ambos Marcan (Alta Probabilidad) Pro 4.0:
    Consistencia BTTS > 50%.
    """
    consistent_btts = (row.get('HomeBTTS_Rate', 0) >= 0.50 and row.get('AwayBTTS_Rate', 0) >= 0.50)
    leaky = (row.get('HomeCleanSheet_Rate', 1.0) < 0.40 and row.get('AwayCleanSheet_Rate', 1.0) < 0.40)
    
    # Check Luck Filter: If Goals Z-Score >> xG Z-Score, they are lucky.
    h_lucky = (row.get('HomeZScore_Goals', 0) - row.get('HomeZScore_xG', 0)) > 1.8
    a_lucky = (row.get('AwayZScore_Goals', 0) - row.get('AwayZScore_xG', 0)) > 1.8
    
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
    stable_std = (row.get('HomeStdDevGoals', 2.0) < 1.4 and row.get('AwayStdDevGoals', 2.0) < 1.4)
    
    # Z-Score Consistency Check
    h_z = row.get('HomeZScore_Goals', 0)
    a_z = row.get('AwayZScore_Goals', 0)
    consistent_z = (-1.0 < h_z < 2.5) and (-1.0 < a_z < 2.5)
    
    no_zeros = (row.get('HomeZeroZero_Count', 0) == 0 and row.get('AwayZeroZero_Count', 0) == 0)
    
    return (combined_avg > 2.0) and stable_std and no_zeros and consistent_z

# --- Defines ---

def cond_paper_tiger_away(row):
    """
    Cazando Tigres de Papel Pro (Lay Visitante):
    Visitante PPG < 1.0.
    Filtro Estricto: Visitante pierde > 50% fuera (LossesLast5 >= 2).
    Defensa coladero: Encaja en > 70% partidos (CleanSheet < 0.30).
    """
    away_bad = (row.get('AwayPPG', 0) < 1.0)
    
    # Visitor struggles away - TIGHTENED
    visitor_leaky = row.get('AwayCleanSheet_Rate', 1.0) < 0.30 # Tightened from 0.2
    visitor_loses = row.get('AwayLossesLast5', 0) >= 2
    
    # Home Strong enough to punish
    home_score = row.get('HomeAvgGoalsFor', 0) > 1.3
    
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

# --- NEW PATTERNS (Shots, Corners, Cards Enhanced) ---

def cond_high_shots_volume(row):
    """
    Lluvia de Tiros (>25):
    Equipos que disparan mucho y conceden mucho.
    Total Tiros proyectado > 25.
    """
    # Requires Shot Data: HS (HomeShots), AS (AwayShots) -> Avg
    # Features usually rely on 'HomeAvgShotsFor', 'AwayAvgShotsFor'
    h_s = row.get('HomeAvgShotsFor', 0) + row.get('AwayAvgShotsAgainst', 0)
    a_s = row.get('AwayAvgShotsFor', 0) + row.get('HomeAvgShotsAgainst', 0)
    
    # Average expected shots for Home and Away
    exp_shots_total = (h_s/2) + (a_s/2)
    return exp_shots_total > 25

def cond_high_sot_sniper(row):
    """
    Francotiradores (Tiros a Puerta > 9.5):
    Alta precisión ofensiva.
    """
    # Shots on Target
    h_st = row.get('HomeAvgShotsTargetFor', 0) + row.get('AwayAvgShotsTargetAgainst', 0)
    a_st = row.get('AwayAvgShotsTargetFor', 0) + row.get('HomeAvgShotsTargetAgainst', 0)
    
    exp_sot_total = (h_st/2) + (a_st/2)
    return exp_sot_total > 9.5

def cond_corner_fest(row):
    """
    Fiesta de Córners (>10.5):
    Equipos verticales, muchos centros, defensas despejadoras.
    """
    # Corners
    h_c = row.get('HomeAvgCornersFor', 0) + row.get('AwayAvgCornersAgainst', 0)
    a_c = row.get('AwayAvgCornersFor', 0) + row.get('HomeAvgCornersAgainst', 0)
    
    exp_corners = (h_c/2) + (a_c/2)
    return exp_corners > 10.5

def cond_card_heavy_strict(row):
    """
    Carnicería (Tarjetas > 5.5) Extreme:
    Arbitro muy estricto (>5.0) y equipos agresivos.
    """
    ref_strict = row.get('RefAvgCards', 4.0) > 5.0
    team_aggr = (row.get('HomeAvgCardsFor', 0) + row.get('AwayAvgCardsFor', 0)) > 5.0
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
    ("Festival de Goles (>2.5)", cond_goal_fest_strict, target_over_25, "B365>2.5"),
    ("Seguro de Gol (>1.5)", cond_over_15_safe, target_over_15, "B365>1.5"), 
    ("Cazando Tigres de Papel (Lay Visitante)", cond_paper_tiger_away, target_home_win, "B365H"),
    ("Batalla de Tarjetas (>3.5)", cond_cards_battle, lambda r: (r.get('HY',0)+r.get('AY',0)+r.get('HR',0)+r.get('AR',0)) > 3.5, "B365>3.5"),
    ("Ambos Marcan (BTTS)", cond_btts_high, target_btts, "B365GG"),
    
    # New Patterns (No Odds usually available, so no ROI calc)
    ("Lluvia de Tiros (>25)", cond_high_shots_volume, target_shots_25, None),
    ("Francotiradores (SoT > 9.5)", cond_high_sot_sniper, target_sot_9, None),
    ("Fiesta de Córners (>10.5)", cond_corner_fest, target_corn_10, None),
    ("Carnicería (Tarjetas > 5.5)", cond_card_heavy_strict, target_cards_55, None)
]
