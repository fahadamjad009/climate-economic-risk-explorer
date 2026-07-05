"""
Climate-Economic Risk Explorer - Streamlit app.

Run with:
    streamlit run app/app.py
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "climate.duckdb"
HEAT_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "heat_anomaly_model.json"
RISK_MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "high_risk_model.json"

st.set_page_config(
    page_title="Climate-Economic Risk Explorer",
    page_icon="\U0001F30D",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Apple-style theme: near-black bg, big bold type, CSS-native scroll fade-ins
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
}

.stApp {
    background: #000000;
}

/* Scroll-triggered fade-up, CSS-native (no JS) - supported in Chromium/Brave */
.scroll-section {
    animation: fadeUp linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 35%;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(28px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    color: #F5F5F7;
    letter-spacing: -0.03em;
    margin-bottom: 0.2rem;
    line-height: 1.05;
}
.hero-accent {
    background: linear-gradient(90deg, #A78BFA 0%, #60D9EF 60%, #34D399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-subtitle {
    color: #86868B;
    font-size: 1.15rem;
    font-weight: 400;
    margin-bottom: 2.5rem;
    letter-spacing: -0.01em;
}

.section-header {
    font-size: 2rem;
    font-weight: 700;
    color: #F5F5F7;
    margin-top: 5rem;
    margin-bottom: 0.4rem;
    letter-spacing: -0.02em;
}
.section-subtext {
    color: #86868B;
    font-size: 1.02rem;
    margin-bottom: 1.6rem;
    max-width: 650px;
}

.kpi-card {
    background: linear-gradient(145deg, rgba(139,92,246,0.10), rgba(52,211,153,0.05));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    backdrop-filter: blur(10px);
}
.kpi-label {
    font-size: 0.75rem;
    color: #86868B;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #F5F5F7;
    font-family: 'JetBrains Mono', monospace;
}

.risk-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.02em;
}
.risk-high { background: rgba(248,113,113,0.15); color: #F87171; border: 1px solid rgba(248,113,113,0.4); }
.risk-normal { background: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.4); }

section[data-testid="stSidebar"] {
    background: #000000;
    border-right: 1px solid rgba(255,255,255,0.06);
}

.chip-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #34D399;
    letter-spacing: 0.05em;
    margin-bottom: 0.8rem;
}
div[data-testid="column"] .stButton button {
    width: 100%;
    border-radius: 10px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.6rem !important;
    transition: all 0.15s ease;
}
div[data-testid="column"] .stButton button[kind="secondary"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #86868B !important;
}
div[data-testid="column"] .stButton button[kind="secondary"]:hover {
    border-color: rgba(52,211,153,0.5) !important;
    color: #F5F5F7 !important;
}
div[data-testid="column"] .stButton button[kind="primary"] {
    background: rgba(52,211,153,0.14) !important;
    border: 1px solid #34D399 !important;
    color: #34D399 !important;
    font-weight: 700 !important;
}
</style>
"""

PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.02)",
    font=dict(color="#E8EAF0", family="Inter"),
)


@st.cache_resource
def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data
def load_city_year_features() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM city_year_features").df()


@st.cache_data
def load_weather_daily() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM weather_daily").df()


@st.cache_data
def load_temp_forecasts() -> pd.DataFrame:
    return get_connection().execute("SELECT * FROM city_temp_forecasts").df()


@st.cache_data
def load_city_locations() -> pd.DataFrame:
    return get_connection().execute("""
        SELECT DISTINCT city, country, lat, lon FROM weather_daily ORDER BY city
    """).df()


@st.cache_resource
def load_heat_model():
    model = xgb.XGBClassifier()
    model.load_model(str(HEAT_MODEL_PATH))
    return model


@st.cache_resource
def load_risk_model():
    model = xgb.XGBClassifier()
    model.load_model(str(RISK_MODEL_PATH))
    return model


