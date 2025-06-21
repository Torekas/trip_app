import io
import pandas as pd
import pytest
from items.routes import upload  # if refactored into util

def test_parse_excel(tmp_path, client, auth_headers):
    # create a dummy Excel file
    df = pd.DataFrame({
        "category": ["A", "B"],
        "item_name": ["foo", "bar"],
        "quantity": [1, 2]
    })
    path = tmp_path / "test.xlsx"
    df.to_excel(path, index=False)
    with open(path, "rb") as f:
        resp = client.post("/upload",
            data={"file": (io.BytesIO(f.read()), "test.xlsx")},
            headers=auth_headers,
            follow_redirects=True)
    assert b"Excel data imported" in resp.data
