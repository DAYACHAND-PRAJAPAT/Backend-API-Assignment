import pandas as pd
import numpy as np

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a cleaned DataFrame to flag statistical outliers and 
        cross-border merchant/currency mismatches.
        """
        # Ensure working on a clean copy
        df = df.copy()
        
        # Initialize default columns if they don't exist
        df['is_anomaly'] = False
        df['anomaly_reason'] = ""
        
        if df.empty:
            return df

        # --- 1. Calculate Statistical Outliers (Per Account Median) ---
        # Group by account_id and calculate the median amount for each account
        medians = df.groupby('account_id')['amount'].transform('median')
        
        # Condition: Amount is strictly greater than 3x the account's median
        outlier_condition = df['amount'] > (3 * medians)
        
        # --- 2. Calculate Cross-Border Mismatches ---
        # Domestic brands listed in assignment instructions
        domestic_brands = ['SWIGGY', 'OLA', 'IRCTC', 'ZOMATO'] # Added Zomato based on dataset patterns
        
        # Normalize merchant names for strict comparison
        merchant_upper = df['merchant'].str.upper()
        
        # Condition: Currency is USD but merchant belongs to domestic brands
        mismatch_condition = (df['currency'] == 'USD') & (merchant_upper.isin(domestic_brands))
        
        # --- 3. Apply Flags and Compile Reasons ---
        for idx, row in df.iterrows():
            reasons = []
            
            if outlier_condition.loc[idx]:
                account_median = df.groupby('account_id')['amount'].median().loc[row['account_id']]
                reasons.append(f"Statistical Outlier: Amount ({row['amount']}) exceeds 3x the account median ({account_median:.2f})")
            
            if mismatch_condition.loc[idx]:
                reasons.append(f"Cross-Border Mismatch: Domestic merchant '{row['merchant']}' billed in USD")
                
            if reasons:
                df.at[idx, 'is_anomaly'] = True
                df.at[idx, 'anomaly_reason'] = " | ".join(reasons)
                
        return df