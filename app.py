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

# ======================================
# 📱 HP MODE — TAKE PHOTO CACHE OCR
# ======================================
if scanner_mode:

    st.title("📸 PRIORITY TAKE PHOTO CACHE SCANNER")

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

<button id="snap" style="width:100%;padding:15px;margin-top:10px;font-size:18px">
📸 TAKE PHOTO
</button>

<div id="status"></div>

<canvas id="photo" style="display:none;"></canvas>
<canvas id="crop" style="display:none;"></canvas>

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

 const photo=document.getElementById("photo");
 const crop=document.getElementById("crop");

 const ctxPhoto=photo.getContext("2d");
 const ctxCrop=crop.getContext("2d");

 const w=video.videoWidth;
 const h=video.videoHeight;

 // =====================
 // STEP 1: SIMPAN FOTO FULL
 // =====================
 photo.width=w;
 photo.height=h;
 ctxPhoto.drawImage(video,0,0,w,h);

 // =====================
 // STEP 2: CROP AREA PRIORITY
 // =====================
 const cropX=w*0.15;
 const cropY=h*0.45;
 const cropW=w*0.7;
 const cropH=h*0.15;

 crop.width=cropW;
 crop.height=cropH;

 ctxCrop.drawImage(photo,cropX,cropY,cropW,cropH,0,0,cropW,cropH);

 status.innerHTML="🔎 Membaca angka dari foto...";

 // =====================
 // STEP 3: OCR DARI CACHE FOTO
 // =====================
 const result=await Tesseract.recognize(crop,'eng');

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

listener="""
<script>
setInterval(function(){
 const val=localStorage.getItem("ROOM___ROOM__");
 if(val){
  window.parent.postMessage({
   type:"streamlit:setComponentValue",
   value:val
  },"*");
 }
},500);
</script>
"""

listener=listener.replace("__ROOM__",room)
scan_value=components.html(listener,height=0)

manual=st.text_input("✏️ Input NPSN Manual")

npsn=None
if isinstance(scan_value,str) and scan_value.strip().isdigit():
    npsn=scan_value.strip()
    st.success("📡 Dari HP: "+npsn)
elif manual:
    npsn=manual.strip()

sheet_url=st.text_input("Link Spreadsheet")

# ======================================
# PRIORITY LOADER (ANTI NaN JSON ERROR)
# ======================================
@st.cache_data(show_spinner=False)
def load_priority_data(url):

    if "docs.google.com" in url:
        url=url.split("/edit")[0]+"/export?format=xlsx"

    excel=pd.ExcelFile(url,engine="openpyxl")

    PRIORITY_SHEET="PAKE DATA INI UDAH KE UPDATE!!!"
    BACKUP_SHEET="18/2/2026"

    def read_sheet(sheet_name):

        raw=pd.read_excel(excel,sheet_name=sheet_name,header=None)

        header_row=None

        for i in range(min(20,len(raw))):
            vals=raw.iloc[i].fillna("").astype(str).str.lower()
            if "npsn" in " ".join(vals):
                header_row=i
                break

        df=raw.iloc[header_row+1:].copy()
        df.columns=raw.iloc[header_row]

        # 🔥 FIX ERROR JSON NaN
        df.columns = (
            pd.Series(df.columns)
            .fillna("")
            .astype(str)
            .str.lower()
        )

        df=df.loc[:,~df.columns.duplicated()]
        df["source_sheet"]=sheet_name

        return df.reset_index(drop=True)

    data={}

    if PRIORITY_SHEET in excel.sheet_names:
        data["priority"]=read_sheet(PRIORITY_SHEET)

    if BACKUP_SHEET in excel.sheet_names:
        data["backup"]=read_sheet(BACKUP_SHEET)

    return data

# ======================================
# SEARCH
# ======================================
if sheet_url and npsn:

    if "priority_data" not in st.session_state:
        st.session_state.priority_data=load_priority_data(sheet_url)

    data=st.session_state.priority_data

    hasil=None
    source=None

    if "priority" in data and "npsn" in data["priority"].columns:

        temp=data["priority"][
            data["priority"]["npsn"]
            .astype(str)
            .str.replace(r"\D","",regex=True)
            .str.zfill(8)
            ==
            str(npsn).zfill(8)
        ]

        if len(temp)>0:
            hasil=temp
            source="priority"

    if hasil is None and "backup" in data and "npsn" in data["backup"].columns:

        temp=data["backup"][
            data["backup"]["npsn"]
            .astype(str)
            .str.replace(r"\D","",regex=True)
            .str.zfill(8)
            ==
            str(npsn).zfill(8)
        ]

        if len(temp)>0:
            hasil=temp
            source="backup"

    if hasil is not None:

        if source=="priority":
            st.success("🟢 Ditemukan di UPDATE")

        if source=="backup":
            st.info("🔵 Ditemukan di BACKUP")

        st.dataframe(hasil,use_container_width=True,hide_index=True)

    else:
        st.warning("Data tidak ditemukan")
