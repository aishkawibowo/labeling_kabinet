import streamlit as st
import pandas as pd
import json
import os

# ==== Konfigurasi Aspek & Sentimen ====
ASPECTS = [
    "Struktur Kabinet",
    "Figur Menteri", 
    "Program Kerja",
    "Kinerja Kabinet"
]

SENTIMENTS = ["Positif", "Negatif", "Netral"]

# ==== Session State Initialization ====
if 'annotations' not in st.session_state:
    st.session_state.annotations = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'current_aspects' not in st.session_state:
    st.session_state.current_aspects = {}
if 'completed_tweets' not in st.session_state:
    st.session_state.completed_tweets = set()

# Try to load saved state
try:
    with open('annotation_state.json', 'r') as f:
        saved_state = json.load(f)
        st.session_state.annotations = saved_state.get('annotations', [])
        st.session_state.current_index = saved_state.get('current_index', 0)
        st.session_state.current_aspects = saved_state.get('current_aspects', {})
        st.session_state.completed_tweets = set(saved_state.get('completed_tweets', []))
except FileNotFoundError:
    pass

# ==== Load Dataset ====
df = pd.read_csv("dataset/gabungan_dataset.csv")
df = df.rename(columns={'Cleaned_Tweet': 'tweet'})

# ==== Main App ====
st.title("🏛️ Anotator Sentimen Kabinet Merah Putih")
st.subheader("Analisis Sentimen Berbasis Aspek Tweet Politik")

# Progress indicator
progress = len(st.session_state.completed_tweets) / len(df)
st.progress(progress)
st.write(f"Progress: {len(st.session_state.completed_tweets)}/{len(df)} tweet selesai dilabeli")

# Current tweet display
current_tweet = df.iloc[st.session_state.current_index]["tweet"]
st.write(f"### Tweet ke-{st.session_state.current_index+1} dari {len(df)}")
st.info(f"📝 **Tweet:** {current_tweet}")

# Get current tweet's key
tweet_key = f"tweet_{st.session_state.current_index}"
if tweet_key not in st.session_state.current_aspects:
    st.session_state.current_aspects[tweet_key] = {}

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

# Show existing labels for current tweet
if st.session_state.current_aspects[tweet_key]:
    st.write("**Aspek yang sudah dilabeli:**")
    for aspect, sentiment in st.session_state.current_aspects[tweet_key].items():
        col_a, col_b, col_c = st.columns([3,2,1])
        with col_a:
            st.write(f"• **{aspect}**")
        with col_b:
            color = "🟢" if sentiment == "Positif" else "🔴" if sentiment == "Negatif" else "🟡"
            st.write(f"{color} {sentiment}")
        with col_c:
            if st.button(f"🗑️", key=f"del_{aspect}_{tweet_key}"):
                del st.session_state.current_aspects[tweet_key][aspect]
                st.rerun()

# Add new aspect-sentiment pair
st.write("**Tambah Label Baru:**")
col_aspect, col_sentiment = st.columns([2,1])

with col_aspect:
    selected_aspect = st.selectbox("Pilih Aspek:", 
                                  ["-- Pilih Aspek --"] + ASPECTS,
                                  key=f"aspect_selector_{tweet_key}")

with col_sentiment:
    selected_sentiment = st.selectbox("Pilih Sentimen:", 
                                     SENTIMENTS,
                                     key=f"sentiment_selector_{tweet_key}")

# Add aspect button
if st.button("➕ Tambah Label", type="primary", key=f"add_label_{tweet_key}"):
    if selected_aspect != "-- Pilih Aspek --":
        st.session_state.current_aspects[tweet_key][selected_aspect] = selected_sentiment
        st.success(f"✅ Label **{selected_aspect}** → **{selected_sentiment}** berhasil ditambahkan!")
        st.rerun()
    else:
        st.error("❌ Harap pilih aspek terlebih dahulu!")

