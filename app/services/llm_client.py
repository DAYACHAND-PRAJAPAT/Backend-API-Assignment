import json
import logging
import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger(__name__)

# --- Pydantic Schemas for Structured JSON Output ---
class CategoryMapping(BaseModel):
    idx: int
    category: str = Field(description="Must be one of: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, or Other")

class BatchCategorizationResponse(BaseModel):
    items: List[CategoryMapping]

class FinancialSummaryResponse(BaseModel):
    total_spend_by_currency: Dict[str, float] = Field(description="Total spending grouped by currency like INR and USD")
    top_3_merchants: List[str] = Field(description="Top 3 merchants by transaction count or spend amount")
    anomaly_count: int
    spending_narrative: str = Field(description="A clean 2-3 sentence overview of spending habits and concerns.")
    risk_level: str = Field(description="Must be exactly: low, medium, or high")


class LLMClient:
    def __init__(self):
        # Initialize the official Google Gen AI Client using the API key
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-1.5-flash"

    # Exponential Backoff Retry Strategy (up to 3 times)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_llm_with_retry(self, prompt: str, response_schema: Any) -> str:
        """Helper method to invoke Gemini with structured JSON outputs and retry logic."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1, # Low temperature for consistent classification
            ),
        )
        return response.text

    def batch_classify_categories(self, df: pd.DataFrame) -> Dict[int, str]:
        """
        Batches all 'Uncategorised' transactions into a single LLM prompt
        and returns a dictionary mapping original DataFrame index to assigned category.
        """
        # Find rows needing classification
        uncategorized_rows = df[df['category'] == 'Uncategorised']
        if uncategorized_rows.empty:
            return {}

        # Prepare a lightweight layout to send to the LLM to save token space
        batch_data = []
        for idx, row in uncategorized_rows.iterrows():
            batch_data.append({
                "idx": int(idx),
                "merchant": row['merchant'],
                "notes": row['notes'],
                "amount": float(row['amount']),
                "currency": row['currency']
            })

        prompt = f"""
        You are a financial data analyst. Classify the following transactions into exactly one of these categories:
        [Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other]

        Input Data:
        {json.dumps(batch_data, indent=2)}
        
        Return a structured JSON object containing a mapping for every single index provided.
        """

        try:
            raw_response = self._call_llm_with_retry(prompt, BatchCategorizationResponse)
            parsed = json.loads(raw_response)
            
            # Map index back to classification results
            return {item['idx']: item['category'] for item in parsed.get('items', [])}
            
        except Exception as e:
            logger.error(f"LLM Batch Classification failed after retries: {str(e)}")
            # Return empty map so worker can flag rows as llm_failed instead of crashing completely
            return {}

    def generate_narrative_summary(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Sends the entire cleaned dataset summary statistics to the LLM to generate
        a structured JSON narrative report.
        """
        if df.empty:
            return None

        # Prepare aggregate context data for the prompt
        total_anomalies = int(df['is_anomaly'].sum())
        sample_records = df[['date', 'merchant', 'amount', 'currency', 'category', 'is_anomaly', 'anomaly_reason']].to_dict(orient='records')

        prompt = f"""
        Analyze these processed financial transactions and generate a high-level narrative summary report.
        
        Metadata & Dataset Context:
        - Total Row Count: {len(df)}
        - Processed Flagged Anomalies Count: {total_anomalies}
        - Full Transaction list: {json.dumps(sample_records, indent=2)}

        Generate a single JSON object containing:
        1. total_spend_by_currency (calculated sum for INR and USD separately)
        2. top_3_merchants (by transaction frequency or total value)
        3. anomaly_count (total counts found)
        4. spending_narrative (2-3 sentences max summarizing patterns, velocity, or risk concerns)
        5. risk_level (evaluate based on anomalies: low/medium/high)
        """

        try:
            raw_response = self._call_llm_with_retry(prompt, FinancialSummaryResponse)
            return json.loads(raw_response)
        except Exception as e:
            logger.error(f"LLM Narrative Report generation failed after retries: {str(e)}")
            return None