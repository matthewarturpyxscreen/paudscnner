import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

st.title("🎓 NPSN Scanner — Laptop Mode (Super Stabil)")

# =========================
# CAMERA SCANNER DI LAPTOP
# =========================
html = """
<style>
.frame{
position:absolute;
border:3px solid red;
width:70%;
height:120px;
left:15%;
top:45%;
border-radius:12px;
}
</style>

<div style="position:relative">
<video id="video" autoplay playsinline style="width:100%"></video>
<div class="frame"></div>
</div>

<input id="hiddenInput" />

<script>
const video=document.getElementById("video");

navigator.mediaDevices.getUserMedia({
 video:true
}).then(stream=>{
 video.srcObject=stream;
});

document.getElementById("hiddenInput").addEventListener("change",function(){
 window.parent.postMessage({
   type:"streamlit:setComponentValue",
   value:this.value
 },"*");
});
</script>
"""

scan_value = components.html(html, height=420)

manual = st.text_input("Input NPSN")

npsn=None
if isinstance(scan_value,str):
    npsn=scan_value
elif manual:
    npsn=manual

sheet_url = st.text_input("Link Spreadsheet")

# =========================
# DATA LOADER
# =========================
@st.cache_data
def load_data(url):

    if "docs.google.com" in url:
        url=url.split("/edit")[0]+"/export?format=xlsx"

    excel=pd.ExcelFile(url)

    def read_sheet(name):
        raw=pd.read_excel(excel,sheet_name=name,header=None)

        header_row=None
        for i in range(min(20,len(raw))):
            vals=raw.iloc[i].fillna("").astype(str).str.lower()
            if "npsn" in " ".join(vals):
                header_row=i
                break

        df=raw.iloc[header_row+1:].copy()
        df.columns=pd.Series(raw.iloc[header_row]).fillna("").astype(str).str.lower()
        df=df.loc[:,~df.columns.duplicated()]
        return df.reset_index(drop=True)

    data={}

    if "PAKE DATA INI UDAH KE UPDATE!!!" in excel.sheet_names:
        data["priority"]=read_sheet("PAKE DATA INI UDAH KE UPDATE!!!")

    if "18/2/2026" in excel.sheet_names:
        data["backup"]=read_sheet("18/2/2026")

    return data

# =========================
# SEARCH
# =========================
if sheet_url and npsn:

    data=load_data(sheet_url)

    hasil=None

    if "priority" in data:
        hasil=data["priority"][
            data["priority"]["npsn"].astype(str).str.zfill(8)==str(npsn).zfill(8)
        ]

    if (hasil is None or len(hasil)==0) and "backup" in data:
        hasil=data["backup"][
            data["backup"]["npsn"].astype(str).str.zfill(8)==str(npsn).zfill(8)
        ]

    if hasil is not None and len(hasil)>0:
        st.dataframe(hasil,use_container_width=True,hide_index=True)
    else:
        st.warning("Data tidak ditemukan")
