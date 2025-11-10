import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials
import datetime

ANNOTATOR_NAME = "Bu Jiphie"

# =============================
# CONFIGURASI GOOGLE SHEETS
# =============================

SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Sentimen_Kabinet_Labeling"  # ubah ke nama Google Sheet kamu
CREDS_FILE = "sanguine-air-477810-q8-oth-anotator.json" 

@st.cache_resource
def connect_gsheet():
    # Baca langsung file kredensial JSON
    with open("sanguine-air-477810-q8-254b06f9bfde.json", "r") as f:
        creds_json = json.load(f)

    # Buat objek Credentials dari isi file
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPE)

    # Otorisasi ke Google Sheets
    client = gspread.authorize(creds)

    # Pastikan nama sheet sama persis
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

def append_to_gsheet(df_annotations, annotator_name):
    sheet = connect_gsheet()
    for _, row in df_annotations.iterrows():
        sheet.append_row([
            row.get('tweet_id', ''),
            row.get('tweet', ''),
            row.get('aspek', ''),
            row.get('sentimen', ''),
            annotator_name,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])
    st.success("✅ Data berhasil dikirim ke Google Sheet!")

# ==== Konfigurasi Aspek & Sentimen ====
ASPECTS = [
    "Kebijakan Pemerintah",
    "Kompetensi Menteri", 
    "Fleksibilitas",
    "Keterwakilan",
    "Transparansi"
]

SENTIMENTS = ["Positif", "Negatif", "Netral"]

# ==== Mapping Aspek ke File Dataset ====
ASPECT_FILES = {
    "Kebijakan Pemerintah": "filtered_aspek_kebijakan_top100.csv",
    "Kompetensi": "filtered_aspek_kompetensi_top100.csv",
    "Responsivitas": "filtered_aspek_responsivitas_top100.csv",
    "Representasi": "filtered_aspek_representasi_top100.csv",
    "Transparansi": "filtered_aspek_transparansi_top100.csv"
}

# ==== Load & Combine All Datasets ====
@st.cache_data
def load_combined_dataset():
    all_dfs = []
    for aspect, filename in ASPECT_FILES.items():
        try:
            df_temp = pd.read_csv(f"dataset/{filename}")  # Add dataset/ prefix
            df_temp['aspek_utama'] = aspect  # Tambahkan kolom aspek utama
            all_dfs.append(df_temp)
        except FileNotFoundError:
            st.warning(f"File dataset/{filename} tidak ditemukan!")
    
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        # Rename column to match our code
        combined = combined.rename(columns={'Cleaned_Tweet': 'tweet'})
        return combined
    else:
        st.error("Tidak ada dataset yang berhasil dimuat!")
        return pd.DataFrame()

df = load_combined_dataset()

# ==== Session State Initialization ====
# Try to load saved state
try:
    with open('annotation_state.json', 'r') as f:
        saved_state = json.load(f)
        
    if "annotations" not in st.session_state:
        st.session_state.annotations = saved_state.get('annotations', [])
    
    if "current_index" not in st.session_state:
        st.session_state.current_index = saved_state.get('current_index', 0)
    
    if "current_aspects" not in st.session_state:
        st.session_state.current_aspects = saved_state.get('current_aspects', {})
    
    if "completed_tweets" not in st.session_state:
        st.session_state.completed_tweets = set(saved_state.get('completed_tweets', []))
        
except FileNotFoundError:
    # Initialize fresh state if no saved state exists
    if "annotations" not in st.session_state:
        st.session_state.annotations = []
    
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    
    if "current_aspects" not in st.session_state:
        st.session_state.current_aspects = {}
    
    if "completed_tweets" not in st.session_state:
        st.session_state.completed_tweets = set()

# ==== Main App ====
st.title("🏛️ Anotator Sentimen Kabinet Merah Putih")

# Progress indicator
progress = len(st.session_state.completed_tweets) / len(df)
st.progress(progress)

