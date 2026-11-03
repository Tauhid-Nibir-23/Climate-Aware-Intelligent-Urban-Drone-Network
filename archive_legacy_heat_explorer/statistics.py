def summary_statistics(grid):
    values = grid["intensity"]
    return {"count": len(values), "mean": values.mean(), "minimum": values.min(), "maximum": values.max()}
