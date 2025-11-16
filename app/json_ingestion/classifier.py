from typing import Any, List, Dict

def is_sql_like(data: Any) -> bool:
    """
    JSON is considered SQL-like if:
      - it is a list
      - every element is a dict
      - keys match across all rows (consistent schema)
      - values are primitives (str, int, float, bool, None)
    """

    # Must be a list
    if not isinstance(data, list):
        return False

    if len(data) == 0:
        return False

    # Must be list of dicts
    if not all(isinstance(item, dict) for item in data):
        return False

    # Keys must match (consistent schema)
    base_keys = set(data[0].keys())

    for item in data:
        if set(item.keys()) != base_keys:
            return False

        # No nested dicts/lists allowed inside values
        for v in item.values():
            if isinstance(v, (dict, list)):
                return False

    return True
