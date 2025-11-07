"""
Chart generation utilities using DuckDB for high-performance data aggregation
Generates Plotly chart configurations
"""

import duckdb
import pandas as pd
from typing import Dict, List, Optional, Any
import uuid
import math


def _sanitize_col(col_name: str) -> str:
    """
    Sanitize column names to prevent SQL injection
    Use DuckDB double-quote protection
    """
    return f'"{col_name}"'


def _get_duckdb_connection(file_path: str) -> duckdb.DuckDBPyConnection:
    """
    Create DuckDB connection and load data file

    Args:
        file_path: Data file path (supports CSV, Parquet)

    Returns:
        DuckDB connection object
    """
    conn = duckdb.connect(':memory:')

    # Load data based on file type
    if file_path.endswith('.parquet'):
        conn.execute(f"CREATE TABLE data AS SELECT * FROM read_parquet('{file_path}')")
    elif file_path.endswith('.csv'):
        conn.execute(f"CREATE TABLE data AS SELECT * FROM read_csv_auto('{file_path}')")
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    return conn


def bar_chart_duckdb(
    file_path: str,
    category_col: str,
    value_col: str = 'count',
    agg: str = 'sum',
    top_k: int = 8,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate bar chart using DuckDB SQL aggregation
    Performance: 10-100x faster than Pandas

    Args:
        file_path: Data file path
        category_col: Category column name
        value_col: Value column name ('count' for row count)
        agg: Aggregation method (sum|count|mean|median)
        top_k: Show top K categories, merge others to 'Others'
        title: Chart title

    Returns:
        Dictionary with Plotly config and metadata
    """
    conn = _get_duckdb_connection(file_path)
    notes = []

    try:
        # 1. Build SQL aggregation query
        if value_col == 'count':
            value_expr = 'COUNT(*)'
        else:
            agg_func = agg.upper()
            value_expr = f"{agg_func}({_sanitize_col(value_col)})"

        sql = f"""
            SELECT
                {_sanitize_col(category_col)} AS category,
                {value_expr} AS value
            FROM data
            WHERE {_sanitize_col(category_col)} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT {top_k}
        """

        # 2. Execute query (DuckDB executes directly on files, extremely fast)
        agg_df = conn.sql(sql).to_df()

        # 3. Calculate 'Others' (optional)
        total_query = f"SELECT {value_expr} AS total FROM data WHERE {_sanitize_col(category_col)} IS NOT NULL"
        total_value = conn.sql(total_query).fetchone()[0]
        top_sum = float(agg_df['value'].sum())
        others_value = float(total_value) - top_sum

        # Robustness check: warn if Others ratio is too high
        if others_value > 0 and total_value > 0:
            others_ratio = others_value / total_value
            if others_ratio > 0.5:
                notes.append("Too many categories, Top-K chart may not be representative")

            # Add Others row
            others_df = pd.DataFrame([{'category': 'Others', 'value': others_value}])
            agg_df = pd.concat([agg_df, others_df], ignore_index=True)

        # 4. Build Plotly JSON
        trace = {
            "type": "bar",
            "x": agg_df['category'].tolist(),
            "y": agg_df['value'].tolist(),
            "marker": {"color": "#007aff"},
            "text": [f"{v:.2f}" for v in agg_df['value']],
            "textposition": "auto"
        }

        layout = {
            "title": title or f"{category_col} Distribution",
            "xaxis": {"title": category_col},
            "yaxis": {"title": f"{agg}({value_col})" if value_col != 'count' else "Count"},
            "template": "plotly_white"
        }

        # 5. Return result
        return {
            "chart_id": str(uuid.uuid4()),
            "chart_type": "bar",
            "data": [trace],
            "layout": layout,
            "meta": {
                "category_col": category_col,
                "value_col": value_col,
                "aggregation": agg,
                "top_k": top_k,
                "notes": notes
            },
            "summary": {
                "total_value": float(total_value),
                "top_value": float(agg_df['value'].max()),
                "categories_count": len(agg_df)
            }
        }

    finally:
        conn.close()


def timeseries_chart_duckdb(
    file_path: str,
    time_col: str,
    value_col: str = 'count',
    freq: str = 'D',
    agg: str = 'sum',
    group_by: Optional[str] = None,
    time_range: Optional[List[str]] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate timeseries chart using DuckDB aggregation

    Args:
        file_path: Data file path
        time_col: Time column name
        value_col: Value column name ('count' for row count)
        freq: Aggregation frequency (D=day, W=week, M=month)
        agg: Aggregation method (sum|count|mean|median)
        group_by: Group by column (optional, for multiple series)
        time_range: Time range [start, end] (optional)
        title: Chart title

    Returns:
        Dictionary with Plotly config and metadata
    """
    conn = _get_duckdb_connection(file_path)
    notes = []

    try:
        # Map frequency to DuckDB date_trunc
        freq_map = {'D': 'day', 'W': 'week', 'M': 'month'}
        trunc_unit = freq_map.get(freq, 'day')

        # Build value expression
        if value_col == 'count':
            value_expr = 'COUNT(*)'
        else:
            agg_func = agg.upper()
            value_expr = f"{agg_func}({_sanitize_col(value_col)})"

        # Build time filter condition
        where_clause = f"WHERE {_sanitize_col(time_col)} IS NOT NULL"
        if time_range and len(time_range) == 2:
            where_clause += f" AND {_sanitize_col(time_col)} BETWEEN '{time_range[0]}' AND '{time_range[1]}'"
            notes.append(f"Time range: {time_range[0]} to {time_range[1]}")

        # Build SQL
        if group_by:
            sql = f"""
                SELECT
                    date_trunc('{trunc_unit}', CAST({_sanitize_col(time_col)} AS TIMESTAMP)) AS time,
                    {_sanitize_col(group_by)} AS series,
                    {value_expr} AS value
                FROM data
                {where_clause}
                GROUP BY 1, 2
                ORDER BY 1, 2
            """
        else:
            sql = f"""
                SELECT
                    date_trunc('{trunc_unit}', CAST({_sanitize_col(time_col)} AS TIMESTAMP)) AS time,
                    {value_expr} AS value
                FROM data
                {where_clause}
                GROUP BY 1
                ORDER BY 1
            """

        # Execute query
        result_df = conn.sql(sql).to_df()

        # Return ISO 8601 format timestamp (avoid timezone issues)
        result_df['time'] = pd.to_datetime(result_df['time']).dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Build Plotly traces
        if group_by and 'series' in result_df.columns:
            traces = []
            for series_name in result_df['series'].unique():
                if pd.isna(series_name):
                    continue
                series_data = result_df[result_df['series'] == series_name]
                traces.append({
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": str(series_name),
                    "x": series_data['time'].tolist(),
                    "y": series_data['value'].tolist(),
                    "line": {"width": 2},
                    "marker": {"size": 4}
                })
        else:
            traces = [{
                "type": "scatter",
                "mode": "lines+markers",
                "name": value_col,
                "x": result_df['time'].tolist(),
                "y": result_df['value'].tolist(),
                "line": {"width": 2, "color": "#007aff"},
                "marker": {"size": 4}
            }]

        layout = {
            "title": title or f"{value_col} over time",
            "xaxis": {"title": "Date", "type": "date"},
            "yaxis": {"title": f"{agg}({value_col})" if value_col != 'count' else "Count"},
            "template": "plotly_white",
            "hovermode": "x unified"
        }

        # Calculate key metrics
        values = result_df['value'].values
        summary = {
            "max_value": float(values.max()) if len(values) > 0 else 0,
            "min_value": float(values.min()) if len(values) > 0 else 0,
            "mean_value": float(values.mean()) if len(values) > 0 else 0,
            "data_points": len(result_df)
        }

        # Calculate percent change (if enough data)
        if len(values) >= 2:
            pct_change = ((values[-1] - values[-2]) / values[-2] * 100) if values[-2] != 0 else 0
            summary["pct_change"] = float(pct_change)

        return {
            "chart_id": str(uuid.uuid4()),
            "chart_type": "timeseries",
            "data": traces,
            "layout": layout,
            "meta": {
                "time_col": time_col,
                "value_col": value_col,
                "freq": freq,
                "aggregation": agg,
                "group_by": group_by,
                "notes": notes
            },
            "summary": summary
        }

    finally:
        conn.close()


def pie_chart_duckdb(
    file_path: str,
    category_col: str,
    value_col: str = 'count',
    agg: str = 'sum',
    top_k: int = 8,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate pie chart (based on bar chart aggregation logic)

    Args:
        file_path: Data file path
        category_col: Category column name
        value_col: Value column name
        agg: Aggregation method
        top_k: Show top K categories
        title: Chart title

    Returns:
        Dictionary with Plotly config and metadata
    """
    conn = _get_duckdb_connection(file_path)
    notes = []

    try:
        # Build SQL
        if value_col == 'count':
            value_expr = 'COUNT(*)'
        else:
            agg_func = agg.upper()
            value_expr = f"{agg_func}({_sanitize_col(value_col)})"

        sql = f"""
            SELECT
                {_sanitize_col(category_col)} AS category,
                {value_expr} AS value
            FROM data
            WHERE {_sanitize_col(category_col)} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT {top_k}
        """

        agg_df = conn.sql(sql).to_df()

        # Calculate Others
        total_query = f"SELECT {value_expr} AS total FROM data WHERE {_sanitize_col(category_col)} IS NOT NULL"
        total_value = conn.sql(total_query).fetchone()[0]
        top_sum = float(agg_df['value'].sum())
        others_value = float(total_value) - top_sum

        if others_value > 0:
            others_df = pd.DataFrame([{'category': 'Others', 'value': others_value}])
            agg_df = pd.concat([agg_df, others_df], ignore_index=True)

            if others_value / total_value > 0.5:
                notes.append("Too many categories, consider using bar chart instead")

        # Build Plotly pie chart
        trace = {
            "type": "pie",
            "labels": agg_df['category'].tolist(),
            "values": agg_df['value'].tolist(),
            "textinfo": "label+percent",
            "hovertemplate": "<b>%{label}</b><br>Value: %{value}<br>Percent: %{percent}<extra></extra>"
        }

        layout = {
            "title": title or f"{category_col} Distribution",
            "template": "plotly_white"
        }

        return {
            "chart_id": str(uuid.uuid4()),
            "chart_type": "pie",
            "data": [trace],
            "layout": layout,
            "meta": {
                "category_col": category_col,
                "value_col": value_col,
                "aggregation": agg,
                "top_k": top_k,
                "notes": notes
            },
            "summary": {
                "total_value": float(total_value),
                "categories_count": len(agg_df)
            }
        }

    finally:
        conn.close()


def distribution_chart_duckdb(
    file_path: str,
    value_col: str,
    bins: Optional[int] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate distribution/histogram chart
    Use DuckDB for efficient binning

    Args:
        file_path: Data file path
        value_col: Value column name
        bins: Number of bins (auto-calculate if None)
        title: Chart title

    Returns:
        Dictionary with Plotly config and metadata
    """
    conn = _get_duckdb_connection(file_path)
    notes = []

    try:
        # Get basic statistics
        stats_sql = f"""
            SELECT
                MIN({_sanitize_col(value_col)}) as min_val,
                MAX({_sanitize_col(value_col)}) as max_val,
                AVG({_sanitize_col(value_col)}) as mean_val,
                MEDIAN({_sanitize_col(value_col)}) as median_val,
                STDDEV({_sanitize_col(value_col)}) as std_val,
                COUNT(*) as count_val
            FROM data
            WHERE {_sanitize_col(value_col)} IS NOT NULL
        """

        stats = conn.sql(stats_sql).fetchone()
        min_val, max_val, mean_val, median_val, std_val, count_val = stats

        # Auto-calculate bins (using Freedman-Diaconis rule)
        if bins is None:
            # IQR based bin width
            iqr_sql = f"""
                SELECT
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {_sanitize_col(value_col)}) -
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {_sanitize_col(value_col)}) as iqr
                FROM data
                WHERE {_sanitize_col(value_col)} IS NOT NULL
            """
            iqr = conn.sql(iqr_sql).fetchone()[0]

            if iqr > 0:
                bin_width = 2 * iqr / (count_val ** (1/3))
                bins = max(10, min(50, int((max_val - min_val) / bin_width)))
            else:
                bins = int(math.sqrt(count_val))

            notes.append(f"Auto-calculated bins: {bins}")

        # Build histogram SQL
        bin_width = (max_val - min_val) / bins
        hist_sql = f"""
            SELECT
                FLOOR(({_sanitize_col(value_col)} - {min_val}) / {bin_width}) * {bin_width} + {min_val} as bin_start,
                COUNT(*) as count
            FROM data
            WHERE {_sanitize_col(value_col)} IS NOT NULL
            GROUP BY 1
            ORDER BY 1
        """

        hist_df = conn.sql(hist_sql).to_df()

        # Build Plotly histogram
        trace = {
            "type": "bar",
            "x": hist_df['bin_start'].tolist(),
            "y": hist_df['count'].tolist(),
            "marker": {"color": "#007aff"},
            "name": "Frequency"
        }

        # Add mean and median lines
        shapes = [
            {
                "type": "line",
                "x0": mean_val, "x1": mean_val,
                "y0": 0, "y1": 1,
                "yref": "paper",
                "line": {"color": "red", "width": 2, "dash": "dash"},
                "name": "Mean"
            },
            {
                "type": "line",
                "x0": median_val, "x1": median_val,
                "y0": 0, "y1": 1,
                "yref": "paper",
                "line": {"color": "green", "width": 2, "dash": "dash"},
                "name": "Median"
            }
        ]

        layout = {
            "title": title or f"Distribution of {value_col}",
            "xaxis": {"title": value_col},
            "yaxis": {"title": "Frequency"},
            "template": "plotly_white",
            "shapes": shapes
        }

        return {
            "chart_id": str(uuid.uuid4()),
            "chart_type": "distribution",
            "data": [trace],
            "layout": layout,
            "meta": {
                "value_col": value_col,
                "bins": bins,
                "notes": notes
            },
            "summary": {
                "min": float(min_val),
                "max": float(max_val),
                "mean": float(mean_val),
                "median": float(median_val),
                "std": float(std_val),
                "count": int(count_val)
            }
        }

    finally:
        conn.close()


def heatmap_chart_duckdb(
    file_path: str,
    columns: Optional[List[str]] = None,
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate correlation matrix heatmap

    Args:
        file_path: Data file path
        columns: List of numeric columns to analyze (auto-select all numeric if None)
        title: Chart title

    Returns:
        Dictionary with Plotly config and metadata
    """
    conn = _get_duckdb_connection(file_path)
    notes = []

    try:
        # If columns not specified, auto-select numeric columns
        if columns is None:
            schema_sql = "DESCRIBE data"
            schema_df = conn.sql(schema_sql).to_df()
            numeric_types = ['INTEGER', 'BIGINT', 'DOUBLE', 'DECIMAL', 'FLOAT', 'HUGEINT']
            columns = schema_df[schema_df['column_type'].str.upper().isin(numeric_types)]['column_name'].tolist()
            notes.append(f"Auto-selected {len(columns)} numeric columns")

        if len(columns) < 2:
            raise ValueError("At least 2 numeric columns required for correlation matrix")

        if len(columns) > 20:
            notes.append("Too many columns, consider dimensionality reduction or select key columns")
            columns = columns[:20]

        # Read data and calculate correlation matrix (using pandas corr method)
        select_cols = ", ".join([_sanitize_col(col) for col in columns])
        data_sql = f"SELECT {select_cols} FROM data"
        df = conn.sql(data_sql).to_df()

        # Calculate correlation matrix
        corr_matrix = df.corr()

        # Build Plotly heatmap
        trace = {
            "type": "heatmap",
            "z": corr_matrix.values.tolist(),
            "x": corr_matrix.columns.tolist(),
            "y": corr_matrix.index.tolist(),
            "colorscale": "RdBu",
            "zmid": 0,
            "zmin": -1,
            "zmax": 1,
            "text": [[f"{val:.2f}" for val in row] for row in corr_matrix.values],
            "texttemplate": "%{text}",
            "textfont": {"size": 10},
            "hovertemplate": "X: %{x}<br>Y: %{y}<br>Correlation: %{z:.3f}<extra></extra>"
        }

        layout = {
            "title": title or "Correlation Matrix",
            "xaxis": {"title": "", "side": "bottom"},
            "yaxis": {"title": ""},
            "template": "plotly_white",
            "width": 600 + len(columns) * 30,
            "height": 600 + len(columns) * 30
        }

        # Find strongest correlations (excluding diagonal)
        corr_values = []
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                corr_values.append({
                    "col1": columns[i],
                    "col2": columns[j],
                    "correlation": float(corr_matrix.iloc[i, j])
                })

        corr_values.sort(key=lambda x: abs(x['correlation']), reverse=True)
        top_correlations = corr_values[:5]

        return {
            "chart_id": str(uuid.uuid4()),
            "chart_type": "heatmap",
            "data": [trace],
            "layout": layout,
            "meta": {
                "columns": columns,
                "notes": notes
            },
            "summary": {
                "columns_count": len(columns),
                "top_correlations": top_correlations
            }
        }

    finally:
        conn.close()


def generate_chart(
    file_path: str,
    chart_type: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Unified chart generation entry point

    Args:
        file_path: Data file path
        chart_type: Chart type (bar|timeseries|pie|distribution|heatmap)
        **kwargs: Chart-specific parameters

    Returns:
        Chart configuration dictionary
    """
    chart_generators = {
        'bar': bar_chart_duckdb,
        'timeseries': timeseries_chart_duckdb,
        'pie': pie_chart_duckdb,
        'distribution': distribution_chart_duckdb,
        'heatmap': heatmap_chart_duckdb
    }

    if chart_type not in chart_generators:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    generator = chart_generators[chart_type]
    return generator(file_path, **kwargs)
