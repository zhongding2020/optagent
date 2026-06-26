import re
from typing import Any, Optional
from fastapi import APIRouter

router = APIRouter(prefix="/api/sessions/{session_id}/data", tags=["data"])

_store = None


def init(store):
    global _store
    _store = store


@router.get("")
async def get_analysis_data(session_id: str):
    if not _store:
        return {"session_id": session_id, "data": {}}

    session = _store.get(session_id)
    if not session:
        return {"session_id": session_id, "error": "Session not found"}

    node_results = session.node_results or {}
    return {
        "session_id": session_id,
        "status": session.status,
        "current_node": session.current_node,
        "node_statuses": {
            k: v.model_dump() for k, v in session.node_statuses.items()
        },
        "data": _extract_analysis(node_results),
    }


def _extract_analysis(node_results: dict[str, Any]) -> dict:
    """Extract structured analysis data from raw node_results."""
    analysis: dict[str, Any] = {
        "factor_importance": [],
        "correlation": {"factors": [], "values": []},
        "pareto": {"categories": [], "values": [], "cumulative": []},
        "design_matrix": {"factors": [], "runs": []},
        "scatter": {"x": [], "y": []},
        "steps": {},
    }

    for node_id, result in node_results.items():
        summary = (result or {}).get("summary", "")
        if not summary:
            continue

        analysis["steps"][node_id] = {"summary": summary}

        # Try to extract numeric factor data from summary text
        factor_matches = re.findall(
            r'([\u4e00-\u9fff\w]+)[：:]\s*([\d.]+)%?', summary
        )
        if factor_matches and len(factor_matches) >= 2:
            factors = [{"name": m[0], "value": float(m[1])} for m in factor_matches]
            factors.sort(key=lambda x: x["value"], reverse=True)
            analysis["factor_importance"] = factors

            # Build pareto from same data
            total = sum(f["value"] for f in factors)
            cum_sum = 0.0
            pareto_cats = []
            pareto_vals = []
            pareto_cum = []
            for f in factors:
                pareto_cats.append(f["name"])
                pareto_vals.append(f["value"])
                cum_sum += f["value"]
                pareto_cum.append(round(cum_sum / total * 100, 1) if total > 0 else 0)
            analysis["pareto"] = {
                "categories": pareto_cats,
                "values": pareto_vals,
                "cumulative": pareto_cum,
            }

            # Build correlation matrix from factor names
            names = [f["name"] for f in factors]
            n = len(names)
            vals = [[1.0] * n for _ in range(n)]
            analysis["correlation"] = {"factors": names, "values": vals}

        # Try to extract DOE design matrix from design_doe step
        if node_id == "design_doe" or node_id == "collect_data":
            run_pattern = re.findall(
                r'(?:Run|试验|组|No)[\s#]*(\d+)[：:](.*?)(?=(?:Run|试验|组|No|\Z))',
                summary, re.DOTALL
            )
            if not run_pattern:
                # Try simpler pattern: numbers with potential factors
                numbers = re.findall(r'(\d+)', summary)
                if len(numbers) >= 4:
                    analysis["scatter"] = {
                        "x": [int(numbers[i]) for i in range(0, len(numbers), 2)],
                        "y": [int(numbers[i+1]) for i in range(0, len(numbers)-1, 2)],
                    }

    return analysis
