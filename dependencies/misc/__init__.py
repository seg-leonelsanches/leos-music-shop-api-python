def deep_dict(obj):
    if not hasattr(obj,"__dict__"):
        return obj
    result = {}
    for key, val in obj.__dict__.items():
        if key.startswith("_"):
            continue
        element = []
        if isinstance(val, list):
            for item in val:
                element.append(deep_dict(item))
        else:
            element = deep_dict(val)
        result[key] = element
    return result