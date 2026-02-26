import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import qrcode
import io
import random
import string

st.set_page_config(layout="wide")

# ===============================
# ROOM SYSTEM
# ===============================
query = st.query_params

def generate_room():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

room = query.get("room")

if not room:
    room = generate_room()
    st.query_params["room"] = room

scanner_mode = query.get("scanner")

# ===============================
# 📱 MODE HP — TAKE PHOTO OCR
# ===============================
if scanner_mode:

    st.title("📸 TAKE PHOTO PRIORITY SCANNER")

    html = """
<style>
.frame{
position:absolute;
border:3px solid red;
width:70%;
height:110px;
left:15%;
top:45%;
border-radius:10px;
}
</style>

<div style="position:relative">
<video id="video" autoplay playsinline style="width:100%"></video>
<div class="frame"></div>
</div>

<button id="snap" style="width:100%;padding:15px;margin-top:10px;font-size:18px">
📸 TAKE PHOTO
</button>

<div id="status"></div>

<canvas id="canvas" style="display:none;"></canvas>

<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>

<script>

const video=document.getElementById("video");
const status=document.getElementById("status");

navigator.mediaDevices.getUserMedia({
 video:{facingMode:"environment"}
}).then(stream=>{
 video.srcObject=stream;
 status.innerHTML="✅ Kamera siap";
});

document.getElementById("snap").onclick=async function(){

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

 status.innerHTML="🔎 Membaca angka...";

 const result=await Tesseract.recognize(canvas,'eng');

 let angka=(result.data.text||"").replace(/[^0-9]/g,'');

 if(angka.length>0){
   localStorage.setItem("ROOM___ROOM__",angka);
   status.innerHTML="📡 Terkirim: "+angka;
 }
 else{
   status.innerHTML="⚠️ Angka tidak terbaca";
 }
}
</script>
"""

    html = html.replace("__ROOM__",room)
    components.html(html,height=700)
    st.stop()

# ===============================
# 💻 MODE LAPTOP
# ===============================
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

listener=f"""
<script>
setInterval(function(){
 const val=localStorage.getItem("ROOM_{room}");
 if(val){
  window.parent.postMessage({{
   type:"streamlit:setComponentValue",
   value:val
  }},"*");
 }
},500);
</script>
"""

scan_value=components.html(listener,height=0)

manual=st.text_input("✏️ Input NPSN Manual")

npsn=None
if scan_value:
    npsn=str(scan_value)
    st.success("📡 Dari HP: "+npsn)
elif manual:
    npsn=manual

sheet_url=st.text_input("Link Spreadsheet")

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_priority_data(url):

    if "docs.google.com" in url:
        url=url.replace("/edit?usp=sharing","/export?format=xlsx")

    excel=pd.ExcelFile(url,engine="openpyxl")

    df=pd.read_excel(excel,header=0,engine="openpyxl")
    df.columns=df.columns.str.lower()

    return df

# ===============================
# SEARCH
# ===============================
if sheet_url and npsn:

    df=load_priority_data(sheet_url)

    if "npsn" in df.columns:

        hasil=df[
            df["npsn"]
            .astype(str)
            .str.replace(r"\D","",regex=True)
            .str.zfill(8)
            ==
            str(npsn).zfill(8)
        ]

        if len(hasil)>0:
            st.dataframe(hasil,use_container_width=True,hide_index=True)
        else:
            st.warning("Data tidak ditemukan")
