import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go  
import streamlit as st

st.set_page_config(
    page_title="Bike Shring Rental Analytics",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    margin: auto;
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
hours_df = pd.read_csv(os.path.join(BASE_DIR, "bike_sharing_hourly_clean.csv"))
hours_df['dteday'] = pd.to_datetime(hours_df['dteday'])
def create_daily_df(df):
    hasil = df.groupby('dteday').agg(
        season=('season', 'first'),
        yr=('yr', 'first'),
        mnth=('mnth', 'first'),
        weekday=('weekday', 'first'),
        casual=('casual', 'sum'),
        registered=('registered', 'sum'),
        cnt=('cnt', 'sum'),
        workingday=('workingday', 'first'),
        weathersit=('weathersit', lambda x: x.mode()[0]),
    ).reset_index()
    return hasil

day_label = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday',
             4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
month_label = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
               7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
season_label = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
weather_label = {1: 'Clear', 2: 'Mist', 3: 'Light Rain/Snow', 4: 'Heavy Rain/Snow'}
year_label = {0: 2011, 1: 2012}

highlight1 = "#E85D04"
highlight2 = "#FFBA6B"
grey = "#D9D9D9"

def create_hari_jam_df(df):
    hasil = df.groupby(['weekday', 'hr']).agg(
        **{'Rata-rata Penyewaan': ('cnt', 'mean')}
    ).reset_index()
    hasil = hasil.rename(columns={'weekday': 'Hari', 'hr': 'Jam'})
    hasil['Rata-rata Penyewaan'] = hasil['Rata-rata Penyewaan'].round(1)
    hasil['Hari'] = hasil['Hari'].map(day_label)
    hasil['Hari'] = pd.Categorical(hasil['Hari'], categories=day_order, ordered=True)
    return hasil

def create_rata2_per_hari_df(df):
    hasil = df.groupby('weekday').agg(
        **{'Rata-rata Penyewaan': ('cnt', 'mean')}
    ).reset_index()
    hasil = hasil.rename(columns={'weekday': 'Hari'})
    hasil['Hari'] = hasil['Hari'].map(day_label)
    hasil['Hari'] = pd.Categorical(hasil['Hari'], categories=day_order, ordered=True)
    hasil = hasil.sort_values('Hari').reset_index(drop=True)
    return hasil

def create_tren_bulanan_df(df):
    hasil = df.groupby(['yr', 'mnth']).agg(
        Total_Casual=('casual', 'sum'),
        Total_Registered=('registered', 'sum'),
        Total_Cnt=('cnt', 'sum')
    ).reset_index()
    hasil['Proporsi_Casual (%)'] = (hasil['Total_Casual'] / hasil['Total_Cnt'] * 100).round(1)
    tahun_asli = hasil['yr'].map(year_label)
    hasil['Periode'] = pd.to_datetime(dict(year=tahun_asli, month=hasil['mnth'], day=1))
    hasil = hasil.sort_values('Periode').reset_index(drop=True)
    hasil['Tahun'] = hasil['yr'].map(year_label).astype(str)
    hasil['Bulan'] = hasil['mnth'].map(month_label)
    hasil['Bulan'] = pd.Categorical(hasil['Bulan'], categories=list(month_label.values()), ordered=True)
    return hasil

def create_tabel_dominasi_df(df):
    hasil = df.groupby('season').agg(
        Total_Casual=('casual', 'sum'),
        Total_Registered=('registered', 'sum')
    ).reset_index()
    hasil['Total_Rental']=(hasil['Total_Casual'] + hasil['Total_Registered'])
    hasil['Rasio_Registered_per_Casual'] = (hasil['Total_Registered'] / hasil['Total_Casual']).round(2)
    hasil['season'] = hasil['season'].map(season_label)
    hasil = hasil.rename(columns={'season': 'Musim'})
    hasil = hasil.sort_values('Total_Rental', ascending=False).reset_index(drop=True)
    return hasil

def create_weather_cnt_df(df):
    hasil = df.groupby('weathersit')['cnt'].agg(
        Jumlah_Data='count', Rata_rata='mean', Median='median', Std_Deviasi='std', Min='min', Max='max'
    ).round(1).reset_index()
    hasil = hasil.rename(columns={'weathersit': 'Kondisi Cuaca'})
    hasil['Kondisi Cuaca'] = hasil['Kondisi Cuaca'].map(weather_label)
    return hasil

def create_weather_penyewa_df(df):
    hasil = df.groupby('weathersit')[['casual', 'registered']].mean().round(1).reset_index()
    hasil = hasil.rename(columns={'weathersit': 'Kondisi Cuaca', 'casual': 'Rata-rata Casual', 'registered': 'Rata-rata Registered'})
    hasil['Kondisi Cuaca'] = hasil['Kondisi Cuaca'].map(weather_label)
    return hasil

def create_env_group_df(df, kolom_asli, kolom_group):
    hasil = df.groupby(kolom_group, observed=True).agg(
        Rentang_Min=(kolom_asli, 'min'),
        Rentang_Max=(kolom_asli, 'max'),
        Rata_rata_Penyewaan=('cnt', 'mean')
    ).round(1).reindex(category_level)
    return hasil

def klasifikasi_archetype(row):
    if row['workingday'] == 1 and row['weathersit'] in [1, 2]:
        return 'Ideal Working Day'
    elif row['workingday'] == 1 and row['weathersit'] in [3, 4]:
        return 'Harsh Working Day'
    elif row['workingday'] == 0 and row['weathersit'] in [1, 2]:
        return 'Ideal Holiday'
    else:
        return 'Harsh Holiday'

hours_df['temp_celcius'] = (hours_df['temp'] * 41).round(1)
hours_df['hum_percent'] = (hours_df['hum'] * 100).round(1)
hours_df['windspeed_kmh'] = (hours_df['windspeed'] * 67).round(1)

category_level = ['Low', 'Medium', 'High', 'Very High']
hours_df['temp_group'] = pd.qcut(hours_df['temp_celcius'], q=4, labels=category_level)
hours_df['hum_group'] = pd.qcut(hours_df['hum_percent'], q=4, labels=category_level)
hours_df['windspeed_group'] = pd.qcut(hours_df['windspeed_kmh'], q=4, labels=category_level, duplicates='drop')

st.sidebar.header("Filter Data")

st.sidebar.warning(
    "Please select a **Start Date**, an **End Date**, and at least one **Season** "
    "below to filter the dashboard data accordingly."
)

min_date = hours_df['dteday'].min()
max_date = hours_df['dteday'].max()
date_range = st.sidebar.date_input(
    "Choose Data Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

try:
    start_date, end_date = date_range
except ValueError:
    start_date = date_range[0]
    end_date = max_date
    st.sidebar.info(
        "End date not selected. Using the maximum available date as the end date."
    )

season_choice = ["All Seasons"] + list(season_label.values())
selected_seasons_raw = st.sidebar.multiselect(
    "Select Seasons",
    options=season_choice,
    default=["All Seasons"]
)
if "All Seasons" in selected_seasons_raw:
    selected_seasons = list(season_label.values())
else:
    selected_seasons = selected_seasons_raw

if not selected_seasons_raw:
    st.sidebar.warning("No season selected. Please select at least one season to view the dashboard data.")
else:
    st.sidebar.caption("Data is filtered based on the selected date range and seasons.")

filtered_hours_df = hours_df[(hours_df['dteday']>=pd.to_datetime(start_date)) & (hours_df['dteday']<=pd.to_datetime(end_date)) & (hours_df['season'].map(season_label).isin(selected_seasons))].copy()
if filtered_hours_df.empty:
    st.sidebar.error("No data is available for the selected date range and seasons.")
    st.warning("No data is available for the selected date range and seasons. Please choose a different date range or season.")
    st.stop()

days_df = create_daily_df(filtered_hours_df)
hari_jam_sewa_df = create_hari_jam_df(filtered_hours_df)
rata2_per_hari_df = create_rata2_per_hari_df(days_df)
tren_bulanan_df = create_tren_bulanan_df(days_df)
tabel_dominasi_df = create_tabel_dominasi_df(days_df)
weather_cnt_df = create_weather_cnt_df(filtered_hours_df)
weather_penyewa_df = create_weather_penyewa_df(filtered_hours_df)
tabel_temp_df = create_env_group_df(filtered_hours_df, 'temp_celcius', 'temp_group')
tabel_hum_df = create_env_group_df(filtered_hours_df, 'hum_percent', 'hum_group')
tabel_windspeed_df = create_env_group_df(filtered_hours_df, 'windspeed_kmh', 'windspeed_group')


st.title("Bike Sharing Rental Analytics (2011-2012)")
total_rentals = filtered_hours_df['cnt'].sum()
total_casual = filtered_hours_df['casual'].sum()
total_registered = filtered_hours_df['registered'].sum()
total_2011 = days_df[days_df['yr'] == 0]['cnt'].sum()
total_2012 = days_df[days_df['yr'] == 1]['cnt'].sum()
growth = round((total_2012 - total_2011) / total_2011 * 100, 1) if total_2011 > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rentals", f"{total_rentals:,.0f}")
col2.metric("Total Casual Users", f"{total_casual:,.0f}")
col3.metric("Total Registered Users", f"{total_registered:,.0f}")
col4.metric("Rental Growth", f"{growth:+.1f}%")
st.divider()

#pertanyaan1
st.header("Hourly Rental Patterns")
weekday_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
weekend_list = ['Saturday', 'Sunday']
pilihan_jenis_hari = st.radio("Day Type:", ["Weekday", "Weekend"], horizontal=True)
if pilihan_jenis_hari == "Weekday":
    daftar_hari_aktif = weekday_list
else:
    daftar_hari_aktif = weekend_list

subset_df = hari_jam_sewa_df[hari_jam_sewa_df['Hari'].isin(daftar_hari_aktif)]
if subset_df.empty:
    st.warning("No data is available for the selected date range. Please select a different date range to continue.")
else:
    hari_tertinggi = subset_df.groupby('Hari', observed=True)['Rata-rata Penyewaan'].max().idxmax()
    baris_max = subset_df.loc[[subset_df['Rata-rata Penyewaan'].idxmax()]]
    baris_min = subset_df.loc[[subset_df['Rata-rata Penyewaan'].idxmin()]]

    col1, col2 = st.columns(2)
    col1.metric("Busiest Hour", f"{baris_max['Jam'].values[0]}:00", f"{baris_max['Rata-rata Penyewaan'].values[0]:.0f} rentals/hour on Average")
    col2.metric("Quietest Hour", f"{baris_min['Jam'].values[0]}:00", f"{baris_min['Rata-rata Penyewaan'].values[0]:.0f} rentals/hour on Average")

    palet_weekday = {
        'Monday': '#FDB863', 'Tuesday': '#E85D04', 'Wednesday': '#B2182B',
        'Thursday': '#F4A582', 'Friday': '#92C5DE'
    }
    palet_weekend = {
        'Saturday': '#E85D04', 'Sunday': '#FDB863'
    }
    palet = palet_weekday if pilihan_jenis_hari == "Weekday" else palet_weekend

    fig = go.Figure()
    for hari in daftar_hari_aktif:
        data_hari = subset_df[subset_df['Hari'] == hari]
        is_top = hari == hari_tertinggi
        fig.add_trace(go.Scatter(
            x=data_hari['Jam'], y=data_hari['Rata-rata Penyewaan'],
            mode='lines', name=hari,
            line=dict(width=3 if is_top else 1.6, color=palet[hari]),
            opacity=1.0 if is_top else 0.65,
            hovertemplate=f'{hari}<br>Hour %{{x}}:00<br>Avg Rentals: %{{y:.0f}}<extra></extra>'
        ))
    fig.add_trace(go.Scatter(
        x=baris_max['Jam'], y=baris_max['Rata-rata Penyewaan'],
        mode='markers', name='Highest Point',
        marker=dict(color='black', size=10, symbol='circle'),
        hovertemplate='Highest Point<br>Hour %{x}:00<br>Avg Rentals: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=baris_min['Jam'], y=baris_min['Rata-rata Penyewaan'],
        mode='markers', name='Lowest Point',
        marker=dict(color='black', size=10, symbol='x'),
        hovertemplate='Lowest Point<br>Hour %{x}:00<br>Avg Rentals: %{y:.0f}<extra></extra>'
    ))
    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=2, title='Hour'),
        yaxis=dict(title='Average Rentals'),
        hovermode='closest',
        legend=dict(orientation='v', yanchor='top', y=1, xanchor='left', x=1.02),
        margin=dict(t=60, b=40, r=120),
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Daily Rental Ranking")
hari_tertinggi_all = rata2_per_hari_df.loc[rata2_per_hari_df['Rata-rata Penyewaan'].idxmax(), 'Hari']
warna_bar = [highlight1 if h == hari_tertinggi_all else grey for h in rata2_per_hari_df['Hari']]

fig = go.Figure(go.Bar(
    x=rata2_per_hari_df['Hari'].astype(str),
    y=rata2_per_hari_df['Rata-rata Penyewaan'],
    marker_color=warna_bar,
    text=rata2_per_hari_df['Rata-rata Penyewaan'],
    texttemplate='%{text:.0f}',
    textposition='outside',
    hovertemplate='%{x}<br>Avg Rentals: %{y:.0f}<extra></extra>'
))
fig.update_layout(height=450, margin=dict(t=30, b=30), yaxis_title='Average Rentals')
st.plotly_chart(fig, use_container_width=True)

with st.expander("View Hourly Rental Data"):
    table = hari_jam_sewa_df.copy()
    table = table.rename(columns={'Hari': 'Day', 'Jam': 'Hour', 'Rata-rata Penyewaan': 'Average Rentals'})
    st.dataframe(table.style.format({'Average Rentals': '{:.0f}'}), hide_index=True, use_container_width=True)

st.divider()

#pertanyaan 2
st.header("Casual vs Registered Rental Pattern")
musim_tertinggi = tabel_dominasi_df.loc[tabel_dominasi_df['Total_Rental'].idxmax(), 'Musim']
musim_terendah = tabel_dominasi_df.loc[tabel_dominasi_df['Total_Rental'].idxmin(), 'Musim']

col1, col2 = st.columns(2)
col1.metric("Highest Rental Volume", musim_tertinggi)
col2.metric("Lowest Rental Volume", musim_terendah)

warna_tahun = {'2011': highlight2, '2012': highlight1}

col1, col2 = st.columns(2)
with col1:
    fig = go.Figure()
    for tahun in ['2011', '2012']:
        data_tahun = tren_bulanan_df[tren_bulanan_df['Tahun'] == tahun].sort_values('Bulan')
        if data_tahun.empty:
            continue
        fig.add_trace(go.Scatter(
            x=data_tahun['Bulan'].astype(str), y=data_tahun['Proporsi_Casual (%)'],
            mode='lines+markers', name=tahun,
            line=dict(width=2.2, color=warna_tahun[tahun]),
            marker=dict(size=6),
            hovertemplate=f'{tahun}<br>%{{x}}<br>Casual Proportion: %{{y:.1f}}%<extra></extra>'
        ))
    fig.update_layout(
        title='Casual Rental Proportion Trend by Month',
        xaxis=dict(tickangle=-45),
        yaxis_title='Casual Proportion (%)',
        height=450, margin=dict(t=50)
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=tabel_dominasi_df['Musim'], y=tabel_dominasi_df['Total_Casual'],
        name='Casual', marker_color=highlight2,
        hovertemplate='%{x}<br>Casual: %{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=tabel_dominasi_df['Musim'], y=tabel_dominasi_df['Total_Registered'],
        name='Registered', marker_color=highlight1,
        hovertemplate='%{x}<br>Registered: %{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(
        barmode='group', title='Rental Volume by Season',
        yaxis=dict(title='Total Rentals', tickformat=','),
        height=450, margin=dict(t=50)
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly Rental Volume Trend")
fig = go.Figure()
for tahun in ['2011', '2012']:
    data_tahun = tren_bulanan_df[tren_bulanan_df['Tahun'] == tahun].sort_values('Bulan')
    if data_tahun.empty:
        continue
    fig.add_trace(go.Scatter(
        x=data_tahun['Bulan'].astype(str), y=data_tahun['Total_Cnt'],
        mode='lines+markers', name=tahun,
        line=dict(width=2.2, color=warna_tahun[tahun]),
        marker=dict(size=6),
        hovertemplate=f'{tahun}<br>%{{x}}<br>Total Rentals: %{{y:,.0f}}<extra></extra>'
    ))
fig.update_layout(yaxis=dict(title='Total Rentals', tickformat=','), height=450, margin=dict(t=30))
st.plotly_chart(fig, use_container_width=True)
st.divider()

#pertanyaan 3
st.header("Weather Impact on Bike Rentals")
kondisi_tertinggi = weather_cnt_df.loc[weather_cnt_df['Rata_rata'].idxmax(), 'Kondisi Cuaca']
kondisi_terendah = weather_cnt_df.loc[weather_cnt_df['Rata_rata'].idxmin(), 'Kondisi Cuaca']

col1, col2 = st.columns(2)
col1.metric("Weather with Highest Rentals", kondisi_tertinggi)
col2.metric("Weather with Lowest Rentals", kondisi_terendah)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weather_penyewa_df['Kondisi Cuaca'], y=weather_penyewa_df['Rata-rata Casual'],
        name='Casual', marker_color=highlight2,
        text=weather_penyewa_df['Rata-rata Casual'], texttemplate='%{text:.0f}', textposition='outside',
        hovertemplate='%{x}<br>Avg Casual: %{y:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=weather_penyewa_df['Kondisi Cuaca'], y=weather_penyewa_df['Rata-rata Registered'],
        name='Registered', marker_color=highlight1,
        text=weather_penyewa_df['Rata-rata Registered'], texttemplate='%{text:.0f}', textposition='outside',
        hovertemplate='%{x}<br>Avg Registered: %{y:.0f}<extra></extra>'
    ))
    fig.update_layout(barmode='group', height=500, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)
