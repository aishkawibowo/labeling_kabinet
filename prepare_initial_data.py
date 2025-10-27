import pandas as pd

# Baca file hasil segmentasi
df = pd.read_csv('dataset/gabungan_dataset_segmented.csv')

# Buat format awal untuk labeling (text saja, tanpa label)
with open('dataset/train.txt', 'w', encoding='utf-8') as f:
    for text in df['Segmented_Text']:
        # Format dasar: text####
        f.write(f"{text}####\n")

print("File train.txt telah dibuat di folder dataset/")
print("Selanjutnya Anda bisa menggunakan 2_ABSADatasetPrepareTool.html untuk melakukan labeling")
