from datetime import date
from io import BytesIO
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Somalia Economic Monitor", page_icon="📊", layout="wide")
WB = "https://api.worldbank.org/v2"
NASA = "https://power.larc.nasa.gov/api/temporal/monthly/point"
OWID = "https://ourworldindata.org/grapher/"
COUNTRIES = {"Somalia":"SOM","Kenya":"KEN","Ethiopia":"ETH","Djibouti":"DJI","Uganda":"UGA","Tanzania":"TZA"}
INDICATORS = {
"GDP (current US$)":("NY.GDP.MKTP.CD","US$"), "GDP growth (annual %)":("NY.GDP.MKTP.KD.ZG","%"),
"GDP per capita (current US$)":("NY.GDP.PCAP.CD","US$ per person"), "Inflation (annual %)":("FP.CPI.TOTL.ZG","%"),
"Population":("SP.POP.TOTL","people"), "Unemployment (% labour force)":("SL.UEM.TOTL.ZS","%"),
"Agriculture (% GDP)":("NV.AGR.TOTL.ZS","%"), "Industry (% GDP)":("NV.IND.TOTL.ZS","%"),
"Services (% GDP)":("NV.SRV.TOTL.ZS","%"), "Exports (% GDP)":("NE.EXP.GNFS.ZS","%"),
"Imports (% GDP)":("NE.IMP.GNFS.ZS","%"), "Trade (% GDP)":("NE.TRD.GNFS.ZS","%"),
"FDI net inflows (% GDP)":("BX.KLT.DINV.WD.GD.ZS","%"), "Remittances (% GDP)":("BX.TRF.PWKR.DT.GD.ZS","%"),
"Life expectancy":("SP.DYN.LE00.IN","years"), "Electricity access":("EG.ELC.ACCS.ZS","%"),
"Internet users":("IT.NET.USER.ZS","%"), "CO₂ emissions per capita":("EN.ATM.CO2E.PC","metric tons")}
OWID_DATASETS = {
"Life expectancy":("life-expectancy","Life expectancy (years)"),
"Child mortality":("child-mortality","Child mortality rate"),
"CO₂ emissions per capita":("annual-co2-emissions-per-country","Annual CO₂ emissions"),
"Electricity access":("access-to-electricity","Access to electricity (%)"),
"Internet use":("share-of-individuals-using-the-internet","Individuals using the internet (%)")}

st.markdown("""<style>
.block-container{padding-top:1.3rem}.hero{background:linear-gradient(110deg,#102b4e,#126b78);
padding:25px 28px;border-radius:15px;color:white;margin-bottom:16px}
.hero h1{color:white;margin:0;font-size:2rem}.hero p{color:#e5f2f4;margin:8px 0 0}
</style><div class="hero"><h1>Somalia Economic Monitor</h1>
<p>Economic, social and climate indicators — powered by open public data.</p></div>""",unsafe_allow_html=True)
st.caption("Open-data prototype · No API keys, accounts, tokens or paid subscriptions required")

def get_json(url, params=None, timeout=45):
    r=requests.get(url,params=params,timeout=timeout,headers={"User-Agent":"SomaliaEconomicMonitor/1.0"})
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=86400,show_spinner=False)
def wb_series(country, indicator):
    payload=get_json(f"{WB}/country/{country}/indicator/{indicator}",
                     {"format":"json","per_page":200,"date":"1960:2035"})
    if not isinstance(payload,list) or len(payload)<2 or not payload[1]:
        return pd.DataFrame(columns=["year","value"])
    rows=[{"year":int(x["date"]),"value":float(x["value"])} for x in payload[1] if x.get("value") is not None]
    return pd.DataFrame(rows).sort_values("year") if rows else pd.DataFrame(columns=["year","value"])

@st.cache_data(ttl=86400,show_spinner=False)
def nasa_series(lat,lon,start,end,param):
    p=get_json(NASA,{"parameters":param,"community":"AG","longitude":lon,"latitude":lat,
                     "start":start,"end":end,"format":"JSON"},timeout=60)
    vals=p["properties"]["parameter"][param]
    rows=[{"month":pd.to_datetime(str(k)+"01",format="%Y%m%d"),"value":float(v)}
          for k,v in vals.items() if not str(k).endswith("13") and v is not None and float(v)>-900]
    return pd.DataFrame(rows).sort_values("month") if rows else pd.DataFrame(columns=["month","value"])

