"""
工艺参数优化分析工具集 — 供 Agent 通过 tool calling 调用。

注意：这些工具在服务端执行计算，Agent 只需要调用工具，不需要生成代码。
所有工具接受/返回 JSON 字符串，便于 Agent 解析和展示。
"""

import json
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("optagent.analysis")

# ── Optional scipy support ──────────────────────────────────────────────────
_HAS_SCIPY = False
try:
    from scipy import stats as sp_stats
    _HAS_SCIPY = True
except ImportError:
    pass


# ── Internal helpers ────────────────────────────────────────────────────────

def _parse_json(data_json: str) -> dict:
    """Parse JSON input, handling both string and dict."""
    if isinstance(data_json, dict):
        return data_json
    return json.loads(data_json)


def _data_to_arrays(data: dict, columns: list[str]) -> tuple[list[np.ndarray], int]:
    """Convert {columns, rows} format to list of numpy arrays."""
    col_map = {name: idx for idx, name in enumerate(data.get("columns", []))}
    rows = data.get("rows", [])
    arrays = []
    for col in columns:
        if col not in col_map:
            raise ValueError(f"Column '{col}' not found. Available: {list(col_map.keys())}")
        col_idx = col_map[col]
        arrays.append(np.array([r[col_idx] for r in rows], dtype=float))
    return arrays, len(rows)


def _data_to_matrix(data: dict) -> tuple[np.ndarray, list[str], int]:
    """Convert {columns, rows} to full matrix."""
    cols = data.get("columns", [])
    rows = data.get("rows", [])
    n = len(rows)
    m = len(cols)
    if n == 0 or m == 0:
        raise ValueError("Empty dataset")
    matrix = np.zeros((n, m))
    for i, row in enumerate(rows):
        for j in range(m):
            val = row[j] if j < len(row) else 0
            try:
                matrix[i, j] = float(val)
            except (ValueError, TypeError):
                matrix[i, j] = 0.0
    return matrix, cols, n


def _json_result(**kwargs) -> str:
    """Return JSON string result."""
    return json.dumps(kwargs, ensure_ascii=False, default=str)


# ── Tool 1: Correlation Analysis ────────────────────────────────────────────

def correlation_analysis(data_json: str, columns: Optional[list[str]] = None) -> str:
    """Compute Pearson correlation matrix.
    
    Args:
        data_json: JSON string with {columns: [str], rows: [[float]]}
        columns: Specific columns to analyze (default: all numeric columns)
    
    Returns:
        JSON with correlation_matrix, p_values, factor_pairs (if scipy available)
    """
    try:
        data = _parse_json(data_json)
        _, n = _data_to_arrays(data, data["columns"][:1])
        if n < 3:
            return _json_result(error="Need at least 3 data points for correlation analysis")
        
        matrix, cols, _ = _data_to_matrix(data)
        
        # Compute correlation matrix
        corr = np.corrcoef(matrix.T)
        
        # Round to 4 decimal places
        corr_rounded = np.round(corr, 4).tolist()
        
        result = {
            "factors": cols,
            "correlation_matrix": corr_rounded,
        }
        
        # Add p-values if scipy available
        if _HAS_SCIPY:
            p_vals = np.zeros_like(corr)
            for i in range(len(cols)):
                for j in range(len(cols)):
                    if i != j:
                        _, p = sp_stats.pearsonr(matrix[:, i], matrix[:, j])
                        p_vals[i, j] = p
            result["p_values"] = np.round(p_vals, 4).tolist()
        
        # Identify strongest correlations
        pairs = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                pairs.append({
                    "factor1": cols[i],
                    "factor2": cols[j],
                    "correlation": round(float(corr[i, j]), 4),
                    "strength": "strong" if abs(corr[i, j]) > 0.7 else
                                "moderate" if abs(corr[i, j]) > 0.4 else "weak",
                    "direction": "positive" if corr[i, j] > 0 else "negative",
                })
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        result["factor_pairs"] = pairs
        
        return _json_result(**result)
    
    except Exception as e:
        logger.exception("correlation_analysis failed")
        return _json_result(error=str(e))