# Complete annotation for current tweet
if st.button("✅ Selesai Label Tweet Ini", type="primary", use_container_width=True):
    current_aspects = st.session_state.current_aspects.get(tweet_key, {})
    
    # Debug information
    st.write("Debug Info:")
    st.write(f"Tweet Key: {tweet_key}")
    st.write(f"Current Aspects: {current_aspects}")
    st.write(f"All Aspects: {st.session_state.current_aspects}")
    
    if len(current_aspects) > 0:
        # Add to final annotations
        for aspect, sentiment in current_aspects.items():
            annotation = {
                "tweet_id": st.session_state.current_index + 1,
                "tweet": current_tweet.strip(),
                "aspek": aspect.strip(),
                "sentimen": sentiment.strip()
            }
            
            # Remove any existing annotation for this tweet and aspect
            st.session_state.annotations = [
                a for a in st.session_state.annotations 
                if not (a["tweet_id"] == annotation["tweet_id"] and a["aspek"] == annotation["aspek"])
            ]
            
            # Add the new annotation
            st.session_state.annotations.append(annotation)
        
        st.session_state.completed_tweets.add(st.session_state.current_index)
        st.success(f"🎉 Tweet {st.session_state.current_index + 1} berhasil diselesaikan dengan {len(current_aspects)} aspek!")
        
        # Save state
        state = {
            'current_index': st.session_state.current_index,
            'annotations': st.session_state.annotations,
            'completed_tweets': list(st.session_state.completed_tweets),
            'current_aspects': st.session_state.current_aspects
        }
        with open('annotation_state.json', 'w') as f:
            json.dump(state, f)
        
        # Move to next tweet
        if st.session_state.current_index < len(df) - 1:
            st.session_state.current_index += 1
            st.rerun()
    else:
        st.error("❌ Tambahkan minimal 1 aspek sebelum menyelesaikan tweet!")

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
    
    # Download buttons
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
        df_unique = df_annotations.drop_duplicates(subset=['tweet', 'aspek'], keep='first')
        for _, row in df_unique.iterrows():
            txt_data += f"$T$ {row['tweet'].strip()}\n{row['aspek'].strip()}\n{row['sentimen'].strip()}\n"
        
        st.download_button(
            label="⬇️ Download TXT",
            data=txt_data,
            file_name="annotations.txt",
            mime="text/plain"
        )
    
    # Statistics
    with st.expander("📈 Statistik Sentimen"):
        # Sentiment distribution
        sentiment_counts = df_annotations['sentimen'].value_counts()
        st.write("**Distribusi Sentimen:**")
        for sentiment, count in sentiment_counts.items():
            color = "🟢" if sentiment == "Positif" else "🔴" if sentiment == "Negatif" else "🟡"
            st.write(f"{color} {sentiment}: {count}")
        
        # Aspect distribution  
        st.write("**Distribusi Aspek:**")
        aspect_counts = df_annotations['aspek'].value_counts()
        for aspect, count in aspect_counts.items():
            st.write(f"• {aspect}: {count}")
    
    # Clear all button
    st.write("---")
    if 'show_clear_confirmation' not in st.session_state:
        st.session_state.show_clear_confirmation = False
        
    col_clear, col_space = st.columns([1, 2])
    with col_clear:
        if not st.session_state.show_clear_confirmation:
            if st.button("🗑️ Clear Semua Label", type="secondary", use_container_width=True):
                st.session_state.show_clear_confirmation = True
                st.rerun()
        else:
            if st.button("⚠️ Konfirmasi Clear Semua Label", type="primary", use_container_width=True):
                st.session_state.annotations = []
                st.session_state.completed_tweets = set()
                st.session_state.current_aspects = {}
                st.session_state.current_index = 0
                st.session_state.show_clear_confirmation = False
                if os.path.exists('annotation_state.json'):
                    os.remove('annotation_state.json')
                st.success("✅ Semua label berhasil dihapus!")
                st.rerun()
