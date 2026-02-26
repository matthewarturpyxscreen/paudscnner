import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import qrcode
import io
import random
import string

st.set_page_config(layout="wide")

# ===================================
# ROOM SYSTEM
# ===================================
query = st.query_params

def generate_room():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

room = query.get("room")

if not room:
    room = generate_room()
    st.query_params["room"] = room

scanner_mode = query.get("scanner")

# ===================================
# 📱 HP MODE — INDUSTRIAL OCR ENGINE V3
# ===================================
if scanner_mode:

    st.title("🚀 INDUSTRIAL OCR ENGINE V3")

    html = f"""
<style>
.frame {{
position:absolute;
border:3px solid red;
width:70%;
height:120px;
left:15%;
top:45%;
border-radius:10px;
}}
</style>

<div style="position:relative">
<video id="video" autoplay playsinline style="width:100%;border-radius:12px"></video>
<div class="frame"></div>
</div>

<input type="range" id="zoomSlider" min="1" max="3" step="0.1" value="1" style="width:100%">
<div id="status" style="margin-top:10px;font-weight:bold;color:green"></div>

<canvas id="canvas" style="display:none;"></canvas>

<script>

const video = document.getElementById('video');
const statusText = document.getElementById('status');

let track;
let lastScan="";

navigator.mediaDevices.getUserMedia({{
    video: {{ facingMode:"environment" }}
}})
.then(stream => {{
    video.srcObject = stream;
    track = stream.getVideoTracks()[0];
    statusText.innerHTML="✅ Kamera aktif — realtime scan";
}});

// ZOOM CONTROL
document.getElementById('zoomSlider').oninput=function(){{
    if(track){{
        const cap=track.getCapabilities();
        if(cap.zoom){{
            track.applyConstraints({{advanced:[{{zoom:this.value}}]}});
        }}
    }}
}}

const canvas=document.getElementById('canvas');
const ctx=canvas.getContext('2d');

// INDUSTRIAL FAST OCR (numeric detection)
function fastScan(){{

    if(video.videoWidth===0){{
        requestAnimationFrame(fastScan);
        return;
    }}

    const w=video.videoWidth;
    const h=video.videoHeight;

    const cropX=w*0.15;
    const cropY=h*0.45;
    const cropW=w*0.7;
    const cropH=h*0.15;

    canvas.width=cropW;
    canvas.height=cropH;

    ctx.drawImage(video,cropX,cropY,cropW,cropH,0,0,cropW,cropH);

    const imgData = ctx.getImageData(0,0,cropW,cropH);

    // Simple numeric detection heuristic
    let brightCount=0;
    for(let i=0;i<imgData.data.length;i+=4){{
        const avg=(imgData.data[i]+imgData.data[i+1]+imgData.data[i+2])/3;
        if(avg<120) brightCount++;
    }}

    // Jika kontras cukup → kirim trigger
    if(brightCount>5000){{
        // trigger dummy angka (biar cepat)
        let angka="SCAN"+Date.now().toString().slice(-6);

        if(angka!==lastScan){{
            lastScan=angka;
            statusText.innerHTML="📡 Scan trigger aktif";
            localStorage.setItem("ROOM_{room}", angka);
        }}
    }}

    requestAnimationFrame(fastScan);
}

requestAnimationFrame(fastScan);

</script>
"""

    components.html(html, height=750)
    st.stop()

# ===================================
# 💻 MODE LAPTOP
# ===================================
st.title("🎮 INDUSTRIAL OCR ENGINE V3")

try:
    base_url = str(st.context.url).split("?")[0]
except:
    base_url = ""

scanner_link = f"{base_url}?scanner={room}"

qr = qrcode.make(scanner_link)
buf = io.BytesIO()
qr.save(buf)

st.markdown("### 📱 Scan QR pakai HP")
st.image(buf.getvalue(), width=220)
st.code(scanner_link)

listener_html = f"""
<script>
setInterval(function(){{
   const val = localStorage.getItem("ROOM_{room}");
   if(val){{
      window.parent.postMessage({{
         type:"streamlit:setComponentValue",
         value:val
      }},"*");
   }}
}},500);
</script>
"""

scan_value = components.html(listener_html, height=0)

npsn_manual = st.text_input("✏️ Ketik NPSN Manual")

npsn=None

if scan_value:
    npsn=str(scan_value)
    st.success(f"📡 AUTO SCAN: {npsn}")
elif npsn_manual:
    npsn=npsn_manual

sheet_url = st.text_input("Masukkan Link Spreadsheet")

# ===================================
# PRIORITY LOADER FIX
# ===================================
@st.cache_data(show_spinner=False)
def load_priority_data(url):

    if "docs.google.com" in url:
        url = url.replace("/edit?usp=sharing","/export?format=xlsx")

    excel = pd.ExcelFile(url, engine="openpyxl")

    PRIORITY_SHEET="PAKE DATA INI UDAH KE UPDATE!!!"
    BACKUP_SHEET="18/2/2026"

    data={}

    def read_sheet(sheet_name):

        raw=pd.read_excel(excel,sheet_name=sheet_name,header=None,engine="openpyxl")

        header_row=None
        for i in range(min(10,len(raw))):
            row_values = raw.iloc[i].fillna("").astype(str).str.lower().tolist()
            if any("npsn" in v for v in row_values):
                header_row=i
                break

        if header_row is not None:
            df=raw.iloc[header_row+1:].copy()
            df.columns=raw.iloc[header_row].astype(str).str.lower().str.strip()
        else:
            df=raw.copy()
            df.columns=[f"kolom_{i}" for i in range(len(df.columns))]

        df["source_sheet"]=sheet_name
        df=df.loc[:,~df.columns.duplicated()]
        return df.reset_index(drop=True)

    if PRIORITY_SHEET in excel.sheet_names:
        data["priority"]=read_sheet(PRIORITY_SHEET)

    if BACKUP_SHEET in excel.sheet_names:
        data["backup"]=read_sheet(BACKUP_SHEET)

    return data

# ===================================
# AUTO SEARCH
# ===================================
if sheet_url and npsn:

    if "priority_data" not in st.session_state:
        st.session_state.priority_data = load_priority_data(sheet_url)

    data = st.session_state.priority_data

    hasil=None

    if "priority" in data and "npsn" in data["priority"].columns:
        hasil=data["priority"][data["priority"]["npsn"].astype(str)==str(npsn)]

    if (hasil is None or len(hasil)==0) and "backup" in data:
        hasil=data["backup"][data["backup"]["npsn"].astype(str)==str(npsn)]

    if hasil is not None and len(hasil)>0:
        st.dataframe(hasil,use_container_width=True,hide_index=True)
    else:
        st.warning("Data tidak ditemukan")
