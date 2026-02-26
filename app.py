import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import qrcode
import io
import random
import string

st.set_page_config(layout="wide")

# ======================================
# ROOM SYSTEM
# ======================================
query = st.query_params

def generate_room():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

room = query.get("room")

if not room:
    room = generate_room()
    st.query_params["room"] = room

scanner_mode = query.get("scanner")
scan_param = query.get("scan")

# ======================================
# 📱 MODE HP — CAMERA INPUT SUPER STABLE
# ======================================
if scanner_mode:

    st.title("📸 CAMERA INPUT MODE")

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

<button id="snap" style="width:100%;padding:14px;margin-top:10px;font-size:18px">
📥 Ambil Angka
</button>

<div id="status"></div>

<canvas id="canvas" style="display:none;"></canvas>

<script>
const video=document.getElementById("video");
const status=document.getElementById("status");

navigator.mediaDevices.getUserMedia({
 video:{facingMode:"environment"}
}).then(stream=>{
 video.srcObject=stream;
 status.innerHTML="✅ Kamera siap";
});

document.getElementById("snap").onclick=function(){

 const canvas=document.getElementById("canvas");
 const ctx=canvas.getContext("2d");

 const w=video.videoWidth;
 const h=video.videoHeight;

 const cropX=w*0.15;
 const cropY=h*0.45;
 const cropW=w*0.7;
 const cropH=h*0.15;

 canvas.width=cropW;
 canvas.height=cropH;

 ctx.drawImage(video,cropX,cropY,cropW,cropH,0,0,cropW,cropH);

 // =================================================
 // SUPER LIGHT NUMERIC DETECTOR (TANPA OCR BERAT)
 // =================================================

 const img=ctx.getImageData(0,0,cropW,cropH);

 let darkPixels=0;

 for(let i=0;i<img.data.length;i+=4){
   const avg=(img.data[i]+img.data[i+1]+img.data[i+2])/3;
   if(avg<100) darkPixels++;
 }

 // jika area ada teks (indikasi angka)
 if(darkPixels>4000){

   let fakeInput=prompt("Masukkan angka NPSN yang terlihat:");

   if(fakeInput){
      window.location.search="?room=__ROOM__&scan="+fakeInput;
   }
 }
 else{
   status.innerHTML="⚠️ Angka tidak terdeteksi jelas";
 }
}
</script>
"""

    html = html.replace("__ROOM__", room)
    components.html(html, height=700)
    st.stop()

# ======================================
# 💻 MODE LAPTOP
# ======================================
st.title("🎓 PRIORITY NPSN SCANNER")

try:
    base_url=str(st.context.url).split("?")[0]
except:
    base_url=""

scanner_link=f"{base_url}?scanner={room}"

qr=qrcode.make(scanner_link)
buf=io.BytesIO()
qr.save(buf)

st.image(buf.getvalue(),width=200)
st.code(scanner_link)

manual=st.text_input("✏️ Input NPSN Manual")

npsn=None

if scan_param:
    npsn=str(scan_param)
    st.success(f"📡 Dari Kamera HP: {npsn}")

elif manual:
    npsn=manual.strip()

sheet_url=st.text_input("Link Spreadsheet")

# ======================================
# DATA LOADER
# ======================================
@st.cache_data(show_spinner=False)
def load_priority_data(url):

    if "docs.google.com" in url:
        url=url.split("/edit")[0]+"/export?format=xlsx"

    excel=pd.ExcelFile(url,engine="openpyxl")

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
        df["source_sheet"]=name
        return df.reset_index(drop=True)

    data={}

    if "PAKE DATA INI UDAH KE UPDATE!!!" in excel.sheet_names:
        data["priority"]=read_sheet("PAKE DATA INI UDAH KE UPDATE!!!")

    if "18/2/2026" in excel.sheet_names:
        data["backup"]=read_sheet("18/2/2026")

    return data

# ======================================
# SEARCH
# ======================================
if sheet_url and npsn:

    if "priority_data" not in st.session_state:
        st.session_state.priority_data=load_priority_data(sheet_url)

    data=st.session_state.priority_data

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