# Info dataset
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric("Total Dataset", f"{len(df)} tweet")
with col_info2:
    st.metric("Sudah Dilabeli", f"{len(st.session_state.completed_tweets)} tweet")
with col_info3:
    remaining = len(df) - len(st.session_state.completed_tweets)
    st.metric("Tersisa", f"{remaining} tweet")

st.divider()

# Current tweet display
current_tweet = df.iloc[st.session_state.current_index]["tweet"]
aspek_utama = df.iloc[st.session_state.current_index]["aspek_utama"]

st.write(f"### 📝 Tweet ke-{st.session_state.current_index+1} dari {len(df)}")

# Tampilkan badge aspek utama
aspek_colors = {
    "Kebijakan Pemerintah": "🔵",
    "Kompetensi": "🟣",
    "Responsivitas": "🟢",
    "Representasi": "🟡",
    "Transparansi": "🔴"
}
badge = aspek_colors.get(aspek_utama, "⚪")

st.info(f" **Tweet:** {current_tweet}")

# Navigation buttons
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("⬅️ Tweet Sebelumnya"):
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1
            st.rerun()

with col2:
    tweet_selector = st.selectbox("Pilih Tweet:", 
                                 range(1, len(df)+1), 
                                 index=st.session_state.current_index,
                                 format_func=lambda x: f"Tweet {x}")
    if tweet_selector - 1 != st.session_state.current_index:
        st.session_state.current_index = tweet_selector - 1
        st.rerun()

with col3:
    if st.button("Tweet Selanjutnya ➡️"):
        if st.session_state.current_index < len(df) - 1:
            st.session_state.current_index += 1
            st.rerun()

st.divider()

# ==== Multi-Aspect Annotation Section ====
st.write("### 🎯 Label Aspek & Sentimen")

# Display current aspects for this tweet
tweet_key = f"tweet_{st.session_state.current_index}"
if tweet_key not in st.session_state.current_aspects:
    st.session_state.current_aspects[tweet_key] = {}

current_tweet_aspects = st.session_state.current_aspects[tweet_key]

# Show existing labels for current tweet
if current_tweet_aspects:
    st.write("**Aspek yang sudah dilabeli:**")
    for aspect, sentiment in current_tweet_aspects.items():
        col_a, col_b, col_c = st.columns([3,2,1])
        with col_a:
            st.write(f"• **{aspect}**")
        with col_b:
            color = "🟢" if sentiment == "Positif" else "🔴" if sentiment == "Negatif" else "🟡"
            st.write(f"{color} {sentiment}")
        with col_c:
            if st.button(f"🗑️", key=f"del_{aspect}"):
                del st.session_state.current_aspects[tweet_key][aspect]
                st.rerun()

# Add new aspect-sentiment pair
st.write("**Tambah Label Baru:**")
col_aspect, col_sentiment = st.columns([2,1])

with col_aspect:
    selected_aspect = st.selectbox("Pilih Aspek:", 
                                  ["-- Pilih Aspek --"] + ASPECTS,
                                  key="aspect_selector")

with col_sentiment:
    selected_sentiment = st.selectbox("Pilih Sentimen:", 
                                     SENTIMENTS,
                                     key="sentiment_selector")

# Add aspect button
if st.button("➕ Tambah Label", type="primary"):
    if selected_aspect != "-- Pilih Aspek --":
        st.session_state.current_aspects[tweet_key][selected_aspect] = selected_sentiment
        st.success(f"✅ Label **{selected_aspect}** → **{selected_sentiment}** berhasil ditambahkan!")
        st.rerun()
    else:
        st.error("❌ Harap pilih aspek terlebih dahulu!")

# Complete annotation for current tweet - Make it more prominent
st.markdown("---")
st.markdown("### 🔥 **SELESAIKAN TWEET INI**")
col_complete, col_info = st.columns([2, 3])