# ── Tool 2: Factor Importance ───────────────────────────────────────────────

def factor_importance(data_json: str, target_column: str,
                      feature_columns: Optional[list[str]] = None) -> str:
    """Analyze factor importance using standardized regression coefficients.
    
    Args:
        data_json: JSON string with {columns: [str], rows: [[float]]}
        target_column: The response/outcome column name
        feature_columns: Factor columns to analyze (default: all except target)
    
    Returns:
        JSON with ranked factors, coefficients, and interpretation
    """
    try:
        data = _parse_json(data_json)
        cols = data.get("columns", [])
        
        if target_column not in cols:
            return _json_result(error=f"Target column '{target_column}' not found")
        
        all_cols = [c for c in cols if c != target_column]
        features = feature_columns if feature_columns else all_cols
        
        # Get data arrays
        matrix, _, n = _data_to_matrix(data)
        target_idx = cols.index(target_column)
        y = matrix[:, target_idx]
        
        # Build feature matrix (standardized)
        X = np.column_stack([
            (matrix[:, cols.index(f)] - np.mean(matrix[:, cols.index(f)])) /
            (np.std(matrix[:, cols.index(f)]) or 1)
            for f in features
        ])
        
        # Add constant term
        X = np.column_stack([np.ones(n), X])
        
        # OLS regression
        try:
            coeffs, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            return _json_result(error="Regression failed - check for collinear factors")
        
        # Build importance list
        importance = []
        for i, f in enumerate(features):
            importance.append({
                "factor": f,
                "standardized_coefficient": round(float(coeffs[i + 1]), 4),
                "absolute_importance": round(abs(float(coeffs[i + 1])), 4),
            })
        
        # Sort by absolute importance
        importance.sort(key=lambda x: x["absolute_importance"], reverse=True)
        
        # Calculate percentage
        total = sum(x["absolute_importance"] for x in importance) or 1
        for item in importance:
            item["importance_pct"] = round(item["absolute_importance"] / total * 100, 1)
        
        return _json_result(
            target=target_column,
            r_squared=round(1 - (residuals[0] / (n * np.var(y))) if (len(residuals) > 0 and n > 1 and np.var(y) > 0) else 0, 4),
            ranked_factors=importance,
            interpretation=f"Top factor: {importance[0]['factor']} ({importance[0]['importance_pct']}%)"
        )
    
    except Exception as e:
        logger.exception("factor_importance failed")
        return _json_result(error=str(e))


# ── Tool 3: DOE Design ─────────────────────────────────────────────────────