st.divider()

#pertanyaan 4
st.header("Environmental Factors Affecting Rentals")

def plot_env_bar_plotly(tabel):
    valid_data = tabel.dropna(subset=['Rata_rata_Penyewaan'])
    if valid_data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False, x=0.5, y=0.5, xref='paper', yref='paper')
        fig.update_layout(height=380)
        return fig
    nilai = valid_data['Rata_rata_Penyewaan'].values
    idx_max = np.argmax(nilai)
    warna = [highlight1 if i == idx_max else grey for i in range(len(nilai))]
    fig = go.Figure(go.Bar(
        x=valid_data.index.astype(str), y=nilai,
        marker_color=warna,
        text=[f'{v:.0f}' for v in nilai],
        textposition='outside',
        hovertemplate='%{x}<br>Avg Rentals: %{y:.0f}<extra></extra>'
    ))
    fig.update_layout(height=380, margin=dict(t=20, b=20), showlegend=False)
    return fig


col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.subheader("Temperature")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_temp_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_temp_df['Rata_rata_Penyewaan'].idxmin())
    st.plotly_chart(plot_env_bar_plotly(tabel_temp_df), use_container_width=True)

with col2:
    st.subheader("Humidity")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_hum_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_hum_df['Rata_rata_Penyewaan'].idxmin())
    st.plotly_chart(plot_env_bar_plotly(tabel_hum_df), use_container_width=True)

