import pandas as pd
from src.data.loader import DataLoader
from src.engine.streaks import StreakAnalyzer

# Load data directly
loader = DataLoader()
# Try loading SP1 for last few seasons
df = loader.fetch_data(['SP1', 'E0'], ['2324', '2425'])
print(f"Loaded {len(df)} matches")

if not df.empty:
    analyzer = StreakAnalyzer(df)
    try:
        streaks = analyzer.get_active_streaks()
        print(f"Calculated {len(streaks)} streaks")
        if not streaks.empty:
            print(streaks.head())
        else:
            print("Streaks DF is empty")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("DataFrame is empty")