def design_experiment(factors: str, levels: str,
                      design_type: str = "full_factorial") -> str:
    """Generate a DOE design matrix.
    
    Args:
        factors: JSON string like '{"Temperature": [150, 170], "Pressure": [30, 50]}'
        levels: Comma-separated or JSON levels per factor
        design_type: "full_factorial" | "fractional_factorial" | "central_composite"
    
    Returns:
        JSON with design matrix as {columns, rows} and metadata
    """
    try:
        factor_dict = _parse_json(factors)
        factor_names = list(factor_dict.keys())
        factor_levels = [factor_dict[f] for f in factor_names]
        
        if design_type == "full_factorial":
            # All combinations
            from itertools import product
            combos = list(product(*factor_levels))
            rows = [list(c) + [0] for c in combos]  # placeholder for response
            columns = factor_names + ["response"]
            
            return _json_result(
                design_type="full_factorial",
                factors=factor_names,
                factor_levels={f: factor_dict[f] for f in factor_names},
                total_runs=len(combos),
                design_matrix={"columns": columns, "rows": rows},
                note="Fill in the 'response' column with experimental results"
            )
        
        elif design_type == "central_composite":
            # CCD: 2^k factorial + axial points + center points
            k = len(factor_names)
            if k < 2 or k > 6:
                return _json_result(error="CCD requires 2-6 factors")
            
            # Scale each factor to [-1, 1] centered
            centers = {}
            half_ranges = {}
            for f_name, vals in factor_dict.items():
                vals_f = [float(v) for v in vals]
                centers[f_name] = (max(vals_f) + min(vals_f)) / 2
                half_ranges[f_name] = (max(vals_f) - min(vals_f)) / 2
            
            alpha = 2 ** (k / 4)  # rotatability
            rows = []
            
            # Factorial points: 2^k
            for combo in product(*[[-1, 1] for _ in range(k)]):
                row = [centers[factor_names[i]] + combo[i] * half_ranges[factor_names[i]]
                       for i in range(k)]
                rows.append(row)
            
            # Axial points: 2k
            for i in range(k):
                for sign in [-alpha, alpha]:
                    row = [centers[j] + (sign * half_ranges[j] if j == i else 0)
                           for j in range(k)]
                    rows.append(row)
            
            # Center points: 3-5 replicates
            center = [centers[f] for f in factor_names]
            for _ in range(3):
                rows.append(center[:])
            
            columns = factor_names + ["response"]
            rows_with_resp = [r + [0] for r in rows]
            
            return _json_result(
                design_type="central_composite_design",
                factors=factor_names,
                alpha=round(alpha, 4),
                total_runs=len(rows_with_resp),
                design_matrix={"columns": columns, "rows": rows_with_resp},
                note="Fill response column with experimental results"
            )
        
        else:
            return _json_result(error=f"Unsupported design type: {design_type}")
    
    except Exception as e:
        logger.exception("design_experiment failed")
        return _json_result(error=str(e))


# ── Tool 4: Response Surface ────────────────────────────────────────────────

def response_surface(data_json: str, factors: list[str],
                     response_column: str) -> str:
    """Fit quadratic response surface model y = b0 + sum(bi*xi) + sum(bii*xi^2) + sum(bij*xi*xj).
    
    Args:
        data_json: JSON with {columns, rows}
        factors: List of factor column names
        response_column: Response/output column name
    
    Returns:
        JSON with model coefficients, optimal point, predicted optimum
    """
    try:
        data = _parse_json(data_json)
        cols = data.get("columns", [])
        
        if response_column not in cols:
            return _json_result(error=f"Response column '{response_column}' not found")
        for f in factors:
            if f not in cols:
                return _json_result(error=f"Factor '{f}' not found")
        
        k = len(factors)
        matrix, _, n = _data_to_matrix(data)
        if n < k + 2:
            return _json_result(error=f"Need at least {k+2} data points for {k} factors")
        
        # Extract data
        y = matrix[:, cols.index(response_column)]
        X_raw = np.column_stack([matrix[:, cols.index(f)] for f in factors])
        
        # Build quadratic model matrix: 1, x_i, x_i^2, x_i*x_j
        terms = ["const"] + factors + [f"{f}^2" for f in factors]
        for i in range(k):
            for j in range(i + 1, k):
                terms.append(f"{factors[i]}*{factors[j]}")
        
        # Normalize factors to [-1, 1] for numerical stability
        x_min = X_raw.min(axis=0)
        x_max = X_raw.max(axis=0)
        x_range = x_max - x_min
        x_range[x_range == 0] = 1
        X_norm = 2 * (X_raw - x_min) / x_range - 1
        
        # Design matrix
        X_des = np.ones((n, len(terms)))
        for i in range(k):
            X_des[:, 1 + i] = X_norm[:, i]  # x_i
            X_des[:, 1 + k + i] = X_norm[:, i] ** 2  # x_i^2
        idx = 1 + 2 * k
        for i in range(k):
            for j in range(i + 1, k):
                X_des[:, idx] = X_norm[:, i] * X_norm[:, j]
                idx += 1
        
        # Fit
        try:
            coeffs, residuals, rank, sv = np.linalg.lstsq(X_des, y, rcond=None)
        except np.linalg.LinAlgError:
            return _json_result(error="Model fitting failed")
        
        # Model quality
        y_pred = X_des @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2) if len(y) > 1 else 1
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        # Find optimal point (maximize)
        # For quadratic, use calculus
        if k <= 2:
            # For 1-2 factors, grid search on normalized [-1.5, 1.5]
            from itertools import product as iter_product
            best_y = -1e9
            best_x_norm = None
            for grid in iter_product(*[np.linspace(-1.5, 1.5, 50) for _ in range(k)]):
                grid_arr = np.array(grid)
                xv = np.ones(len(terms))
                for i in range(k):
                    xv[1 + i] = grid_arr[i]
                    xv[1 + k + i] = grid_arr[i] ** 2
                idx = 1 + 2 * k
                for i in range(k):
                    for j in range(i + 1, k):
                        xv[idx] = grid_arr[i] * grid_arr[j]
                        idx += 1
                pred = np.dot(xv, coeffs)
                if pred > best_y:
                    best_y = pred
                    best_x_norm = grid_arr
            
            # Convert back to original scale
            best_x_orig = [(best_x_norm[i] + 1) / 2 * x_range[i] + x_min[i]
                          if x_range[i] != 0 else x_min[i] for i in range(k)]
        else:
            best_x_orig = None
            best_y = float(np.max(y_pred))
        
        model_coeffs = {terms[i]: round(float(coeffs[i]), 4) for i in range(len(terms))}
        
        return _json_result(
            response=response_column,
            factors=factors,
            model_coefficients=model_coeffs,
            r_squared=round(float(r2), 4),
            sample_count=n,
            optimal_point={factors[i]: round(float(best_x_orig[i]), 2) for i in range(k)} if best_x_orig else None,
            predicted_optimum=round(float(best_y), 4),
        )
    
    except Exception as e:
        logger.exception("response_surface failed")
        return _json_result(error=str(e))


