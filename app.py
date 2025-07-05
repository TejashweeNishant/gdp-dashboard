import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="GDP Dashboard", layout="wide")

# ------------------ CUSTOM CSS DARK THEME ------------------
theme_css = """
    <style>
        body { background-color: #0e1117; color: #e1e1e1; font-family: 'Segoe UI', sans-serif; font-size: 16px; }
        .block-container { padding: 1rem 2rem; }
        .sidebar .sidebar-content { background-color: #161b22; color: #e1e1e1; }
        .metric-box { background-color: #1c212b; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .metric-box h4 { color: #f0f6fc; margin-bottom: 8px; font-size: 18px; }
        .metric-box h2 { color: #79c0ff; font-size: 28px; }
        .stTabs [role="tab"] { background: #21262d; color: #c9d1d9; border: none; font-size: 15px; }
        .stTabs [aria-selected="true"] { background: #30363d; color: #ffffff; font-weight: bold; }
        .summary-table { background-color: #1e232e; border-radius: 10px; padding: 15px; margin-top: 20px; }
    </style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# ------------------ LOAD DATA ------------------
@st.cache_data

def load_data():
    df = pd.read_csv("gdp.csv")
    if "Value" in df.columns:
        df.rename(columns={"Value": "GDP"}, inplace=True)
    if "Country Code" in df.columns:
        region_map = {
            "Asia": ["CN", "IN", "JP", "ID", "KR", "SG", "SA"],
            "Europe": ["DE", "FR", "GB", "IT", "RU", "ES"],
            "North America": ["US", "CA", "MX"],
            "South America": ["BR", "AR", "CO"],
            "Africa": ["ZA", "NG", "EG", "KE"],
            "Oceania": ["AU", "NZ"]
        }
        reverse_region = {code: region for region, codes in region_map.items() for code in codes}
        df["Region"] = df["Country Code"].map(reverse_region)
    return df

df = load_data()

# ------------------ SIDEBAR FILTER FORM ------------------
st.sidebar.title("Filters")
with st.sidebar.form(key="filter_form"):
    years = sorted(df["Year"].unique())
    year_range = st.slider("Year Range", min_value=int(min(years)), max_value=int(max(years)), value=(2000, max(years)))

    countries = sorted(df["Country Name"].unique())
    selected_countries = st.multiselect("Select Countries", countries, default=["India", "United States", "China"])

    show_kpi = st.checkbox("Show KPI Summary", value=True)
    show_download = st.checkbox("Enable Data Export", value=True)
    show_pct = st.radio("GDP View Mode", ["Absolute GDP ($)", "Growth %"], index=0)

    submit_button = st.form_submit_button(label="Apply Filters")

# ------------------ INITIAL VIEW ------------------
if "filters_applied" not in st.session_state and not submit_button:
    st.title("Global Economic Snapshot")
    st.markdown("Gain a high-level overview of global GDP distribution and performance.")

    latest_year = df["Year"].max()
    map_df = df[df["Year"] == latest_year]

    st.subheader(f"World GDP Map ({latest_year})")
    fig_map = px.choropleth(map_df, locations="Country Name", locationmode="country names",
                            color="GDP", hover_name="Country Name", color_continuous_scale="Viridis",
                            template="plotly_dark")
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader(f"Top 10 Economies in {latest_year}")
    top10 = map_df.sort_values(by="GDP", ascending=False).head(10)
    fig_top = px.bar(top10, x="Country Name", y="GDP", color="Country Name",
                     template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set1)
    st.plotly_chart(fig_top, use_container_width=True)

    st.info("Adjust filters from the sidebar and click 'Apply Filters' to explore detailed insights.")
    st.stop()

st.session_state.filters_applied = True
filtered_df = df[
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1]) &
    (df["Country Name"].isin(selected_countries))
]

# ------------------ GDP GROWTH ------------------
def calculate_gdp_growth(df):
    df_sorted = df.sort_values(by=["Country Name", "Year"])
    df_sorted["GDP Growth %"] = df_sorted.groupby("Country Name")["GDP"].pct_change() * 100
    return df_sorted

filtered_df = calculate_gdp_growth(filtered_df)

# ------------------ HEADER ------------------
st.title("GDP Analytics Dashboard")
st.markdown("Analyze country-wise GDP performance and growth over time.")

# ------------------ KPI CARDS ------------------
if show_kpi:
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"<div class='metric-box'><h4>Total GDP</h4><h2>${filtered_df['GDP'].sum():,.0f}</h2></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='metric-box'><h4>Average GDP</h4><h2>${filtered_df['GDP'].mean():,.0f}</h2></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='metric-box'><h4>Max GDP</h4><h2>${filtered_df['GDP'].max():,.0f}</h2></div>", unsafe_allow_html=True)

st.markdown("---")

# ------------------ TABS ORGANIZED ------------------
st.markdown("### Visual Analytics")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["GDP Over Time", "GDP by Country", "GDP Distribution", "GDP Growth", "Treemap View"])

with tab1:
    st.subheader("Trend Over Years")
    y_val = "GDP Growth %" if show_pct == "Growth %" else "GDP"
    fig = px.line(
        filtered_df, x="Year", y=y_val, color="Country Name",
        line_dash="Country Name", hover_data={"GDP":":,.0f"}, markers=True,
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"GDP Ranking - {year_range[1]}")
    year_df = df[(df["Year"] == year_range[1]) & (df["Country Name"].isin(selected_countries))]
    year_df_sorted = year_df.sort_values(by="GDP", ascending=False)
    fig_bar = px.bar(
        year_df_sorted, x="Country Name", y="GDP", color="Country Name",
        text="GDP", template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader(f"GDP Share - {year_range[1]}")
    pie_df = year_df
    fig_pie = px.pie(pie_df, names="Country Name", values="GDP", template="plotly_dark",
                     color_discrete_sequence=px.colors.qualitative.Set3, hole=0.45)
    fig_pie.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with tab4:
    st.subheader("Annual Growth Rates")
    growth_df = filtered_df.dropna(subset=["GDP Growth %"])
    fig_growth = px.line(growth_df, x="Year", y="GDP Growth %", color="Country Name", markers=True,
                         template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Dark2)
    st.plotly_chart(fig_growth, use_container_width=True)

with tab5:
    st.subheader("GDP Treemap by Country")
    treemap_df = year_df.sort_values(by="GDP", ascending=False)
    fig_tree = px.treemap(treemap_df, path=['Country Name'], values='GDP', template="plotly_dark")
    st.plotly_chart(fig_tree, use_container_width=True)

# ------------------ SUMMARY ------------------
st.markdown("### Country Summary & Data Table")
tab6, tab7 = st.tabs(["Summary View", "Raw Data"])

with tab6:
    st.subheader(f"Country GDP Summary ({year_range[1]})")
    latest_df = df[(df["Year"] == year_range[1]) & (df["Country Name"].isin(selected_countries))]
    st.markdown("<div class='summary-table'>", unsafe_allow_html=True)
    st.dataframe(latest_df[["Country Name", "GDP"]].rename(columns={"Country Name": "Country"}))
    st.markdown("</div>", unsafe_allow_html=True)

with tab7:
    st.subheader("Filtered GDP Records")
    st.dataframe(filtered_df)
    if show_download:
        csv = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "filtered_gdp.csv", "text/csv")

# ------------------ INSIGHTS ------------------
st.markdown("### Global GDP Insights")
tab8, tab9 = st.tabs(["Animated Timeline", "Fastest Growing Countries"])

with tab8:
    st.subheader("Animated GDP Map")
    animated_df = df[df["Country Name"].isin(selected_countries)]
    fig_animated = px.choropleth(animated_df, locations="Country Name", locationmode="country names",
                                 color="GDP", hover_name="Country Name", animation_frame="Year",
                                 color_continuous_scale="Plasma", template="plotly_dark")
    st.plotly_chart(fig_animated, use_container_width=True)

with tab9:
    st.subheader("Top Performers by Growth")
    growth = calculate_gdp_growth(df)
    latest = growth[growth["Year"] == year_range[1]].dropna(subset=["GDP Growth %"])
    top_growth = latest.sort_values(by="GDP Growth %", ascending=False).head(10)
    fig_top_growth = px.bar(top_growth, x="Country Name", y="GDP Growth %", color="Country Name",
                            template="plotly_dark", color_discrete_sequence=px.colors.qualitative.T10)
    st.plotly_chart(fig_top_growth, use_container_width=True)

st.markdown("---")
st.caption("Crafted with care by Tejashwee • Streamlit + Plotly")
