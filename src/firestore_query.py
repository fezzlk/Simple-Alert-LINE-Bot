from typing import Any, Dict, List, Tuple


def build_filters(query: Dict[str, Any]) -> List[Tuple[str, str, Any]]:
    if not query:
        return []

    filters: List[Tuple[str, str, Any]] = []

    def add_from_dict(item: Dict[str, Any]) -> None:
        for key, value in item.items():
            if key == '$and':
                for child in value:
                    add_from_dict(child)
            elif key == '$or':
                keys = []
                values = []
                for child in value:
                    if not isinstance(child, dict) or len(child) != 1:
                        raise ValueError('Unsupported OR query structure')
                    child_key = list(child.keys())[0]
                    keys.append(child_key)
                    values.append(child[child_key])
                if len(set(keys)) != 1:
                    raise ValueError('OR queries must target a single field')
                values = [v for v in values if v not in (None, '')]
                filters.append((keys[0], 'in', values))
            elif key.endswith('__in'):
                values = [v for v in value if v not in (None, '')] if isinstance(value, list) else value
                filters.append((key[:-4], 'in', values))
            else:
                filters.append((key, '==', value))

    add_from_dict(query)
    return filters
