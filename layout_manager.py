import math

def auto_layout(total):
    """
    Dead space 최소화 + 정사각형에 가까운 자동 레이아웃
    """
    if total <= 0:
        return 1, 1

    cols = int(total ** 0.5)
    rows = cols

    if cols * rows < total:
        cols += 1
        if cols * rows < total:
            rows += 1

    return cols, rows
