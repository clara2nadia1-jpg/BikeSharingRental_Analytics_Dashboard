# Bike Sharing Rental Analytics Dashboard ✨

## Struktur Proyek
```
proyek_analisis_data/
├───dashboard/
│   ├───bike_sharing_hourly_clean.csv
│   └───dashboard.py
├───data/
│   ├───day.csv
│   └───hour.csv
├───notebook.ipynb
├───README.md
└───requirements.txt
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
```
cd dashboard
streamlit run dashboard.py
```
