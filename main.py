import argparse
import sys
from src.data.loader import DataLoader

def main():
    parser = argparse.ArgumentParser(description="Sports Betting Value Analyzer")
    parser.add_argument('--leagues', nargs='+', default=['SP1', 'E0', 'D1', 'I1', 'F1'], help='Leagues to analyze (e.g., SP1 E0)')
    parser.add_argument('--seasons', nargs='+', default=['2526', '2425', '2324', '2223', '2122', '2021'], help='Seasons to fetch (e.g., 2324)')
    
    args = parser.parse_args()

    print(f"Initializing Analysis for Leagus: {args.leagues}, Seasons: {args.seasons}")
    
    loader = DataLoader()
    data = loader.fetch_data(args.leagues, args.seasons)
    
    print(f"Loaded {len(data)} matches.")
    
    from src.engine.features import FeatureEngineer
    
    engineer = FeatureEngineer(data)
    data = engineer.add_rest_days()
    data = engineer.add_rolling_stats(window=5)
    data = engineer.add_relative_strength()
    
    print("Features calculated successfully.")
    
    from src.engine.patterns import PatternAnalyzer
    
    analyzer = PatternAnalyzer(data)
    
    # Define some sample patterns
    # Condition: Home Team Rest > 7 days AND Away Team Rest < 3 days
    def cond_rest_advantage(row):
        return row['HomeRestDays'] > 7 and row['AwayRestDays'] < 4
        
    def target_home_win(row):
        return row['FTHG'] > row['FTAG']
        
    # Condition: Home High Attack Strength (> 1.5) and Away Weak Defense (implied by Attack Strength > 1.2 for Home)
    def cond_high_attack_home(row):
        # HomeAttackStrength = HomeAvgShotsTargetFor / AwayAvgShotsTargetAgainst
        # If > 1.3, means Home creates 30% more shots than Away usually concedes? Or relative to avg.
        # Let's use simple Avg Goals for now as it's easier to interpret
        return row['HomeAvgGoalsFor'] > 2.0 and row['AwayAvgGoalsAgainst'] > 1.5
        
    def target_over_25(row):
        return (row['FTHG'] + row['FTAG']) > 2.5

    patterns = [
        ("Rest Advantage Home", cond_rest_advantage, target_home_win, "B365H"),
        ("High Scoring Potential", cond_high_attack_home, target_over_25, "B365>2.5")
    ]
    
    print("Scanning for patterns...")
    summary, details = analyzer.scan_patterns(patterns)
    
    print("\nPattern Results:")
    print(summary.to_string())
    
    if not summary.empty:
        from src.reporting.excel_generator import ExcelGenerator
        generator = ExcelGenerator("betting_analysis_report.xlsx")
        generator.generate_report(summary, details)
        print(f"Report saved to betting_analysis_report.xlsx")
        
    # --- Prediction Mode ---
    print("\nStarting Prediction Phase...")
    from src.data.upcoming import FixturesFetcher
    from src.engine.predictor import Predictor
    
    fetcher = FixturesFetcher()
    # Fetch for relevant leagues
    upcoming = fetcher.fetch_upcoming(['E0', 'SP1', 'D1', 'I1', 'F1'])
    
    if not upcoming.empty:
        print(f"Analyzing {len(upcoming)} upcoming matches...")
        predictor = Predictor(data)
        
        predictions = []
        
        for idx, match in upcoming.iterrows():
            row = predictor.predict_match(match['HomeTeam'], match['AwayTeam'])
            if not row:
                continue
                
            # Check Patterns
            for name, condition, target, odds_col in patterns:
                try:
                    if condition(row):
                         predictions.append({
                             'Date': match['Date'],
                             'League': match['Div'],
                             'HomeTeam': match['HomeTeam'],
                             'AwayTeam': match['AwayTeam'],
                             'Pattern': name,
                             'Suggestion': 'Check Bet365' 
                         })
                except Exception as e:
                    pass
                    
        if predictions:
            pred_df = pd.DataFrame(predictions)
            print("\nUPCOMING PREDICTIONS:")
            print(pred_df)
            pred_df.to_excel("upcoming_predictions.xlsx", index=False)
            print("Saved to upcoming_predictions.xlsx")
        else:
            print("No patterns identified in upcoming matches.")
    
if __name__ == "__main__":
    main()