# ── Tool 5: Pareto Analysis ────────────────────────────────────────────────

def pareto_analysis(data_json: str, category_column: str,
                    value_column: str) -> str:
    """Compute Pareto analysis: sort by value, calculate cumulative %.
    
    Args:
        data_json: JSON with {columns, rows}
        category_column: Column with category names
        value_column: Column with numeric values
    
    Returns:
        JSON with sorted categories, values, cumulative %, vital few
    """
    try:
        data = _parse_json(data_json)
        cols = data.get("columns", [])
        
        if category_column not in cols or value_column not in cols:
            return _json_result(error="Category or value column not found")
        
        cat_idx = cols.index(category_column)
        val_idx = cols.index(value_column)
        rows = data.get("rows", [])
        
        # Aggregate by category
        agg: dict[str, float] = {}
        for row in rows:
            cat = str(row[cat_idx])
            val = float(row[val_idx]) if row[val_idx] not in (None, "") else 0
            agg[cat] = agg.get(cat, 0) + val
        
        # Sort descending
        sorted_items = sorted(agg.items(), key=lambda x: x[1], reverse=True)
        total = sum(v for _, v in sorted_items)
        
        cum_sum = 0.0
        items = []
        for cat, val in sorted_items:
            cum_sum += val
            items.append({
                "category": cat,
                "value": round(val, 4),
                "percentage": round(val / total * 100, 1) if total > 0 else 0,
                "cumulative_pct": round(cum_sum / total * 100, 1) if total > 0 else 0,
            })
        
        # Identify vital few (first items until cumulative > 80%)
        vital_few = []
        cum = 0
        for item in items:
            cum += item["percentage"]
            vital_few.append(item["category"])
            if cum >= 80:
                break
        
        return _json_result(
            total=round(total, 4),
            items=items,
            vital_few=vital_few,
            vital_few_count=len(vital_few),
            total_categories=len(items),
            interpretation=f"Top {len(vital_few)} of {len(items)} categories contribute 80%+ of total"
        )
    
    except Exception as e:
        logger.exception("pareto_analysis failed")
        return _json_result(error=str(e))


