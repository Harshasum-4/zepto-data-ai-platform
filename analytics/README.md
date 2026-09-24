# Titanic Analytics Pipeline

Run `python -m pip install -r requirements.txt` and then `python run_analytics.py`.
The first run downloads the Titanic data once via Seaborn, commits `titanic.csv` as its offline fallback, then writes the EDA charts, model metrics, saved full pipeline and required written interpretations to `analysis_report.md` and `artifacts/`.