@st.cache_data(ttl=86400,show_spinner=False)
def owid_csv(slug):
    r=requests.get(f"{OWID}{slug}.csv",timeout=60,headers={"User-Agent":"SomaliaEconomicMonitor/1.0"})
    r.raise_for_status()
    return pd.read_csv(BytesIO(r.content))

def latest(df):
    d=df.dropna(subset=["value"]).sort_values("year")
    return None if d.empty else d.iloc[-1]

with st.sidebar:
    st.header("Monitor settings")
    indicator=st.selectbox("Economic indicator",list(INDICATORS),index=1)
    countries=st.multiselect("Countries",list(COUNTRIES),default=["Somalia","Kenya","Ethiopia","Djibouti"])
    yr=date.today().year
    years=st.slider("Historical period",1960,yr,(2000,yr))
    if st.button("Refresh public data",use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Data cached for 24 hours. Latest observation years vary.")

st.subheader("Somalia at a glance")
kpis=[("GDP","NY.GDP.MKTP.CD","money"),("GDP growth","NY.GDP.MKTP.KD.ZG","pct"),
      ("Inflation","FP.CPI.TOTL.ZG","pct"),("Population","SP.POP.TOTL","pop")]
for col,(label,code,kind) in zip(st.columns(4),kpis):
    try:
        row=latest(wb_series("SOM",code))
        if row is None:
            col.metric(label,"No observation")
            col.caption("World Bank: no non-missing value returned for this indicator.")
        else:
            v=row["value"]
            display=("US$"+f"{v/1e9:,.2f}B") if kind=="money" else (f"{v/1e6:,.2f}M" if kind=="pop" else f"{v:,.2f}%")
            col.metric(label,display)
            col.caption(f"Latest observation: {int(row['year'])} · World Bank")
    except Exception as e:
        col.metric(label,"Unavailable")
        col.caption("World Bank request failed. Refresh or try again later.")

tabs=st.tabs(["Economic monitor","Climate monitor","Development indicators","Sources & methodology"])
with tabs[0]:
    code,unit=INDICATORS[indicator]
    st.subheader(indicator)
    st.caption(f"World Bank indicator: {code} · Unit: {unit}")
    frames=[]
    with st.spinner("Loading World Bank observations..."):
        for country in countries:
            try:
                d=wb_series(COUNTRIES[country],code)
                if not d.empty:
                    d=d[d.year.between(*years)].copy()
                    d["Country"]=country
                    frames.append(d)
            except Exception as e: st.warning(f"{country}: {e}")
    if frames:
        data=pd.concat(frames,ignore_index=True)
        fig=px.line(data,x="year",y="value",color="Country",markers=True,
                     labels={"year":"Observation year","value":unit,"Country":"Country"},
                     hover_data={"year":True,"value":":.3f","Country":True})
        fig.update_layout(template="plotly_white",height=450,legend_title="Country",
                          margin=dict(l=15,r=15,t=25,b=15),hovermode="x unified")
        st.plotly_chart(fig,use_container_width=True)
        latest_by_country=(data.dropna(subset=["value"]).sort_values("year")
                           .groupby("Country",as_index=False).tail(1)
                           .sort_values("Country"))
        st.caption("Latest available observation by selected country (years may differ):")
        st.dataframe(latest_by_country[["Country","year","value"]].rename(
            columns={"year":"Latest year","value":f"Latest value ({unit})"}),
            use_container_width=True,hide_index=True)
        st.caption(f"Source: World Bank Indicators API · Indicator code: {code} · Retrieved live from the public API (cached for up to 24 hours).")
        st.dataframe(data.sort_values(["Country","year"],ascending=[True,False]),use_container_width=True,hide_index=True)
        st.download_button("Download selected data (CSV)",data.to_csv(index=False).encode("utf-8"),
                           "somalia_economic_monitor.csv","text/csv")
    else: st.info("No observations returned. Try another indicator or country.")

with tabs[1]:
    st.subheader("Climate monitor — NASA POWER")
    st.caption("Monthly gridded estimates for a selected point, not a national Somalia average.")
    c1,c2=st.columns(2)
    lat=c1.number_input("Latitude",value=2.0469,min_value=-90.0,max_value=90.0,format="%.4f")
    lon=c2.number_input("Longitude",value=45.3182,min_value=-180.0,max_value=180.0,format="%.4f")
    start=st.slider("Start year",1981,yr,2015)
    end=st.slider("End year",start,yr,yr)
    params={"Precipitation (mm/month)":"PRECTOTCORR","Mean temperature (°C)":"T2M",
            "Maximum temperature (°C)":"T2M_MAX","Minimum temperature (°C)":"T2M_MIN",
            "Relative humidity (%)":"RH2M"}
    variable=st.selectbox("Climate variable",list(params))
    if st.button("Load climate observations"):
        try:
            d=nasa_series(lat,lon,start,end,params[variable])
            if d.empty: st.info("No climate observations returned.")
            else:
                fig=px.line(d,x="month",y="value",labels={"month":"Month","value":variable})
                fig.update_layout(template="plotly_white",height=420)
                st.plotly_chart(fig,use_container_width=True)
                st.dataframe(d.tail(24),use_container_width=True,hide_index=True)
                st.download_button("Download climate data (CSV)",d.to_csv(index=False).encode("utf-8"),
                                   "nasa_power_climate.csv","text/csv")
        except Exception as e: st.error(f"NASA POWER request failed: {e}")

with tabs[2]:
    st.subheader("Development indicators — Our World in Data")
    label=st.selectbox("Development indicator",list(OWID_DATASETS))
    slug,ylabel=OWID_DATASETS[label]
    if st.button("Load development data"):
        try:
            d=owid_csv(slug)
            if not {"Entity","Year"}.issubset(d.columns): st.error("Unexpected dataset structure.")
            else:
                candidates=[x for x in d.columns if x not in ("Entity","Code","Year")]
                if not candidates: st.error("No indicator value column found.")
                else:
                    value_col=candidates[0]
                    som=d[(d.Entity.str.lower()=="somalia") & d.Year.notna()].copy()
                    if som.empty: st.info("This dataset currently has no Somalia observations.")
                    else:
                        som=som.rename(columns={"Year":"year",value_col:"value"})
                        som["year"]=som.year.astype(int)
                        fig=px.line(som,x="year",y="value",markers=True,labels={"year":"Year","value":ylabel})
                        fig.update_layout(template="plotly_white",height=420)
                        st.plotly_chart(fig,use_container_width=True)
                        st.write(f"Latest observation: {som.year.max()}")
                        st.dataframe(som.sort_values("year",ascending=False),use_container_width=True,hide_index=True)
                        st.download_button("Download Somalia data (CSV)",som.to_csv(index=False).encode("utf-8"),
                                           f"owid_{slug}_somalia.csv","text/csv")
        except Exception as e: st.error(f"OWID dataset could not be loaded: {e}")
    st.dataframe(pd.DataFrame([{"Indicator":k,"Dataset":v[0],"Measure":v[1]} for k,v in OWID_DATASETS.items()]),
                 use_container_width=True,hide_index=True)

with tabs[3]:
    st.subheader("Data sources")
    sources=pd.DataFrame([
    {"Source":"World Bank Indicators API","Coverage":"GDP, inflation, population, trade, labour and development","Access":"Public API; no key","Documentation":"https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api"},
    {"Source":"NASA POWER","Coverage":"Monthly precipitation, temperature and humidity at point locations","Access":"Public API; no key","Documentation":"https://power.larc.nasa.gov/docs/services/api/"},
    {"Source":"Our World in Data","Coverage":"Selected health, energy, emissions and development datasets","Access":"Public CSV; no key","Documentation":"https://ourworldindata.org/grapher"}])
    st.dataframe(sources,use_container_width=True,hide_index=True)
    st.subheader("Methodology and limitations")
    st.markdown("""
- All integrations use public endpoints; no credentials or secrets are needed.
- Annual and monthly series have different frequencies and publication lags.
- Missing values are not converted to zero or interpolated.
- NASA POWER represents a selected coordinate, not a national climate average.
- OWID coverage varies by dataset and may not include Somalia for every year.
- Check definitions, units and reference periods before cross-country comparisons.
- This independent dashboard is not an official Government of Somalia statistical publication.
""")
st.divider()
st.caption("Somalia Economic Monitor · Version 1.1 · Open public data · No authentication required")
