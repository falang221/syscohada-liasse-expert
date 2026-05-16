import pandas as pd
from app.services.excel_parser import parse_balance_df

def test_parse_balance_df():
    data = {"compte": ["601", "701"], "debit": [100.0, 0.0], "credit": [0.0, 150.0]}
    df = pd.DataFrame(data)
    result = parse_balance_df(df)
    assert len(result) == 2
    assert result[0]["compte"] == "601"
    assert result[1]["credit"] == 150.0
