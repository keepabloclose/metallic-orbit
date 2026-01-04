from src.engine.strategies import PREMATCH_PATTERNS

class PatternAnalyzer:
    def __init__(self, df):
        self.df = df.copy()
        
    def check_patterns(self, row_dict):
        """
        Checks a single match (row_dict) against all registered PREMATCH_PATTERNS.
        Returns a list of strings (pattern names) that match.
        """
        found = []
        for item in PREMATCH_PATTERNS:
            # Handle 3 or 4 item tuples
            if len(item) == 4:
                name, condition, target, odds = item
            else:
                name, condition, target = item
                
            try:
                if condition(row_dict):
                    found.append(name)
            except Exception as e:
                # print(f"Error check pattern {name}: {e}")
                pass
                
        return found

    def evaluate_pattern(self, condition_func, target_event_func, odds_column=None, min_samples=20):
        """
        Evaluates a specific pattern against the historical data.
        
        Args:
            condition_func: A tailored function that takes a row and returns True if the pre-match condition is met.
            target_event_func: A function that takes a row and returns True if the target event happened (e.g. Over 2.5 Goals).
            odds_column: Column name containing the odds for the target event (e.g. 'B365H').
            min_samples: Minimum number of matches meeting the condition to consider the result valid.
            
        Returns:
            dict: {
                'matches_found': int,
                'probability': float,
                'roi': float (optional)
            }
        """
        # We need to apply this to the generic dataframe. 
        # Ideally, we vectorize this, but for complex conditions, `apply` is easier to start with.
        
        # Filter dataframe for matches where condition is True
        # Note: We must ensure we don't look ahead. The condition_func must only use pre-match features.
        
        matches_meeting_condition = self.df[self.df.apply(condition_func, axis=1)]
        n_samples = len(matches_meeting_condition)
        
        if n_samples < min_samples:
            return None
        
        # Check how often target event happened
        events_happened = matches_meeting_condition.apply(target_event_func, axis=1)
        probability = events_happened.mean()
        
        result = {
            'matches_found': n_samples,
            'probability': probability,
            'success_count': events_happened.sum(),
            'dataframe': matches_meeting_condition
        }
        
        if odds_column and odds_column in self.df.columns:
            # Calculate Profit/Loss (assuming 1 unit stake)
            # P/L = (Odds - 1) if Win, -1 if Loss
            # Which simplifies to: (Odds * Win_Boolean) - 1
            
            odds = matches_meeting_condition[odds_column]
            # Replace NaNs with 1.0 (refund) or skip? Skip is better.
            valid_odds_indices = odds.dropna().index
            
            if len(valid_odds_indices) < n_samples:
                 # Warning: missing odds
                 pass
                 
            # We filter for valid odds
            relevant_matches = matches_meeting_condition.loc[valid_odds_indices]
            relevant_events = events_happened.loc[valid_odds_indices]
            relevant_odds = odds.loc[valid_odds_indices]
            
            total_stake = len(relevant_matches)
            total_return = (relevant_odds * relevant_events).sum()
            roi = (total_return - total_stake) / total_stake if total_stake > 0 else 0
            
            result['roi'] = roi
            result['avg_odds'] = relevant_odds.mean()
            
        return result

    def scan_patterns(self, patterns_list):
        """
        Scans a list of patterns and returns the results.
        patterns_list: list of (name, condition, target, odds_col)
        """
        results = []
        for item in patterns_list:
            if len(item) == 4:
                name, condition, target, odds_col = item
            else:
                name, condition, target = item
                odds_col = None
                
            stats = self.evaluate_pattern(condition, target, odds_column=odds_col)
            if stats:
                row = {
                    'pattern_name': name,
                    'matches': stats['matches_found'],
                    'probability': stats['probability'],
                    'successes': stats['success_count']
                }
                if 'roi' in stats:
                    row['roi'] = stats['roi']
                    row['avg_odds'] = stats['avg_odds']
                    row['EV'] = (stats['probability'] * stats['avg_odds']) - 1
                results.append(row)
        
        if not results:
            return pd.DataFrame(), {}
            
        summary_df = pd.DataFrame(results).sort_values('probability', ascending=False)
        
        # Collect details
        details = {}
        for item in patterns_list:
            name = item[0]
            # Re-evaluate to get df (slightly inefficient but cleaner for now, or we could have stored it)
            # Actually, let's store it in the loop above? 
            # Better: refactor the loop above to store 'dataframe' in a separate dict
            pass 
            
        # Refactored Loop for efficiency
        final_results = []
        details = {}
        
        for item in patterns_list:
            if len(item) == 4:
                name, condition, target, odds_col = item
            else:
                name, condition, target = item
                odds_col = None
            
            stats = self.evaluate_pattern(condition, target, odds_column=odds_col)
            if stats:
                row = {
                    'pattern_name': name,
                    'matches': stats['matches_found'],
                    'probability': stats['probability'],
                    'successes': stats['success_count']
                }
                if 'roi' in stats:
                    row['roi'] = stats['roi']
                    row['avg_odds'] = stats['avg_odds']
                    row['EV'] = (stats['probability'] * stats['avg_odds']) - 1
                final_results.append(row)
                details[name] = stats['dataframe']
                
        if not final_results:
            return pd.DataFrame(), {}
            
        return pd.DataFrame(final_results).sort_values('probability', ascending=False), details