with col3:
    st.subheader("Wind Speed")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_windspeed_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_windspeed_df['Rata_rata_Penyewaan'].idxmin())
    st.plotly_chart(plot_env_bar_plotly(tabel_windspeed_df), use_container_width=True)
st.divider()

#pertanyaan 5
st.subheader("Casual and Registered User Patterns by Day Type")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    - **Ideal Working Day:** Working day with favorable weather conditions.
    - **Harsh Working Day:** Working day with unfavorable or extreme weather conditions.
    """)
with col2:
    st.markdown("""
    - **Ideal Holiday:** Holiday with favorable weather conditions.
    - **Harsh Holiday:** Holiday with unfavorable or extreme weather conditions.
    """)

days_df['Day_Archetype'] = days_df.apply(klasifikasi_archetype, axis=1)

col1, col2 = st.columns([2,1], gap="large")
with col1:
    archetype_order = ['Harsh Holiday', 'Ideal Holiday', 'Harsh Working Day', 'Ideal Working Day']
    archetype_summary_df = days_df.groupby('Day_Archetype').agg(
        Rata_rata_Casual=('casual', 'mean'),
        Rata_rata_Registered=('registered', 'mean')
    ).round(1).reindex(archetype_order)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=archetype_summary_df.index, x=archetype_summary_df['Rata_rata_Casual'],
        name='Casual', orientation='h', marker_color=highlight2,
        text=archetype_summary_df['Rata_rata_Casual'], texttemplate='%{text:.0f}', textposition='outside',
        hovertemplate='%{y}<br>Avg Casual: %{x:.0f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        y=archetype_summary_df.index, x=archetype_summary_df['Rata_rata_Registered'],
        name='Registered', orientation='h', marker_color=highlight1,
        text=archetype_summary_df['Rata_rata_Registered'], texttemplate='%{text:.0f}', textposition='outside',
        hovertemplate='%{y}<br>Avg Registered: %{x:.0f}<extra></extra>'
    ))
    fig.update_layout(barmode='group', height=450, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Casual")
    st.metric("Highest Average Rentals", f"{archetype_summary_df['Rata_rata_Casual'].idxmax()}")
    st.metric("Lowest Average Rentals", f"{archetype_summary_df['Rata_rata_Casual'].idxmin()}")
    st.divider()

    st.subheader("Registered")
    st.metric("Highest Average Rentals", f"{archetype_summary_df['Rata_rata_Registered'].idxmax()}")
    st.metric("Lowest Average Rentals", f"{archetype_summary_df['Rata_rata_Registered'].idxmin()}")