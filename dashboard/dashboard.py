import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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
min_date = hours_df['dteday'].min()
max_date = hours_df['dteday'].max()
date_range = st.sidebar.date_input(
    "Choose Data Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

season_choice = list(season_label.values())
selected_seasons = st.sidebar.multiselect(
    "Select Seasons",
    options = season_choice,
    default = season_choice
)

filtered_hours_df = hours_df[(hours_df['dteday']>=pd.to_datetime(start_date)) & (hours_df['dteday']<=pd.to_datetime(end_date)) & (hours_df['season'].map(season_label).isin(selected_seasons))].copy()
if filtered_hours_df.empty:
    st.sidebar.error("No data is available for the selected date range and seasons.")
    st.warning("No data is available for the selected date range and seasons.Please choose a different date range or season.")
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
growth = round((total_2012 - total_2011) / total_2011 * 100, 1)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rentals (2011-2012)", f"{total_rentals:,.0f}")
col2.metric("Total Casual Users", f"{total_casual:,.0f}")
col3.metric("Total Registered Users", f"{total_registered:,.0f}")
col4.metric("Rental Growth", f"+{growth}%")
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
fig, ax = plt.subplots(figsize=(12, 5))
for hari in daftar_hari_aktif:
    data_hari = subset_df[subset_df['Hari'] == hari]
    if hari == hari_tertinggi:
        ax.plot(data_hari['Jam'], data_hari['Rata-rata Penyewaan'], label=hari,
                linewidth=2.5, color=palet[hari], alpha=1.0, zorder=3)
    else:
        ax.plot(data_hari['Jam'], data_hari['Rata-rata Penyewaan'], label=hari,
                linewidth=1.6, color=palet[hari], alpha=0.7, zorder=2)
ax.scatter(baris_max['Jam'], baris_max['Rata-rata Penyewaan'], color='black', s=70, zorder=5, label='Titik Tertinggi')
ax.scatter(baris_min['Jam'], baris_min['Rata-rata Penyewaan'], color='black', marker='x', s=70, zorder=5, label='Titik Terendah')
ax.margins(x=0)
ax.set_xticks(range(0, 24, 2))
ax.legend(frameon=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig)

st.subheader("Daily Rental Ranking")
hari_tertinggi_all = rata2_per_hari_df.loc[rata2_per_hari_df['Rata-rata Penyewaan'].idxmax(), 'Hari']
warna_bar = [highlight1 if h == hari_tertinggi_all else grey for h in rata2_per_hari_df['Hari']]

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(rata2_per_hari_df['Hari'], rata2_per_hari_df['Rata-rata Penyewaan'], color=warna_bar)
for bar in bars:
    tinggi = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2, tinggi + 30, f'{tinggi:.0f}', ha='center', fontsize=9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig)

with st.expander("View Hourly Rental Data"):
    table = hari_jam_sewa_df.copy()
    table = table.rename(columns={'Hari': 'Day', 'Jam': 'Hour', 'Rata-rata Penyewaan': 'Average Rentals'})
    st.dataframe(table.style.format({'Average Rentals': '{:.0f}'}), hide_index=True, use_container_width=True)

st.divider()

#pertanyaan 2
st.header("Casual vs Registered Rental Pattern")
musim_tertinggi = tabel_dominasi_df.loc[tabel_dominasi_df['Total_Rental'].idxmin(), 'Musim']
musim_terendah = tabel_dominasi_df.loc[tabel_dominasi_df['Total_Rental'].idxmax(), 'Musim']

col1, col2 = st.columns(2)
col1.metric("Highest Rental Volume", musim_tertinggi)
col2.metric("Lowest Rental Volume", musim_terendah)

warna_tahun = {'2011': highlight2, '2012': highlight1}