with col_complete:
    if st.button("✅ SELESAI LABEL TWEET INI", type="primary", use_container_width=True):
        # Check if there are already added aspects OR if new aspect is selected
        has_aspects = bool(current_tweet_aspects)
        has_new_selection = selected_aspect != "-- Pilih Aspek --"
        
        if has_aspects or has_new_selection:
            # Add the currently selected aspect if not already added
            if has_new_selection and selected_aspect not in current_tweet_aspects:
                st.session_state.current_aspects[tweet_key][selected_aspect] = selected_sentiment
            
            # Save all aspects to final annotations
            for aspect, sentiment in st.session_state.current_aspects[tweet_key].items():
                st.session_state.annotations.append({
                    "tweet_id": st.session_state.current_index + 1,
                    "tweet": current_tweet,
                    "aspek": aspect,
                    "sentimen": sentiment
                })
            
            st.session_state.completed_tweets.add(st.session_state.current_index)
            total_aspects = len(st.session_state.current_aspects[tweet_key])
            st.success(f"🎉 Tweet {st.session_state.current_index + 1} berhasil diselesaikan dengan {total_aspects} aspek!")
            
            # Move to next tweet
            if st.session_state.current_index < len(df) - 1:
                st.session_state.current_index += 1
                st.rerun()
        else:
            st.error("❌ Pilih aspek dan sentimen sebelum menyelesaikan tweet!")

with col_info:
    has_aspects = bool(current_tweet_aspects)
    has_new_selection = selected_aspect != "-- Pilih Aspek --"
    
    if has_aspects and has_new_selection:
        total_count = len(current_tweet_aspects) + (1 if selected_aspect not in current_tweet_aspects else 0)
        st.success(f"✅ Siap diselesaikan ({total_count} aspek)")
    elif has_aspects:
        st.success(f"✅ Siap diselesaikan ({len(current_tweet_aspects)} aspek)")
    elif has_new_selection:
        st.info(f"✅ Siap diselesaikan (1 aspek: {selected_aspect})")
    else:
        st.warning("⚠️ Pilih aspek dan sentimen untuk melanjutkan")

st.divider()

# ==== Results Summary ====
st.write("### 📊 Ringkasan Hasil Anotasi")

