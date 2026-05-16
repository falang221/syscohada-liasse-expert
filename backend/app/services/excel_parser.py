import pandas as pd
from typing import List, Dict

def parse_balance_df(df: pd.DataFrame) -> List[Dict]:
    """
    Converts a pandas DataFrame (Balance) to a list of dictionaries.
    In the future, this will include validation and SYSCOHADA mapping logic.
    """
    return df.to_dict(orient="records")
