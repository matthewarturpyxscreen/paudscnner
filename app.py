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
# 📱 MODE HP — AUTO OPEN CAMERA + OCR
# ===================================
if scanner_mode:

    st.title("📸 Scanner HP Aktif")

    camera_html = f"""
    <video id="video" autoplay playsinline style="width:100%"></video>
    <canvas id="canvas" style="display:none"></canvas>

    <script src="https://cdn.jsdelivr.net/npm/tesseract.js@4/dist/tesseract.min.js"></script>

    const video = document.getElementById('video');

    // 🔥 AUTO OPEN CAMERA
    navigator.mediaDevices.getUserMedia({{
        video:{{facingMode:"environment"}}
    }}).then(stream=>{{
        video.srcObject = stream;
    }});

    function kirim(val){{
        const angka = val.replace(/[^0-9]/g,'');
        if(angka.length>0){{
            localStorage.setItem("ROOM_{room}", angka);
        }}
    }}

    // 🔥 AUTO TAKE PHOTO SETIAP 2 DETIK
    setInterval(function(){{
        const canvas = document.getElementById('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video,0,0);

        Tesseract.recognize(canvas,'eng').then(({{
            data:{{text}}
        }})=>{{
            kirim(text);
        }});
    }},2000);
    </script>
    """

    components.html(camera_html, height=500)
    st.stop()

# ===================================
# 💻 MODE LAPTOP
# ===================================
st.title("🎮 AUTO CAMERA NPSN OCR SCANNER")

# ===================================
# QR CODE UNTUK HP
# ===================================
try:
    base_url = str(st.context.url).split("?")[0]
except:
    base_url = ""

scanner_link = f"{base_url}?scanner={room}"

qr = qrcode.make(scanner_link)
buf = io.BytesIO()
qr.save(buf)

st.markdown("### 📱 Scan QR ini pakai HP")
st.image(buf.getvalue(), width=220)
st.code(scanner_link)

# ===================================
# LISTENER REALTIME
# ===================================
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

# ===================================
# INPUT MANUAL
# ===================================
npsn_manual = st.text_input("✏️ Ketik NPSN Manual")

npsn = None

if scan_value:
    npsn = str(scan_value)
    st.success(f"📡 NPSN dari HP: {npsn}")

elif npsn_manual:
    npsn = npsn_manual

# ===================================
# PRIORITY SEARCH ENGINE
# ===================================
sheet_url = st.text_input("Masukkan Link Spreadsheet")

@st.cache_data(show_spinner=False)
def load_priority_data(url):

    if "docs.google.com" in url:
        url = url.replace("/edit?usp=sharing","/export?format=xlsx")

    excel = pd.ExcelFile(url)

    PRIORITY_SHEET="PAKE DATA INI UDAH KE UPDATE!!!"
    BACKUP_SHEET="18/2/2026"

    data={}

    def read_sheet(sheet_name):
        raw=pd.read_excel(excel,sheet_name=sheet_name,header=None)

        header_row=None
        for i in range(min(10,len(raw))):
            row_values=raw.iloc[i].astype(str).str.lower().tolist()
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
    source=None

    if "priority" in data and "npsn" in data["priority"].columns:
        temp=data["priority"][data["priority"]["npsn"].astype(str)==str(npsn)]
        if len(temp)>0:
            hasil=temp
            source="priority"

    if hasil is None and "backup" in data and "npsn" in data["backup"].columns:
        temp=data["backup"][data["backup"]["npsn"].astype(str)==str(npsn)]
        if len(temp)>0:
            hasil=temp
            source="backup"

    if hasil is not None:

        if source=="priority":
            st.success("🟢 DATA UTAMA TERDETEKSI")

        if source=="backup":
            st.info("🔵 DATA BACKUP TERDETEKSI")

        st.dataframe(hasil,use_container_width=True,hide_index=True)

    else:
        st.warning("Data tidak ditemukan")