def score_heat_anomaly_risk(city: str, weather: pd.DataFrame, locations: pd.DataFrame) -> float:
    """Score current heat-anomaly risk for a city using the trained XGBoost
    classifier, replicating the exact feature engineering used in training
    (lag/trailing weather features + day-of-year + city climatology)."""
    city_weather = weather[weather["city"] == city].copy()
    city_weather["date"] = pd.to_datetime(city_weather["date"])
    city_weather = city_weather.sort_values("date")

    last_date = city_weather["date"].max()
    next_day_of_year = (last_date + pd.Timedelta(days=1)).dayofyear

    last_row = city_weather.iloc[-1]
    lag1 = last_row["temperature_2m_max"]
    lag2 = city_weather.iloc[-2]["temperature_2m_max"]
    trailing_3day = city_weather["temperature_2m_max"].tail(3).mean()
    trailing_7day_temp = city_weather["temperature_2m_max"].tail(7).mean()
    trailing_7day_precip = city_weather["precipitation_sum"].tail(7).mean()

    # Full-history climatology (correct for live inference - no leakage
    # concern here since we're not fitting/labeling, just scoring)
    city_weather["day_of_year"] = city_weather["date"].dt.dayofyear
    climo_mean = city_weather[city_weather["day_of_year"] == next_day_of_year]["temperature_2m_max"].mean()

    loc_row = locations[locations["city"] == city].iloc[0]

    features = pd.DataFrame([{
        "lat": loc_row["lat"], "lon": loc_row["lon"],
        "day_of_year_sin": np.sin(2 * np.pi * next_day_of_year / 365.25),
        "day_of_year_cos": np.cos(2 * np.pi * next_day_of_year / 365.25),
        "lag1_temp_max": lag1, "lag2_temp_max": lag2,
        "trailing_3day_avg_temp": trailing_3day,
        "trailing_7day_avg_temp": trailing_7day_temp,
        "trailing_7day_avg_precip": trailing_7day_precip,
        "climo_mean": climo_mean,
    }])
    model = load_heat_model()
    return float(model.predict_proba(features)[0, 1])


def score_high_risk_year(city: str, features_df: pd.DataFrame) -> float:
    """Score probability that this city's most recent year qualifies as a
    high-risk (top-quartile damage-to-GDP) year, using the trained classifier."""
    city_latest = features_df[features_df["city"] == city].sort_values("year").iloc[-1]
    feature_cols = [
        "avg_temp_c", "max_temp_c", "min_temp_c",
        "total_precip_mm", "max_daily_precip_mm",
        "days_over_35c", "heavy_rain_days", "avg_max_windspeed",
        "population",
    ]
    X = pd.DataFrame([city_latest[feature_cols]])
    model = load_risk_model()
    return float(model.predict_proba(X)[0, 1])



    col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str, col):
    col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)


def section(title: str, subtext: str = ""):
    st.markdown(f'<div class="section-header scroll-section">{title}</div>', unsafe_allow_html=True)
    if subtext:
        st.markdown(f'<div class="section-subtext scroll-section">{subtext}</div>', unsafe_allow_html=True)


def temp_to_rgb(temp, vmin=10, vmax=30):
    """Map avg temp to a blue->red RGB gradient for the pydeck map."""
    t = np.clip((temp - vmin) / (vmax - vmin), 0, 1)
    r = int(30 + t * 220)
    g = int(80 + (1 - abs(t - 0.5) * 2) * 100)
    b = int(255 - t * 220)
    return [r, g, b, 200]


