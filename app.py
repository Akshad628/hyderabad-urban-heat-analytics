from pathlib import Path
import pandas as pd
import plotly.express as px
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
selected_year = st.sidebar.selectbox("Analysis year", years, index=len(years)-1)
heat = zonal[zonal["year"] == selected_year].copy()

st.sidebar.markdown("---")
st.sidebar.caption("LST is land-surface temperature, not air temperature.")
st.sidebar.caption("Zone averages are grouped using rounded geographic coordinates.")

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