if st.session_state.annotations:
    df_annotations = pd.DataFrame(st.session_state.annotations)

    # Summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Label", len(df_annotations))
    with col2:
        st.metric("Tweet Selesai", len(st.session_state.completed_tweets))
    with col3:
        aspects_count = df_annotations['aspek'].nunique()
        st.metric("Aspek Unik", aspects_count)

    # Show annotations table
    with st.expander("🔍 Lihat Detail Anotasi"):
        st.dataframe(df_annotations)

    # === Simpan dan ekspor hasil ===
    def save_annotations():
        df_annotations = pd.DataFrame(st.session_state.annotations)

        # 1️⃣ Simpan ke file lokal (backup)
        csv_filename = "annotations.csv"
        df_annotations.to_csv(csv_filename, index=False)

        json_filename = "annotations.json"
        df_annotations.to_json(json_filename, orient='records', indent=2)

        txt_filename = "annotations.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for _, row in df_annotations.iterrows():
                f.write(f"$T$ {row['tweet']}\n")
                f.write(f"{row['aspek']}\n")
                f.write(f"{row['sentimen']}\n")

        # 2️⃣ Simpan ke Google Sheet (dengan nama anotator otomatis)
        try:
            sheet = connect_gsheet()
            for _, row in df_annotations.iterrows():
                sheet.append_row([
                    row.get('tweet_id', ''),
                    row.get('tweet', ''),
                    row.get('aspek', ''),
                    row.get('sentimen', ''),
                    ANNOTATOR_NAME,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
            st.success(f"✅ Data berhasil dikirim ke Google Sheet oleh {ANNOTATOR_NAME}!")
        except Exception as e:
            st.error(f"⚠️ Gagal menyimpan ke Google Sheet: {e}")

        # 3️⃣ Simpan progress state
        state = {
            'current_index': st.session_state.current_index,
            'annotations': st.session_state.annotations,
            'completed_tweets': list(st.session_state.completed_tweets),
            'current_aspects': st.session_state.current_aspects
        }
        with open('annotation_state.json', 'w') as f:
            json.dump(state, f)

        return csv_filename, json_filename, txt_filename

    # Tombol simpan manual
    if st.button("💾 Simpan Progress", type="primary"):
        save_annotations()
        st.success("✅ Progress berhasil disimpan!")

    # Tombol download
    col1, col2, col3 = st.columns(3)
    with col1:
        csv_data = df_annotations.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name="annotations.csv",
            mime="text/csv"
        )

    with col2:
        json_data = df_annotations.to_json(orient='records', indent=2)
        st.download_button(
            label="⬇️ Download JSON",
            data=json_data,
            file_name="annotations.json",
            mime="application/json"
        )

    with col3:
        txt_data = ""
        for _, row in df_annotations.iterrows():
            txt_data += f"$T$ {row['tweet']}\n"
            txt_data += f"{row['aspek']}\n"
            txt_data += f"{row['sentimen']}\n"

        st.download_button(
            label="⬇️ Download TXT",
            data=txt_data,
            file_name="annotations.txt",
            mime="text/plain"
        )

else:
    st.info("👆 Mulai labeling untuk melihat ringkasan hasil")


# ==== Statistics ====
if st.session_state.annotations:
    with st.expander("📈 Statistik Sentimen"):
        df_stats = pd.DataFrame(st.session_state.annotations)
        
        # Sentiment distribution
        sentiment_counts = df_stats['sentimen'].value_counts()
        st.write("**Distribusi Sentimen:**")
        for sentiment, count in sentiment_counts.items():
            color = "🟢" if sentiment == "Positif" else "🔴" if sentiment == "Negatif" else "🟡"
            st.write(f"{color} {sentiment}: {count}")
        
        # Aspect distribution  
        st.write("**Distribusi Aspek:**")
        aspect_counts = df_stats['aspek'].value_counts()
        for aspect, count in aspect_counts.head(5).items():
            st.write(f"• {aspect}: {count}")

# ==== Clear Annotations Button ====
if st.session_state.annotations:
    st.markdown("---")
    st.markdown("### 🗑️ **Hapus Semua Anotasi**")
    
    col_warning, col_clear = st.columns([3, 1])
    with col_warning:
        st.warning("⚠️ **Peringatan:** Tindakan ini akan menghapus semua hasil anotasi yang telah dibuat!")
    
    with col_clear:
        if st.button("🗑️ HAPUS SEMUA", type="secondary", use_container_width=True):
            # Show confirmation dialog using session state
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = True
                st.rerun()
    
    # Confirmation dialog
    if st.session_state.get('confirm_clear', False):
        st.error("🚨 **Konfirmasi Penghapusan**")
        st.write("Apakah Anda yakin ingin menghapus semua anotasi? Tindakan ini tidak dapat dibatalkan!")
        
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Ya, Hapus Semua", type="primary", use_container_width=True):
                # Clear all annotations and state
                st.session_state.annotations = []
                st.session_state.completed_tweets = set()
                st.session_state.current_aspects = {}
                st.session_state.current_index = 0
                st.session_state.confirm_clear = False
                
                # Remove saved files
                try:
                    import os
                    files_to_remove = ['annotation_state.json', 'annotations.csv', 'annotations.json', 'annotations.txt']
                    for file in files_to_remove:
                        if os.path.exists(file):
                            os.remove(file)
                except:
                    pass
                
                st.success("✅ Semua anotasi berhasil dihapus!")
                st.rerun()
        
        with col_no:
            if st.button("❌ Batal", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
