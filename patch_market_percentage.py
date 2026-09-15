"""
Fix percentage calculation in backend quote route and FlowMarketSelectionScreen.
"""
import re

# 1. Update backend/api/routes/markets.py
markets_route_path = "backend/api/routes/markets.py"
try:
    with open(markets_route_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure change_pct and change keys exist in quote dictionary
    if '"change_pct": change_pct' not in content:
        content = content.replace(
            '"raw_change": change_pct,',
            '"raw_change": change_pct,\n                "change_pct": change_pct,\n                "change": f"{"+" if change_pct >= 0 else \"\"}{change_pct:.2f}%",',
        )
        content = content.replace(
            '"raw_change": 0.0,',
            '"raw_change": 0.0,\n                "change_pct": 0.0,\n                "change": "+0.00%",',
        )
        with open(markets_route_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("[OK] backend/api/routes/markets.py updated with change_pct and change keys")
    else:
        print("[SKIP] backend/api/routes/markets.py already has change_pct")
except Exception as e:
    print(f"[ERR] Failed updating markets.py: {e}")

# 2. Update mobile/src/screens/flow/FlowMarketSelectionScreen.tsx
sel_path = "mobile/src/screens/flow/FlowMarketSelectionScreen.tsx"
try:
    with open(sel_path, "r", encoding="utf-8") as f:
        sel_content = f.read()

    # Make percentage retrieval fallback to raw_change if change_pct is missing
    sel_content = re.sub(
        r'activeQuote\?\.change_pct',
        r'(activeQuote?.change_pct ?? (activeQuote as any)?.raw_change ?? 0)',
        sel_content,
    )
    sel_content = re.sub(
        r'q\?\.change_pct != null \? `\$\{isUp \? \'\+\' : \'\'\}\$\{q\.change_pct\.toFixed\(2\)\}%` : \'0\.00%\'',
        r'`${(q?.change_pct ?? (q as any)?.raw_change ?? 0) >= 0 ? "+" : ""}${Number(q?.change_pct ?? (q as any)?.raw_change ?? 0).toFixed(2)}%`',
        sel_content,
    )
    with open(sel_path, "w", encoding="utf-8") as f:
        f.write(sel_content)
    print("[OK] FlowMarketSelectionScreen.tsx updated with resilient percentage parsing")
except Exception as e:
    print(f"[ERR] Failed updating FlowMarketSelectionScreen.tsx: {e}")
