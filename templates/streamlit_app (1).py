from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# ShopScope | E-Commerce Customer Behaviour Analytics
# Place this file beside sample_data.csv and run:
#     streamlit run streamlit_app.py
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="ShopScope | Commerce Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Visual system ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #0b1020; color: #edf2ff; }
    [data-testid="stHeader"] { background: rgba(11,16,32,0.92); }
    [data-testid="stSidebar"] { background: #10182b; border-right: 1px solid #25314a; }
    [data-testid="stSidebar"] * { color: #dce6fa; }
    .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1500px; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -0.04em; }
    h1 { color: #f4f7ff; font-weight: 800 !important; }
    h2, h3 { color: #e8efff; }
    p, label, .stMarkdown { color: #c4cee2; }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #17233b, #121c31);
        border: 1px solid #2a3a58; border-radius: 16px;
        padding: 17px 19px; min-height: 118px;
    }
    div[data-testid="stMetricLabel"] { color: #9eacc7; font-size: 0.82rem; }
    div[data-testid="stMetricValue"] { color: #f4f7ff; font-family: 'Manrope'; font-weight: 800; }
    div[data-testid="stMetricDelta"] { font-size: 0.78rem; }
    .hero {
        background: radial-gradient(circle at 85% 10%, rgba(52,211,191,.20), transparent 30%),
                    linear-gradient(120deg, #172744 0%, #17203b 55%, #211d46 100%);
        border: 1px solid #344768; border-radius: 22px; padding: 27px 30px;
        margin-bottom: 22px;
    }
    .eyebrow { color: #62e3d0; text-transform: uppercase; letter-spacing: .16em;
               font-size: .72rem; font-weight: 700; }
    .hero-title { font-family: 'Manrope'; font-size: 2.15rem; font-weight: 800;
                  color: #fff; letter-spacing: -.055em; margin: 5px 0 4px; }
    .hero-sub { color: #b8c7df; font-size: .98rem; margin: 0; }
    .section-kicker { color: #6ee7d8; text-transform: uppercase; letter-spacing: .13em;
                      font-size: .70rem; font-weight: 700; margin-bottom: 3px; }
    .panel {
        background: #121d32; border: 1px solid #263652; border-radius: 16px;
        padding: 17px 19px; margin-bottom: 12px;
    }
    .panel-title { color: #edf3ff; font-weight: 700; font-family: 'Manrope'; font-size: 1rem; }
    .muted { color: #91a1bd; font-size: .83rem; }
    .insight {
        background: #142b36; border: 1px solid #245466; border-left: 4px solid #42d6c2;
        padding: 13px 16px; border-radius: 10px; margin: 8px 0;
        color: #d9f7f2;
    }
    .warning {
        background: #302719; border: 1px solid #68502c; border-left: 4px solid #f2b85b;
        padding: 13px 16px; border-radius: 10px; margin: 8px 0; color: #ffedc8;
    }
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px; border: 1px solid #3a5678; background: #203957;
        color: white; font-weight: 700;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #5ce0cf; color: #70eadb;
    }
    [data-testid="stDataFrame"] { border: 1px solid #2a3a58; border-radius: 12px; }
    [data-baseweb="select"] > div, [data-baseweb="input"] > div {
        background: #17233b; border-color: #344663; border-radius: 9px;
    }
    hr { border-color: #263652; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data loading and schema handling ----------
DATA_PATH = Path(__file__).parent / "sample_data.csv"

ALIASES = {
    "customer": ["customer_name", "customer", "customer_id", "user_id", "visitor_id"],
    "product": ["product", "r.product", "product_name", "item", "item_id", "product_id"],
    "category": ["category", "r.category", "product_category", "category_name"],
    "quantity": ["quantity", "r.quantity", "qty", "units"],
    "unit_price": ["unit_price", "r.unit_price", "price", "product_price"],
    "revenue": ["total", "r.total", "total_price", "revenue", "sales", "amount", "order_value"],
    "region": ["region", "country", "city", "location", "state"],
    "date": ["order_date", "date", "timestamp", "event_time", "created_at", "purchase_date"],
    "order": ["order_id", "transaction_id", "invoice_id", "order"],
}

def clean_col(name: object) -> str:
    return re.sub(r"\s+", "_", str(name).strip().lower())

def find_col(df: pd.DataFrame, key: str) -> Optional[str]:
    cols = {clean_col(c): c for c in df.columns}
    for alias in ALIASES[key]:
        if clean_col(alias) in cols:
            return cols[clean_col(alias)]
    return None

@st.cache_data(show_spinner=False)
def read_csv_file(path: str, modified: float) -> pd.DataFrame:
    # The modified timestamp is part of the cache key so changed CSVs reload.
    return pd.read_csv(path)

def load_data() -> tuple[pd.DataFrame, str]:
    if DATA_PATH.exists():
        try:
            return read_csv_file(str(DATA_PATH), DATA_PATH.stat().st_mtime), "sample_data.csv"
        except Exception as exc:
            return pd.DataFrame(), f"Could not read sample_data.csv: {exc}"
    return pd.DataFrame(), "sample_data.csv was not found beside streamlit_app.py"

def prepare_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    df.columns = [clean_col(c) for c in df.columns]
    found = {key: find_col(df, key) for key in ALIASES}

    # Numeric conversion for known numeric fields.
    for key in ("quantity", "unit_price", "revenue"):
        col = found[key]
        if col:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[$,₹]", "", regex=True),
                errors="coerce",
            )

    # If total/revenue is absent, calculate it when possible.
    if not found["revenue"] and found["quantity"] and found["unit_price"]:
        df["calculated_revenue"] = df[found["quantity"]] * df[found["unit_price"]]
        found["revenue"] = "calculated_revenue"

    if found["date"]:
        df[found["date"]] = pd.to_datetime(df[found["date"]], errors="coerce", dayfirst=True)

    # Keep source names for display and use normalized names internally.
    return df, found

def money(value: float) -> str:
    if pd.isna(value):
        value = 0
    if abs(value) >= 10_000_000:
        return f"₹{value/10_000_000:,.2f}Cr"
    if abs(value) >= 100_000:
        return f"₹{value/100_000:,.2f}L"
    if abs(value) >= 1_000:
        return f"₹{value/1_000:,.1f}K"
    return f"₹{value:,.0f}"

def chart_layout(fig, height=330):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c5d1e7", family="DM Sans"),
        margin=dict(l=8, r=8, t=28, b=8),
        legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor="#263652", zerolinecolor="#263652"),
        yaxis=dict(gridcolor="#263652", zerolinecolor="#263652"),
        hoverlabel=dict(bgcolor="#17233b", font_color="#f4f7ff"),
    )
    return fig

# ---------- Header ----------
raw_df, data_status = load_data()
if raw_df.empty:
    st.markdown(
        '<div class="hero"><div class="eyebrow">Commerce intelligence platform</div>'
        '<div class="hero-title">ShopScope</div><p class="hero-sub">Understand customers. '
        'Discover products. Make smarter decisions.</p></div>', unsafe_allow_html=True
    )
    st.error(data_status)
    st.info("Place your sample_data.csv in the same folder as streamlit_app.py, then refresh this page.")
    st.stop()

df, cols = prepare_data(raw_df)

st.markdown(
    '<div class="hero"><div class="eyebrow">Commerce intelligence platform&nbsp; / &nbsp;Live dataset</div>'
    '<div class="hero-title">ShopScope<span style="color:#62e3d0">.</span></div>'
    '<p class="hero-sub">A clearer view of your sales, customers and product performance.</p></div>',
    unsafe_allow_html=True,
)

# ---------- Sidebar controls ----------
with st.sidebar:
    st.markdown("## 🛍️ ShopScope")
    st.caption("E-COMMERCE INTELLIGENCE")
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Customer Insights", "Product Performance", "Explore Data"],
        label_visibility="visible",
    )
    st.divider()
    st.markdown("### Refine your view")

    filtered = df.copy()
    date_col = cols["date"]
    if date_col and pd.api.types.is_datetime64_any_dtype(filtered[date_col]):
        valid_dates = filtered[date_col].dropna()
        if not valid_dates.empty:
            min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
            selected_dates = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start, end = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                filtered = filtered[filtered[date_col].between(start, end)]

    for key, label in [("category", "Category"), ("region", "Region")]:
        col = cols[key]
        if col and filtered[col].notna().any():
            options = sorted(filtered[col].dropna().astype(str).unique().tolist())
            chosen = st.multiselect(f"{label}", options, default=options)
            filtered = filtered[filtered[col].astype(str).isin(chosen)]

    st.divider()
    st.caption(f"Source: {data_status}")
    st.caption(f"{len(filtered):,} of {len(df):,} records selected")

# ---------- Common metrics ----------
revenue_col, qty_col = cols["revenue"], cols["quantity"]
customer_col, product_col = cols["customer"], cols["product"]
category_col, region_col = cols["category"], cols["region"]
order_col = cols["order"]

revenue = float(filtered[revenue_col].fillna(0).sum()) if revenue_col else 0.0
orders = int(filtered[order_col].nunique()) if order_col else len(filtered)
customers = int(filtered[customer_col].nunique()) if customer_col else 0
units = float(filtered[qty_col].fillna(0).sum()) if qty_col else 0.0
avg_order = revenue / orders if orders else 0.0

def show_metrics():
    a, b, c, d, e = st.columns(5)
    a.metric("Total Revenue", money(revenue) if revenue_col else "—")
    b.metric("Orders / Records", f"{orders:,}")
    c.metric("Customers", f"{customers:,}" if customer_col else "—")
    d.metric("Units Sold", f"{units:,.0f}" if qty_col else "—")
    e.metric("Avg. Order Value", money(avg_order) if revenue_col else "—")

def section(label: str, title: str):
    st.markdown(f'<div class="section-kicker">{label}</div><h2>{title}</h2>', unsafe_allow_html=True)

def empty_note(message: str):
    st.info(message)

# ---------- Overview ----------
if page == "Overview":
    section("01 / Executive snapshot", "Your business at a glance")
    show_metrics()
    st.write("")
    left, right = st.columns([1.55, 1])
    with left:
        st.markdown('<div class="panel-title">Revenue movement</div>', unsafe_allow_html=True)
        if revenue_col and date_col:
            trend = filtered.dropna(subset=[date_col]).copy()
            if not trend.empty:
                trend["Period"] = trend[date_col].dt.to_period("M").astype(str)
                series = trend.groupby("Period", as_index=False)[revenue_col].sum()
                fig = px.area(series, x="Period", y=revenue_col, markers=True)
                fig.update_traces(line_color="#55d9c8", fillcolor="rgba(85,217,200,.13)", marker=dict(size=6))
                st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
            else:
                empty_note("No valid dates were found in the selected data.")
        elif revenue_col:
            if category_col:
                series = filtered.groupby(category_col, as_index=False)[revenue_col].sum().sort_values(revenue_col, ascending=False).head(12)
                fig = px.bar(series, x=category_col, y=revenue_col, color=revenue_col, color_continuous_scale=["#263b59", "#56ddca"])
                st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
            else:
                empty_note("Add an order date or category column to see a revenue trend.")
        else:
            empty_note("A revenue/total/amount column is needed for sales charts.")
    with right:
        st.markdown('<div class="panel-title">Revenue mix</div>', unsafe_allow_html=True)
        if revenue_col and category_col:
            mix = filtered.groupby(category_col, as_index=False)[revenue_col].sum().sort_values(revenue_col, ascending=False)
            fig = px.pie(mix, names=category_col, values=revenue_col, hole=.68,
                         color_discrete_sequence=["#55d9c8", "#8d83ff", "#f5b95c", "#5798ef", "#e27db5"])
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
        elif region_col and revenue_col:
            mix = filtered.groupby(region_col, as_index=False)[revenue_col].sum().sort_values(revenue_col, ascending=False)
            fig = px.pie(mix, names=region_col, values=revenue_col, hole=.68)
            st.plotly_chart(chart_layout(fig, 350), use_container_width=True)
        else:
            empty_note("Category or region data will unlock revenue mix.")
    st.write("")
    section("02 / Performance leaders", "What is driving the numbers?")
    x1, x2 = st.columns(2)
    with x1:
        if product_col and revenue_col:
            top = filtered.groupby(product_col, as_index=False)[revenue_col].sum().nlargest(8, revenue_col)
            fig = px.bar(top.sort_values(revenue_col), x=revenue_col, y=product_col, orientation="h",
                         color_discrete_sequence=["#55d9c8"])
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
        else:
            empty_note("Product and revenue columns are needed for top products.")
    with x2:
        if region_col and revenue_col:
            reg = filtered.groupby(region_col, as_index=False)[revenue_col].sum().nlargest(8, revenue_col)
            fig = px.bar(reg, x=region_col, y=revenue_col, color_discrete_sequence=["#8d83ff"])
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
        elif qty_col and category_col:
            cat = filtered.groupby(category_col, as_index=False)[qty_col].sum().nlargest(8, qty_col)
            fig = px.bar(cat, x=category_col, y=qty_col, color_discrete_sequence=["#8d83ff"])
            st.plotly_chart(chart_layout(fig, 330), use_container_width=True)
        else:
            empty_note("Region or category and quantity columns are needed for this chart.")
    if revenue_col and not filtered.empty:
        best_line = ""
        if category_col:
            s = filtered.groupby(category_col)[revenue_col].sum()
            if not s.empty:
                best_line = f"**{s.idxmax()}** is the leading category by revenue ({money(float(s.max()))})."
        elif product_col:
            s = filtered.groupby(product_col)[revenue_col].sum()
            if not s.empty:
                best_line = f"**{s.idxmax()}** is the top product by revenue ({money(float(s.max()))})."
        if best_line:
            st.markdown(f'<div class="insight">✦ Business signal&nbsp; {best_line}</div>', unsafe_allow_html=True)

# ---------- Customer insights ----------
elif page == "Customer Insights":
    section("03 / Customer intelligence", "Know who is buying")
    if not customer_col:
        st.warning("Your CSV does not contain a recognised customer column (for example customer_name or customer_id).")
    else:
        show_metrics()
        customer_summary = filtered.groupby(customer_col, dropna=False).agg(
            Transactions=(customer_col, "size"),
        ).reset_index()
        if revenue_col:
            rev = filtered.groupby(customer_col, dropna=False)[revenue_col].sum().reset_index(name="Revenue")
            customer_summary = customer_summary.merge(rev, on=customer_col, how="left")
        if qty_col:
            q = filtered.groupby(customer_col, dropna=False)[qty_col].sum().reset_index(name="Units")
            customer_summary = customer_summary.merge(q, on=customer_col, how="left")
        customer_summary = customer_summary.sort_values("Revenue" if "Revenue" in customer_summary else "Transactions", ascending=False)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="panel-title">Most valuable customers</div>', unsafe_allow_html=True)
            if "Revenue" in customer_summary:
                topc = customer_summary.head(10).sort_values("Revenue")
                fig = px.bar(topc, x="Revenue", y=customer_col, orientation="h", color_discrete_sequence=["#55d9c8"])
                st.plotly_chart(chart_layout(fig, 360), use_container_width=True)
            else:
                st.dataframe(customer_summary.head(10), use_container_width=True, hide_index=True)
        with c2:
            st.markdown('<div class="panel-title">Purchase frequency</div>', unsafe_allow_html=True)
            freq = customer_summary["Transactions"].value_counts().sort_index().reset_index()
            freq.columns = ["Transactions per customer", "Number of customers"]
            fig = px.bar(freq, x="Transactions per customer", y="Number of customers",
                         color_discrete_sequence=["#8d83ff"])
            st.plotly_chart(chart_layout(fig, 360), use_container_width=True)
        st.markdown("#### Customer leaderboard")
        st.dataframe(customer_summary.head(100), use_container_width=True, hide_index=True)
        if len(customer_summary):
            repeat = int((customer_summary["Transactions"] > 1).sum())
            repeat_rate = repeat / len(customer_summary) * 100
            st.markdown(f'<div class="insight">✦ {repeat_rate:.1f}% of identified customers have more than one record in this dataset. This is a record-frequency proxy, not a verified repeat-purchase rate unless each row represents a transaction.</div>', unsafe_allow_html=True)

# ---------- Product performance ----------
elif page == "Product Performance":
    section("04 / Product intelligence", "Find your winning products")
    if not product_col:
        st.warning("Your CSV does not contain a recognised product column (for example product or product_id).")
    else:
        show_metrics()
        if revenue_col:
            product_summary = filtered.groupby(product_col, as_index=False)[revenue_col].sum().sort_values(revenue_col, ascending=False)
            best, low = st.columns(2)
            with best:
                st.markdown('<div class="panel-title">Top products by revenue</div>', unsafe_allow_html=True)
                fig = px.bar(product_summary.head(10).sort_values(revenue_col), x=revenue_col, y=product_col,
                             orientation="h", color_discrete_sequence=["#55d9c8"])
                st.plotly_chart(chart_layout(fig, 390), use_container_width=True)
            with low:
                st.markdown('<div class="panel-title">Products needing attention</div>', unsafe_allow_html=True)
                bottom = product_summary.tail(10)
                fig = px.bar(bottom, x=revenue_col, y=product_col, orientation="h",
                             color_discrete_sequence=["#f0ad68"])
                st.plotly_chart(chart_layout(fig, 390), use_container_width=True)
            st.markdown("#### Product revenue table")
            st.dataframe(product_summary, use_container_width=True, hide_index=True)
        if category_col and qty_col:
            st.markdown("#### Category demand")
            demand = filtered.groupby(category_col, as_index=False)[qty_col].sum().sort_values(qty_col, ascending=False)
            fig = px.bar(demand, x=category_col, y=qty_col, color_discrete_sequence=["#8d83ff"])
            st.plotly_chart(chart_layout(fig, 320), use_container_width=True)
        if cols["unit_price"] and qty_col:
            st.markdown("#### Price versus units sold")
            fig = px.scatter(filtered, x=cols["unit_price"], y=qty_col,
                             color=category_col if category_col else None,
                             hover_name=product_col if product_col else None,
                             opacity=.72)
            st.plotly_chart(chart_layout(fig, 350), use_container_width=True)

# ---------- Data explorer ----------
elif page == "Explore Data":
    section("05 / Data workspace", "Explore the underlying records")
    show_metrics()
    st.write("")
    st.markdown("#### Dataset health")
    h1, h2, h3 = st.columns(3)
    h1.metric("Rows", f"{len(filtered):,}")
    h2.metric("Columns", f"{filtered.shape[1]:,}")
    h3.metric("Missing cells", f"{int(filtered.isna().sum().sum()):,}")
    with st.expander("Column quality report", expanded=False):
        quality = pd.DataFrame({
            "Column": filtered.columns,
            "Data type": [str(filtered[c].dtype) for c in filtered.columns],
            "Missing values": [int(filtered[c].isna().sum()) for c in filtered.columns],
            "Missing %": [round(float(filtered[c].isna().mean() * 100), 1) for c in filtered.columns],
            "Unique values": [int(filtered[c].nunique(dropna=True)) for c in filtered.columns],
        })
        st.dataframe(quality, use_container_width=True, hide_index=True)
    st.markdown("#### Filtered records")
    st.dataframe(filtered, use_container_width=True, hide_index=True, height=480)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download filtered CSV", csv_bytes, "shopscope_filtered_data.csv", "text/csv")
    st.markdown("#### Source column mapping")
    mapping = pd.DataFrame([
        {"ShopScope field": key.replace("_", " ").title(), "Detected CSV column": value or "Not available"}
        for key, value in cols.items()
    ])
    st.dataframe(mapping, use_container_width=True, hide_index=True)

# ---------- Footer ----------
st.divider()
st.markdown(
    '<div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;'
    'color:#7889a7;font-size:.78rem;"><span>SHOP SCOPE · COMMERCE INTELLIGENCE</span>'
    '<span>Built for data-driven decisions</span></div>',
    unsafe_allow_html=True,
)