col1, col2 = st.columns(2)
with col1:
    fig, ax = plt.subplots(figsize=(7, 5))
    for tahun in ['2011', '2012']:
        data_tahun = tren_bulanan_df[tren_bulanan_df['Tahun'] == tahun].sort_values('Bulan')
        if data_tahun.empty:
            continue
        ax.plot(data_tahun['Bulan'], data_tahun['Proporsi_Casual (%)'], linewidth=2.2, color=warna_tahun[tahun], marker='o', markersize=4)
        ax.annotate(tahun, xy=(data_tahun['Bulan'].iloc[-1], data_tahun['Proporsi_Casual (%)'].iloc[-1]),
                    xytext=(8, 0), textcoords='offset points', color=warna_tahun[tahun], fontsize=10, fontweight='bold', va='center')
    ax.set_title('Casual Rental Proportion Trend by Month', fontsize=13, pad=15)
    ax.tick_params(axis='x', rotation=45)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(tabel_dominasi_df))
    width = 0.35
    ax.bar(x - width/2, tabel_dominasi_df['Total_Casual'], width, label='Casual', color=highlight2)
    ax.bar(x + width/2, tabel_dominasi_df['Total_Registered'], width, label='Registered', color=highlight1)
    ax.set_xticks(x)
    ax.set_xticklabels(tabel_dominasi_df['Musim'])
    ax.set_title('Rental Volume by Season', fontsize=13, pad=15)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x/1000)}k' if x >= 1000 else f'{x:.0f}'))
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Monthly Rental Volume Trend")
fig, ax = plt.subplots(figsize=(14, 5))
for tahun in ['2011', '2012']:
    data_tahun = tren_bulanan_df[tren_bulanan_df['Tahun'] == tahun].sort_values('Bulan')
    if data_tahun.empty:
        continue
    ax.plot(data_tahun['Bulan'], data_tahun['Total_Cnt'], linewidth=2.2, color=warna_tahun[tahun], marker='o', markersize=4)
    ax.annotate(tahun, xy=(data_tahun['Bulan'].iloc[-1], data_tahun['Total_Cnt'].iloc[-1]),
                xytext=(8, 0), textcoords='offset points', color=warna_tahun[tahun], fontsize=10, fontweight='bold', va='center')
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x/1000)}k'))
ax.tick_params(axis='x')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
st.pyplot(fig)
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
    fig, ax = plt.subplots(figsize=(9, 6))
    x = np.arange(len(weather_penyewa_df))
    width = 0.35
    bars_c = ax.bar(x - width/2, weather_penyewa_df['Rata-rata Casual'], width, label='Casual', color=highlight2)
    bars_r = ax.bar(x + width/2, weather_penyewa_df['Rata-rata Registered'], width, label='Registered', color=highlight1)
    for bars in [bars_c, bars_r]:
        for bar in bars:
            tinggi = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, tinggi + 3, f'{tinggi:.0f}', ha='center', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(weather_penyewa_df['Kondisi Cuaca'])
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
st.divider()

#pertanyaan 4
st.header("Environmental Factors Affecting Rentals")

def plot_env_bar(ax, tabel):
    nilai = tabel['Rata_rata_Penyewaan'].values
    idx_max = np.argmax(nilai)
    warna = [highlight1 if i == idx_max else grey for i in range(len(nilai))]
    bars = ax.bar(tabel.index, nilai, color=warna)
    for bar in bars:
        tinggi = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, tinggi + 5, f'{tinggi:.0f}', ha='center', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.subheader("Temperature")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_temp_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_temp_df['Rata_rata_Penyewaan'].idxmin())
    fig, ax = plt.subplots(figsize=(6, 5))
    plot_env_bar(ax, tabel_temp_df)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("Humidity")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_hum_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_hum_df['Rata_rata_Penyewaan'].idxmin())
    fig, ax = plt.subplots(figsize=(6, 5))
    plot_env_bar(ax, tabel_hum_df)
    plt.tight_layout()
    st.pyplot(fig)

with col3:
    st.subheader("Wind Speed")
    widget1, widget2 = st.columns(2)
    widget1.metric("Highest Rentals", tabel_windspeed_df['Rata_rata_Penyewaan'].idxmax())
    widget2.metric("Lowest Rentals", tabel_windspeed_df['Rata_rata_Penyewaan'].idxmin())
    fig, ax = plt.subplots(figsize=(6, 5))
    plot_env_bar(ax, tabel_windspeed_df)
    plt.tight_layout()
    st.pyplot(fig)
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

    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(archetype_summary_df))
    height = 0.35

    bars_c = ax.barh(y - height/2, archetype_summary_df['Rata_rata_Casual'], height, label='Casual', color=highlight2)
    bars_r = ax.barh(y + height/2, archetype_summary_df['Rata_rata_Registered'], height, label='Registered', color=highlight1)

    for bars in [bars_c, bars_r]:
        for bar in bars:
            lebar = bar.get_width()
            ax.text(lebar + 40, bar.get_y() + bar.get_height()/2, f'{lebar:.0f}', va='center', fontsize=9)

    ax.set_yticks(y)
    ax.set_yticklabels(archetype_summary_df.index)
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("Casual")
    st.metric("Highest Average Rentals", f"{archetype_summary_df['Rata_rata_Casual'].idxmax()}")
    st.metric("Lowest Average Rentals", f"{archetype_summary_df['Rata_rata_Casual'].idxmin()}")
    st.divider()

    st.subheader("Registered")
    st.metric("Highest Average Rentals", f"{archetype_summary_df['Rata_rata_Registered'].idxmax()}")
    st.metric("Lowest Average Rentals", f"{archetype_summary_df['Rata_rata_Registered'].idxmin()}")