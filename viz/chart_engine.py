"""
SpeakSQL — Chart engine.
Auto-suggests chart types based on result shape and renders Plotly charts with dark theme.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Light theme template for Plotly ───────────────────────────────────────────
LIGHT_TEMPLATE = {
    "paper_bgcolor": "#FFFDF2",
    "plot_bgcolor": "#FFFFFF",
    "font": {"color": "#475569", "family": "Inter, sans-serif", "size": 13},
    "title": {"font": {"color": "#1E293B", "size": 16, "family": "Inter, sans-serif"}},
    "xaxis": {
        "gridcolor": "#E5E1D8", "linecolor": "#E5E1D8",
        "tickfont": {"color": "#64748B"}, "title": {"font": {"color": "#475569"}},
    },
    "yaxis": {
        "gridcolor": "#E5E1D8", "linecolor": "#E5E1D8",
        "tickfont": {"color": "#64748B"}, "title": {"font": {"color": "#475569"}},
    },
    "colorway": [
        "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#EF4444",
        "#EC4899", "#06B6D4", "#14B8A6", "#A855F7", "#F97316",
    ],
    "legend": {"font": {"color": "#475569"}, "bgcolor": "rgba(0,0,0,0)"},
}


def _apply_light_layout(fig):
    """Apply consistent light theme to a Plotly figure."""
    fig.update_layout(
        **LIGHT_TEMPLATE,
        margin=dict(l=40, r=40, t=50, b=40),
        hoverlabel=dict(bgcolor="#FFFFFF", font_color="#1E293B", bordercolor="#F59E0B"),
    )
    return fig


def suggest_chart_type(df: pd.DataFrame) -> list[str]:
    """
    Analyze result DataFrame and suggest appropriate chart types.

    Returns list of chart type strings: 'bar', 'line', 'scatter', 'pie', 'histogram', 'heatmap'.
    """
    if df is None or df.empty:
        return []

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = []

    # Detect date columns (string dates)
    for col in cat_cols[:]:
        try:
            sample = df[col].dropna().head(10)
            if len(sample) > 0:
                pd.to_datetime(sample, errors="raise")
                date_cols.append(col)
                cat_cols.remove(col)
        except (ValueError, TypeError):
            pass

    suggestions = []
    rows = len(df)

    # 1 categorical + 1 numeric → bar chart
    if len(cat_cols) >= 1 and len(num_cols) >= 1:
        suggestions.append("bar")
        if rows <= 10:
            suggestions.append("pie")

    # Date column + numeric → line chart
    if len(date_cols) >= 1 and len(num_cols) >= 1:
        suggestions.insert(0, "line")

    # 2+ numeric columns → scatter
    if len(num_cols) >= 2:
        suggestions.append("scatter")

    # Single numeric column → histogram
    if len(num_cols) >= 1 and len(cat_cols) == 0 and len(date_cols) == 0:
        suggestions.append("histogram")

    # Multiple numeric columns → heatmap (correlation)
    if len(num_cols) >= 3:
        suggestions.append("heatmap")

    # Deduplicate while preserving order
    seen = set()
    result = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            result.append(s)

    return result if result else ["bar"]


def render_chart(df: pd.DataFrame, chart_type: str, title: str = "") -> go.Figure | None:
    """
    Render a Plotly chart from the result DataFrame.

    Args:
        df: Result DataFrame
        chart_type: One of 'bar', 'line', 'scatter', 'pie', 'histogram', 'heatmap'
        title: Optional chart title

    Returns:
        Plotly Figure or None if chart can't be rendered
    """
    if df is None or df.empty:
        return None

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Detect date columns
    date_cols = []
    for col in cat_cols[:]:
        try:
            pd.to_datetime(df[col].dropna().head(10), errors="raise")
            date_cols.append(col)
            cat_cols.remove(col)
        except (ValueError, TypeError):
            pass

    fig = None

    try:
        if chart_type == "bar" and cat_cols and num_cols:
            x_col = cat_cols[0]
            y_col = num_cols[0]
            fig = px.bar(df, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}",
                         color_discrete_sequence=LIGHT_TEMPLATE["colorway"])

        elif chart_type == "line":
            x_col = date_cols[0] if date_cols else (cat_cols[0] if cat_cols else num_cols[0])
            y_col = num_cols[0] if num_cols else None
            if y_col:
                plot_df = df.copy()
                if x_col in date_cols:
                    plot_df[x_col] = pd.to_datetime(plot_df[x_col])
                    plot_df = plot_df.sort_values(x_col)
                fig = px.line(plot_df, x=x_col, y=y_col, title=title or f"{y_col} over {x_col}",
                              color_discrete_sequence=LIGHT_TEMPLATE["colorway"],
                              markers=True)

        elif chart_type == "scatter" and len(num_cols) >= 2:
            x_col, y_col = num_cols[0], num_cols[1]
            color_col = cat_cols[0] if cat_cols else None
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col,
                             title=title or f"{y_col} vs {x_col}",
                             color_discrete_sequence=LIGHT_TEMPLATE["colorway"])

        elif chart_type == "pie" and cat_cols and num_cols:
            fig = px.pie(df, names=cat_cols[0], values=num_cols[0],
                         title=title or f"{num_cols[0]} by {cat_cols[0]}",
                         color_discrete_sequence=LIGHT_TEMPLATE["colorway"],
                         hole=0.4)

        elif chart_type == "histogram" and num_cols:
            fig = px.histogram(df, x=num_cols[0], title=title or f"Distribution of {num_cols[0]}",
                               color_discrete_sequence=LIGHT_TEMPLATE["colorway"],
                               nbins=30)

        elif chart_type == "heatmap" and len(num_cols) >= 3:
            corr = df[num_cols].corr()
            fig = px.imshow(corr, title=title or "Correlation Heatmap",
                            color_continuous_scale="amp", text_auto=".2f",
                            aspect="auto")

        if fig:
            _apply_light_layout(fig)

    except Exception:
        return None

    return fig


def render_all_suggested_charts(df: pd.DataFrame) -> list[tuple[str, go.Figure]]:
    """
    Auto-suggest and render all applicable chart types.

    Returns list of (chart_type, figure) tuples.
    """
    suggestions = suggest_chart_type(df)
    charts = []
    for chart_type in suggestions[:3]:  # Max 3 charts
        fig = render_chart(df, chart_type)
        if fig:
            charts.append((chart_type, fig))
    return charts
