import pandas as pd
import xlsxwriter

class ExcelGenerator:
    def __init__(self, filename="betting_analysis.xlsx"):
        self.filename = filename

    def generate_report(self, patterns_df, matches_details=None):
        """
        patterns_df: DataFrame with summary of patterns (Name, Matches, ROI, EV)
        matches_details: Dict of {pattern_name: dataframe_of_matches}
        """
        print(f"Generating Excel report: {self.filename}...")
        
        with pd.ExcelWriter(self.filename, engine='xlsxwriter') as writer:
            # 1. Summary Sheet
            patterns_df.to_excel(writer, sheet_name='Summary', index=False)
            
            summary_sheet = writer.sheets['Summary']
            workbook = writer.book
            
            # Formats
            fmt_pct = workbook.add_format({'num_format': '0.00%'})
            fmt_dec = workbook.add_format({'num_format': '0.00'})
            fmt_bold = workbook.add_format({'bold': True})
            
            summary_sheet.set_column('A:A', 25) # Name
            summary_sheet.set_column('C:C', 12, fmt_pct) # Probability
            summary_sheet.set_column('E:G', 12, fmt_pct) # ROI, EV
            
            # 2. Detailed Sheets for each Pattern
            if matches_details:
                for pat_name, df in matches_details.items():
                    # Sanitize sheet name
                    sheet_name = pat_name[:30].replace(":", "").replace("/", "-")
                    
                    # Select useful columns
                    cols_to_show = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'B365H', 'B365D', 'B365A', 'B365>2.5']
                    # Add any computed feature columns if they exist
                    feature_cols = [c for c in df.columns if c not in cols_to_show and c in ['HomeRestDays', 'HomeAttackStrength', 'AwayRestDays']]
                    
                    final_df = df[cols_to_show + feature_cols]
                    final_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("Excel report generated successfully.")
