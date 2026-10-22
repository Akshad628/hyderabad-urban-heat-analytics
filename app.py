from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Hyderabad Urban Heat Analytics",
    page_icon="🌡️",
    layout="wide"
)

ROOT = Path(__file__).parent


@st.cache_data
def load_data():
    zonal = pd.read_csv(ROOT / "uhi_zonal_summary.csv")
    annual = pd.read_csv(ROOT / "uhi_annual_summary.csv")
    zonal["year"] = zonal["year"].astype(int)
    annual["year"] = annual["year"].astype(int)
    return zonal, annual


try:
    zonal, annual = load_data()
except Exception as e:
    st.error(f"Could not load dashboard data: {e}")
    st.stop()

st.title("🌡️ Hyderabad Urban Heat Island Analytics")
st.caption(
    "Satellite-derived land-surface temperature (LST) and "
    "Normalized Difference Vegetation Index (NDVI), 2022–2025"
)

years = sorted(zonal["year"].unique())
selected_year = st.sidebar.selectbox(
    "Analysis year", years, index=len(years) - 1
)
heat = zonal[zonal["year"] == selected_year].copy()

st.sidebar.markdown("---")
st.sidebar.caption("LST is land-surface temperature, not air temperature.")
st.sidebar.caption(
    "Zone averages are grouped using rounded geographic coordinates."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Year", str(selected_year))
c2.metric("Mean LST", f"{heat['mean_lst_c'].mean():.2f} °C")
c3.metric("Mean NDVI", f"{heat['mean_ndvi'].mean():.3f}")
c4.metric("Geographic zones", f"{len(heat):,}")

st.subheader(f"Temperature distribution — {selected_year}")
map_fig = px.scatter_map(
    heat,
    lat="latitude",
    lon="longitude",
    color="mean_lst_c",
    size="record_count",
    hover_name="year",
    hover_data={
        "mean_lst_c": ":.2f",
        "mean_ndvi": ":.3f",
        "record_count": True,
        "latitude": ":.4f",
        "longitude": ":.4f"
    },
    color_continuous_scale="Inferno",
    size_max=13,
    zoom=9,
    center={"lat": 17.385, "lon": 78.4867},
    map_style="open-street-map",
    labels={
        "mean_lst_c": "Mean LST (°C)",
        "mean_ndvi": "Mean NDVI",
        "record_count": "Records"
    }
)
map_fig.update_layout(height=600, margin={"l": 0, "r": 0, "t": 10, "b": 0})
st.plotly_chart(map_fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Annual temperature trend")
    trend = px.line(
        annual, x="year", y="mean_lst_c", markers=True,
        labels={"year": "Year", "mean_lst_c": "Mean LST (°C)"}
    )
    trend.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(trend, use_container_width=True)

with right:
    st.subheader("Vegetation vs. temperature")
    relation = px.scatter(
        heat, x="mean_ndvi", y="mean_lst_c",
        color="mean_lst_c", color_continuous_scale="Inferno",
        labels={"mean_ndvi": "Mean NDVI", "mean_lst_c": "Mean LST (°C)"},
        hover_data=["latitude", "longitude", "record_count"]
    )
    st.plotly_chart(relation, use_container_width=True)

st.subheader("Annual summary")
st.dataframe(annual.round(3), use_container_width=True, hide_index=True)

# -------------------------------------------------------------------
# NEW FEATURES: hotspot ranking, map layers, and correlation analysis
# These are intentionally placed between Annual summary and Zone-level data.
# -------------------------------------------------------------------
st.markdown("---")
st.header("🔎 Hotspot & Vegetation Analysis")
st.caption(
    f"Explore the hottest and coolest zones, switch map layers, and "
    f"measure the NDVI–LST relationship for {selected_year}."
)

st.subheader("1. Hottest and coolest zones")
hot_col, cool_col = st.columns(2)

hotspots = heat.nlargest(10, "mean_lst_c").copy()
coolspots = heat.nsmallest(10, "mean_lst_c").copy()

display_cols = [
    "latitude", "longitude", "mean_lst_c", "mean_ndvi", "record_count"
]
rename_cols = {
    "latitude": "Latitude",
    "longitude": "Longitude",
    "mean_lst_c": "Mean LST (°C)",
    "mean_ndvi": "Mean NDVI",
    "record_count": "Records"
}

with hot_col:
    st.markdown("**🔥 Top 10 hottest zones**")
    st.dataframe(
        hotspots[display_cols].rename(columns=rename_cols).round(4),
        use_container_width=True,
        hide_index=True
    )

with cool_col:
    st.markdown("**❄️ Top 10 coolest zones**")
    st.dataframe(
        coolspots[display_cols].rename(columns=rename_cols).round(4),
        use_container_width=True,
        hide_index=True
    )

st.subheader("2. Interactive map layers")
map_layer = st.radio(
    "Choose what to display",
    [
        "Land-surface temperature",
        "Vegetation (NDVI)",
        "Hotspots (top 10 hottest zones)"
    ],
    horizontal=True,
    key="uhi_map_layer"
)

map_data = heat.copy()
layer_kwargs = {
    "lat": "latitude",
    "lon": "longitude",
    "size": "record_count",
    "hover_data": {
        "mean_lst_c": ":.2f",
        "mean_ndvi": ":.3f",
        "record_count": True,
        "latitude": ":.4f",
        "longitude": ":.4f"
    },
    "size_max": 14,
    "zoom": 9,
    "center": {"lat": 17.385, "lon": 78.4867},
    "map_style": "open-street-map"
}

if map_layer == "Land-surface temperature":
    layer_fig = px.scatter_map(
        map_data,
        color="mean_lst_c",
        color_continuous_scale="Inferno",
        labels={"mean_lst_c": "Mean LST (°C)"},
        **layer_kwargs
    )
elif map_layer == "Vegetation (NDVI)":
    layer_fig = px.scatter_map(
        map_data,
        color="mean_ndvi",
        color_continuous_scale="Greens",
        labels={"mean_ndvi": "Mean NDVI"},
        **layer_kwargs
    )
else:
    map_data["Zone category"] = np.where(
        map_data.index.isin(hotspots.index),
        "Top 10 hottest",
        "Other zones"
    )
    layer_fig = px.scatter_map(
        map_data,
        color="Zone category",
        color_discrete_map={
            "Top 10 hottest": "#e63946",
            "Other zones": "#9ca3af"
        },
        labels={"Zone category": "Zone category"},
        **layer_kwargs
    )

layer_fig.update_layout(
    height=520,
    margin={"l": 0, "r": 0, "t": 10, "b": 0},
    legend_title_text="Map layer"
)
st.plotly_chart(layer_fig, use_container_width=True)

st.subheader("3. NDVI–temperature correlation")
valid = heat[["mean_ndvi", "mean_lst_c"]].replace(
    [np.inf, -np.inf], np.nan
).dropna()

if len(valid) >= 2 and valid["mean_ndvi"].nunique() > 1 and valid["mean_lst_c"].nunique() > 1:
    pearson_r = valid["mean_ndvi"].corr(valid["mean_lst_c"], method="pearson")
    slope, intercept = np.polyfit(
        valid["mean_ndvi"].to_numpy(),
        valid["mean_lst_c"].to_numpy(),
        1
    )
    predicted = slope * valid["mean_ndvi"] + intercept
    ss_res = ((valid["mean_lst_c"] - predicted) ** 2).sum()
    ss_tot = ((valid["mean_lst_c"] - valid["mean_lst_c"].mean()) ** 2).sum()
    r_squared = 1 - (ss_res / ss_tot) if ss_tot else float("nan")

    r1, r2, r3 = st.columns(3)
    r1.metric("Pearson correlation (r)", f"{pearson_r:.3f}")
    r2.metric("R²", f"{r_squared:.3f}")
    if pearson_r < -0.1:
        interpretation = "Negative relationship"
    elif pearson_r > 0.1:
        interpretation = "Positive relationship"
    else:
        interpretation = "Weak or near-zero relationship"
    r3.metric("Relationship", interpretation)

    corr_fig = px.scatter(
        valid,
        x="mean_ndvi",
        y="mean_lst_c",
        labels={
            "mean_ndvi": "Mean NDVI",
            "mean_lst_c": "Mean LST (°C)"
        },
        opacity=0.65,
        title=f"NDVI vs. land-surface temperature — {selected_year}"
    )
    x_line = np.linspace(valid["mean_ndvi"].min(), valid["mean_ndvi"].max(), 100)
    corr_fig.add_trace(
        go.Scatter(
            x=x_line,
            y=slope * x_line + intercept,
            mode="lines",
            name="Linear trendline",
            line={"dash": "dash"}
        )
    )
    corr_fig.update_layout(height=430)
    st.plotly_chart(corr_fig, use_container_width=True)
    st.caption(
        "Pearson r describes the direction and strength of a linear relationship. "
        "R² describes how much of the observed temperature variation is explained "
        "by this simple linear fit in these zone-level data. Neither measure proves "
        "that vegetation causes a temperature change."
    )
else:
    st.info(
        "Not enough variation in valid NDVI and temperature values to calculate "
        "a meaningful correlation for this year."
    )

st.markdown("---")
# -------------------------------------------------------------------
# Existing zone-level table and download controls remain below unchanged.
# -------------------------------------------------------------------
st.subheader("Zone-level data")
st.dataframe(
    heat.sort_values("mean_lst_c", ascending=False),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Download selected year's zone data",
    data=heat.to_csv(index=False).encode("utf-8"),
    file_name=f"hyderabad_uhi_{selected_year}.csv",
    mime="text/csv"
)

st.download_button(
    "Download annual summary",
    data=annual.to_csv(index=False).encode("utf-8"),
    file_name="uhi_annual_summary.csv",
    mime="text/csv"
)

st.caption(
    "Interpretation note: higher LST indicates hotter land surfaces. "
    "NDVI indicates vegetation greenness; correlation does not establish causation."
)
