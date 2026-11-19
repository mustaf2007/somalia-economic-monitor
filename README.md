# Somalia Economic Monitor

A free Streamlit dashboard for Somalia's economic, social and climate indicators.

## Public sources — no authentication
- World Bank Indicators API: GDP, growth, inflation, population, trade, employment and development indicators.
- NASA POWER: monthly rainfall, temperature and humidity estimates for a selected coordinate (default: Mogadishu).
- Our World in Data: selected public CSV datasets for life expectancy, child mortality, CO₂, electricity access and internet use.

No API keys, tokens, paid subscriptions or manual data uploads are required. Coverage and update frequency vary by indicator.

## Run locally
Python 3.10+ recommended.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Open https://share.streamlit.io/ and sign in with GitHub.
2. Select **mustaf2007/somalia-economic-monitor**.
3. Select branch **main** and main file **app.py**.
4. Click **Deploy**. No secrets need to be configured.

## Methodological notes
- Latest available observations may lag behind the current year.
- World Bank and OWID data are generally annual; NASA POWER provides monthly gridded estimates.
- NASA POWER point estimates are not national Somalia averages.
- OWID datasets may not contain Somalia observations for every indicator or year.
- Missing observations are not treated as zero.
- This independent analytical prototype is not an official Government of Somalia statistical publication.

## Sources
- https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api
- https://power.larc.nasa.gov/docs/services/api/
- https://ourworldindata.org/grapher
