from typing import Any, List, Dict

def is_sql_like(data: Any) -> bool:
    """
    JSON is considered SQL-like if:
      - it is a list
      - every element is a dict
      - keys match across all rows (consistent schema)
      - values are primitives (str, int, float, bool, None)
    """


    if not isinstance(data, list):
        return False

    if len(data) == 0:
        return False


    if not all(isinstance(item, dict) for item in data):
        return False

    base_keys = set(data[0].keys())

    for item in data:
        if set(item.keys()) != base_keys:
            return False

        for v in item.values():
            if isinstance(v, (dict, list)):
                return False

    return True