# ── Tool 6: ANOVA ──────────────────────────────────────────────────────────

def anova_one_way(data_json: str, factor_column: str,
                  response_column: str) -> str:
    """One-way ANOVA: test if different factor levels have different mean responses.
    
    Uses scipy if available, otherwise computes F-test manually.
    
    Args:
        data_json: JSON with {columns, rows}
        factor_column: Categorical factor column
        response_column: Numeric response column
    
    Returns:
        JSON with ANOVA table (SS, df, MS, F, p-value)
    """
    try:
        data = _parse_json(data_json)
        cols = data.get("columns", [])
        
        if factor_column not in cols or response_column not in cols:
            return _json_result(error="Factor or response column not found")
        
        fct_idx = cols.index(factor_column)
        resp_idx = cols.index(response_column)
        rows = data.get("rows", [])
        
        # Group by factor level
        groups: dict[str, list[float]] = {}
        for row in rows:
            level = str(row[fct_idx])
            val = float(row[resp_idx]) if row[resp_idx] not in (None, "") else 0
            if level not in groups:
                groups[level] = []
            groups[level].append(val)
        
        group_names = list(groups.keys())
        group_vals = [np.array(groups[g], dtype=float) for g in group_names]
        
        if len(group_names) < 2:
            return _json_result(error="Need at least 2 groups for ANOVA")
        
        # Use scipy if available
        if _HAS_SCIPY:
            f_stat, p_val = sp_stats.f_oneway(*group_vals)
            return _json_result(
                test="one-way ANOVA (scipy)",
                factor=factor_column,
                response=response_column,
                groups={g: {"count": len(groups[g]), "mean": round(float(np.mean(groups[g])), 4),
                           "std": round(float(np.std(groups[g], ddof=1)), 4)}
                       for g in group_names},
                f_statistic=round(float(f_stat), 4),
                p_value=round(float(p_val), 6),
                significant=bool(p_val < 0.05),
            )
        
        # Manual F-test
        all_data = np.concatenate(group_vals)
        grand_mean = np.mean(all_data)
        n = len(all_data)
        k = len(group_names)
        
        ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in group_vals)
        ss_within = sum(np.sum((g - np.mean(g)) ** 2) for g in group_vals)
        
        df_between = k - 1
        df_within = n - k
        ms_between = ss_between / df_between if df_between > 0 else 0
        ms_within = ss_within / df_within if df_within > 0 else 0
        f_stat = ms_between / ms_within if ms_within > 0 else 0
        
        # Approximate p-value using F-distribution (if scipy available)
        p_val = None
        if _HAS_SCIPY:
            p_val = round(float(1 - sp_stats.f.cdf(f_stat, df_between, df_within)), 6)
        
        return _json_result(
            test="one-way ANOVA (manual)",
            factor=factor_column,
            response=response_column,
            groups={g: {"count": len(groups[g]), "mean": round(float(np.mean(groups[g])), 4),
                       "std": round(float(np.std(groups[g], ddof=1)), 4)}
                   for g in group_names},
            anova_table={
                "source": ["between_groups", "within_groups", "total"],
                "ss": [round(float(ss_between), 4), round(float(ss_within), 4),
                       round(float(ss_between + ss_within), 4)],
                "df": [df_between, df_within, n - 1],
                "ms": [round(float(ms_between), 4), round(float(ms_within), 4), ""],
                "f": [round(float(f_stat), 4), "", ""],
                "p": [p_val, "", ""],
            },
            significant=bool(p_val < 0.05) if p_val is not None else None,
            note="Install scipy for accurate p-values" if p_val is None else "",
        )
    
    except Exception as e:
        logger.exception("anova_one_way failed")
        return _json_result(error=str(e))