def render_map(city_avg: pd.DataFrame):
    city_avg = city_avg.copy()
    city_avg["radius"] = np.sqrt(city_avg["total_disaster_damage"].clip(lower=1)) * 2.2
    city_avg["color"] = city_avg["avg_temp_c"].apply(temp_to_rgb)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=city_avg,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="color",
        radius_min_pixels=6,
        radius_max_pixels=55,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 120],
    )
    view_state = pdk.ViewState(latitude=15, longitude=20, zoom=1.3, pitch=25)
    tooltip = {
        "html": "<b>{city}</b>, {country}<br/>Avg temp: {avg_temp_c}\u00b0C"
                "<br/>Total damage: ${total_disaster_damage}",
        "style": {"backgroundColor": "#131722", "color": "#F5F5F7", "fontFamily": "Inter"},
    }
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip=tooltip,
    )
    st.pydeck_chart(deck, use_container_width=True)


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    features = load_city_year_features()
    locations = load_city_locations()
    weather = load_weather_daily()
    forecasts = load_temp_forecasts()

    st.markdown(
        '<div class="hero-title">Climate-Economic <span class="hero-accent">Risk Explorer</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hero-subtitle">10 years of weather, GDP, and disaster data across 30 global '
        'cities \u2014 with ML-based risk forecasting.</div>',
        unsafe_allow_html=True,
    )

    # --- City selector: chip grid ---
    st.markdown('<div class="chip-label">// SELECT A CITY</div>', unsafe_allow_html=True)
    city_list = sorted(locations["city"].unique())

    if "selected_city" not in st.session_state:
        st.session_state.selected_city = "Sydney" if "Sydney" in city_list else city_list[0]

    CHIPS_PER_ROW = 6
    for row_start in range(0, len(city_list), CHIPS_PER_ROW):
        row_cities = city_list[row_start:row_start + CHIPS_PER_ROW]
        cols = st.columns(CHIPS_PER_ROW)
        for col, city in zip(cols, row_cities):
            is_selected = city == st.session_state.selected_city
            if col.button(city, key=f"city_chip_{city}",
                           type="primary" if is_selected else "secondary",
                           use_container_width=True):
                st.session_state.selected_city = city
                st.rerun()

    selected_city = st.session_state.selected_city
    city_row = locations[locations["city"] == selected_city].iloc[0]
    st.caption(f"**{selected_city}, {city_row['country']}**  \u00b7  {city_row['lat']:.2f}, {city_row['lon']:.2f}")

    # --- Global KPI row ---
    total_damage = features["disaster_damage_usd"].sum()
    global_avg_temp = features["avg_temp_c"].mean()
    total_events = features["disaster_event_count"].sum()
    n_cities = features["city"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card("Cities Tracked", f"{n_cities}", c1)
    kpi_card("Global Avg Temp", f"{global_avg_temp:.1f}\u00b0C", c2)
    kpi_card("Total Disaster Events", f"{int(total_events):,}", c3)
    kpi_card("Total Damage (USD)", f"${total_damage/1e9:.1f}B", c4)

    # --- Global map (pydeck / deck.gl - smooth WebGL zoom+pan) ---
    section("Global Overview", "Bubble size = total disaster damage 2016-2025. Color = average temperature. Zoom and pan freely.")

    city_avg = features.groupby(["city", "lat", "lon", "country"]).agg(
        avg_temp_c=("avg_temp_c", "mean"),
        total_disaster_damage=("disaster_damage_usd", "sum"),
    ).reset_index()
    render_map(city_avg)

    # --- City deep-dive: temperature trend + forecast ---
    section(f"{selected_city}: Temperature Trend & Forecast")

    city_weather = weather[weather["city"] == selected_city].copy()
    city_weather["date"] = pd.to_datetime(city_weather["date"])
    city_weather["year"] = city_weather["date"].dt.year
    yearly_temp = city_weather.groupby("year")["temperature_2m_mean"].mean().reset_index()
    city_forecast = forecasts[forecasts["city"] == selected_city]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=yearly_temp["year"], y=yearly_temp["temperature_2m_mean"],
        mode="lines+markers", name="Historical avg temp",
        line=dict(color="#60D9EF", width=3), marker=dict(size=8),
    ))
    if not city_forecast.empty:
        trend_c_decade = city_forecast["warming_trend_c_per_decade"].iloc[0]
        last_year = yearly_temp["year"].max()
        last_val = yearly_temp["temperature_2m_mean"].iloc[-1]
        fig_trend.add_trace(go.Scatter(
            x=[last_year, last_year + 1, last_year + 2],
            y=[last_val, city_forecast["avg_temp_forecast_year1"].iloc[0], city_forecast["avg_temp_forecast_year2"].iloc[0]],
            mode="lines+markers", name="ETS forecast",
            line=dict(color="#A78BFA", width=3, dash="dash"), marker=dict(size=8, symbol="diamond"),
        ))
        st.markdown(
            f'<span class="risk-badge {"risk-high" if trend_c_decade > 0.5 else "risk-normal"}">'
            f'{trend_c_decade:+.2f}\u00b0C / decade warming trend</span>',
            unsafe_allow_html=True,
        )

    fig_trend.update_layout(
        height=380, **PLOTLY_DARK,
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Year"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)", title="Avg Temp (\u00b0C)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_trend, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Live risk score card: actual trained XGBoost models, scored live ---
    section(f"{selected_city}: Live Risk Score", "Computed live from the trained XGBoost models - not pre-cached values.")

    try:
        heat_risk = score_heat_anomaly_risk(selected_city, weather, locations)
        year_risk = score_high_risk_year(selected_city, features)

        rc1, rc2 = st.columns(2)
        with rc1:
            badge_class = "risk-high" if heat_risk >= 0.5 else "risk-normal"
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Extreme Heat Risk (Next Day)</div>
                    <div class="kpi-value">{heat_risk*100:.0f}%</div>
                    <span class="risk-badge {badge_class}">{"Elevated" if heat_risk >= 0.5 else "Normal"}</span>
                </div>
            """, unsafe_allow_html=True)
        with rc2:
            badge_class = "risk-high" if year_risk >= 0.5 else "risk-normal"
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">High-Damage-Year Probability</div>
                    <div class="kpi-value">{year_risk*100:.0f}%</div>
                    <span class="risk-badge {badge_class}">{"Elevated" if year_risk >= 0.5 else "Normal"}</span>
                </div>
            """, unsafe_allow_html=True)
        st.caption(
            "Heat risk: XGBoost classifier, ROC-AUC 0.898 on held-out data. "
            "High-damage-year risk: XGBoost classifier, ROC-AUC 0.754 on held-out data."
        )
    except Exception as e:
        st.warning(f"Could not compute live risk scores for {selected_city}: {e}")

    # --- Disaster damage by city ---
    section("Disaster Damage: Top 10 Cities", "Total climate-related disaster damage, 2016-2025 (USD billions).")

    damage_by_city = features.groupby("city")["disaster_damage_usd"].sum().sort_values(ascending=False).head(10).reset_index()
    damage_by_city["damage_billions"] = damage_by_city["disaster_damage_usd"] / 1e9

    fig_bar = px.bar(
        damage_by_city, x="damage_billions", y="city", orientation="h",
        color="damage_billions", color_continuous_scale="Magma",
        labels={"damage_billions": "Total Damage (USD Billions)", "city": ""},
    )
    fig_bar.update_layout(
        height=420, **PLOTLY_DARK,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- EDA: distribution boxplots across all cities ---
    section("Climate Distributions Across Cities", "How temperature and rainfall vary and spread within each city's 10-year record.")

    top_cities_by_damage = damage_by_city["city"].tolist()
    box_data = weather[weather["city"].isin(top_cities_by_damage)]

    fig_box = px.box(
        box_data, x="city", y="temperature_2m_mean", color="city",
        labels={"temperature_2m_mean": "Daily Mean Temp (\u00b0C)", "city": ""},
        points=False,
    )
    fig_box.update_layout(
        height=440, **PLOTLY_DARK,
        showlegend=False,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- EDA: correlation heatmap ---
    section("What Drives Disaster Damage?", "Correlation between climate extremes, economic context, and disaster outcomes across all 300 city-years.")

    corr_cols = [
        "avg_temp_c", "max_temp_c", "days_over_35c", "total_precip_mm",
        "heavy_rain_days", "avg_max_windspeed", "gdp_current_usd",
        "population", "disaster_damage_usd", "disaster_deaths",
    ]
    corr_matrix = features[corr_cols].corr()

    fig_heat = px.imshow(
        corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        aspect="auto",
    )
    fig_heat.update_layout(
        height=480, **PLOTLY_DARK,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- EDA: treemap of damage by country -> city ---
    section("Where the Damage Concentrates", "Total disaster damage 2016-2025, broken down by country and city. Box size = dollar exposure.")

    treemap_data = features.groupby(["country", "city"])["disaster_damage_usd"].sum().reset_index()
    treemap_data = treemap_data[treemap_data["disaster_damage_usd"] > 0]

    fig_tree = px.treemap(
        treemap_data, path=["country", "city"], values="disaster_damage_usd",
        color="disaster_damage_usd", color_continuous_scale="Magma",
    )
    fig_tree.update_layout(
        height=520, **PLOTLY_DARK,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
    )
    fig_tree.update_traces(textfont=dict(size=14))
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_tree, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- POLICY & BUSINESS: risk matrix (probability x impact) ---
    section(
        "Climate Risk Matrix: Where to Prioritize Adaptation Investment",
        "Classic risk-management framing. X-axis = frequency of extreme heat days (probability). "
        "Y-axis = disaster damage as % of GDP (financial impact). Bubble size = population exposed. "
        "The top-right quadrant is where climate-adaptation funding has the highest marginal value: "
        "cities facing both frequent extreme events AND high proportional economic exposure.",
    )

    risk_data = features.groupby(["city", "country"]).agg(
        avg_heat_days=("days_over_35c", "mean"),
        total_damage=("disaster_damage_usd", "sum"),
        avg_gdp=("gdp_current_usd", "mean"),
        population=("population", "mean"),
    ).reset_index()
    risk_data["damage_to_gdp_pct"] = risk_data["total_damage"] / (risk_data["avg_gdp"] * 10) * 100  # avg annual damage vs GDP

    heat_median = risk_data["avg_heat_days"].median()
    damage_median = risk_data["damage_to_gdp_pct"].median()

    fig_matrix = px.scatter(
        risk_data, x="avg_heat_days", y="damage_to_gdp_pct",
        size="population", color="country", hover_name="city",
        labels={"avg_heat_days": "Avg Extreme Heat Days / Year", "damage_to_gdp_pct": "Avg Annual Damage (% of GDP)"},
        size_max=45,
    )
    fig_matrix.add_hline(y=damage_median, line_dash="dot", line_color="rgba(255,255,255,0.25)")
    fig_matrix.add_vline(x=heat_median, line_dash="dot", line_color="rgba(255,255,255,0.25)")
    fig_matrix.update_layout(
        height=560, **PLOTLY_DARK,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(font=dict(size=10)),
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_matrix, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- POLICY & BUSINESS: humanitarian lens ---
    section(
        "Humanitarian Exposure",
        "People affected vs. lives lost per city, 2016-2025. Bubble size = population. "
        "Cities far up-and-right combine high casualty risk with high displacement risk - "
        "the priority targets for early-warning systems and disaster-response funding.",
    )

    humanitarian = features.groupby(["city", "country"]).agg(
        total_affected=("disaster_affected", "sum"),
        total_deaths=("disaster_deaths", "sum"),
        population=("population", "mean"),
    ).reset_index()
    humanitarian = humanitarian[(humanitarian["total_affected"] > 0) | (humanitarian["total_deaths"] > 0)]

    fig_human = px.scatter(
        humanitarian, x="total_affected", y="total_deaths",
        size="population", color="country", hover_name="city",
        labels={"total_affected": "Total People Affected (2016-2025)", "total_deaths": "Total Deaths (2016-2025)"},
        size_max=45, log_x=True,
    )
    fig_human.update_layout(
        height=520, **PLOTLY_DARK,
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(font=dict(size=10)),
    )
    st.markdown('<div class="scroll-section">', unsafe_allow_html=True)
    st.plotly_chart(fig_human, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Closing: policy recommendations, derived dynamically from the data ---
    section("Key Findings & Policy Recommendations")

    priority_cities = risk_data[
        (risk_data["avg_heat_days"] >= heat_median) & (risk_data["damage_to_gdp_pct"] >= damage_median)
    ].sort_values("damage_to_gdp_pct", ascending=False)

    top_humanitarian = humanitarian.sort_values("total_deaths", ascending=False).head(3)
    fastest_warming = forecasts.sort_values("warming_trend_c_per_decade", ascending=False).head(3)

    priority_list = ", ".join(priority_cities["city"].head(5).tolist()) if len(priority_cities) > 0 else "none identified"
    humanitarian_list = ", ".join(top_humanitarian["city"].tolist())
    warming_list = ", ".join(
        f"{row['city']} ({row['warming_trend_c_per_decade']:+.1f}\u00b0C/decade)"
        for _, row in fastest_warming.iterrows()
    )

    st.markdown(f"""
        <div class="section-subtext scroll-section" style="max-width: 900px; font-size: 1.05rem; line-height: 1.7;">
        <p><b style="color:#F87171;">Adaptation investment priority</b> \u2014 {priority_list} sit in the
        top-right risk quadrant: frequent extreme heat combined with above-median damage relative to
        GDP size. These cities get the highest marginal return on climate-adaptation infrastructure
        spending (cooling centers, flood defenses, early-warning systems).</p>
        <p><b style="color:#60D9EF;">Humanitarian response priority</b> \u2014 {humanitarian_list} recorded
        the highest disaster death tolls in the dataset. Disaster-response funding and evacuation
        planning should weight these cities most heavily.</p>
        <p><b style="color:#A78BFA;">Fastest-warming cities</b> \u2014 {warming_list}. Absolute-dollar
        damage regression (R\u00b2=0.25) and GDP-ratio regression (R\u00b2=0.12) both struggled to predict
        exact damage figures, because catastrophic losses are driven by discrete events (a hurricane
        landfall, a specific flood) rather than smooth yearly climate trends. The high-risk-year
        classifier (ROC-AUC=0.75) is the more robust and actionable framing \u2014 consistent with how
        real catastrophe risk models are used in practice: as screening tools, not precise forecasters.</p>
        </div>
    """, unsafe_allow_html=True)




if __name__ == "__main__":
    main()
