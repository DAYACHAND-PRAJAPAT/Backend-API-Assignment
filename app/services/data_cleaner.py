import pandas as pd
import io
from datetime import datetime
from typing import Tuple

class DataCleaner:
    @staticmethod
    def clean_csv(file_bytes: bytes) -> Tuple[pd.DataFrame, int, int]:
        """
        Reads a raw CSV stream, cleans it according to assignment guidelines,
        and returns (cleaned_dataframe, raw_row_count, cleaned_row_count).
        """
        # 1. Load raw bytes safely into a Pandas DataFrame
        df_raw = pd.read_csv(io.BytesIO(file_bytes))
        raw_row_count = len(df_raw)
        
        # 2. Remove exact duplicate rows completely
        df = df_raw.drop_duplicates().copy()
        
        # 3. Clean and Normalize columns
        # Fill completely missing fields with default tracking strings or handle floats safely
        df['merchant'] = df['merchant'].fillna('Unknown').astype(str).str.strip()
        df['account_id'] = df['account_id'].fillna('Unknown').astype(str).str.strip()
        df['notes'] = df['notes'].fillna('').astype(str).str.strip()
        
        # Normalize Casing for Status
        df['status'] = df['status'].fillna('PENDING').astype(str).str.upper().str.strip()
        
        # Fill missing categories with 'Uncategorised'
        df['category'] = df['category'].fillna('Uncategorised').astype(str).str.strip()
        df.loc[df['category'] == '', 'category'] = 'Uncategorised'
        
        # Strip currency symbols (like $) from amount strings and cast to float
        if df['amount'].dtype == object:
            df['amount'] = df['amount'].astype(str).str.replace('$', '', regex=False)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        
        # Normalize currency casing (e.g. 'inr' -> 'INR')
        df['currency'] = df['currency'].fillna('INR').astype(str).str.upper().str.strip()
        
        # Normalize mixed date formats (DD-MM-YYYY or YYYY/MM/DD) to ISO 8601 (YYYY-MM-DD)
        df['date'] = df['date'].apply(DataCleaner._normalize_date)
        
        cleaned_row_count = len(df)
        return df, raw_row_count, cleaned_row_count

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        if pd.isna(date_str) or str(date_str).strip() == '':
            return datetime.utcnow().strftime('%Y-%m-%d')
        
        date_str = str(date_str).strip()
        
        # Try parsing potential formats present in the dirty dataset
        for fmt in ('%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d'):
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        # Fallback default if completely corrupted
        return datetime.utcnow().strftime('%Y-%m-%d')