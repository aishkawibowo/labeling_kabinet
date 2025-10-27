import pandas as pd
import os

def prepare_absa_dataset():
    # Baca file hasil segmentasi
    input_file = 'dataset/gabungan_dataset_segmented.csv'
    df = pd.read_csv(input_file)
    
    # Buat direktori output jika belum ada
    output_dir = 'dataset/prepared_data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Siapkan file untuk training dan testing
    train_file = os.path.join(output_dir, 'train.txt')
    test_file = os.path.join(output_dir, 'test.txt')
    
    # Fungsi untuk memformat teks sesuai format ABSA
    def format_for_absa(row):
        text = row['Segmented_Text']
        # Format: text####aspect terms####polarities
        # Untuk sementara kita set aspek dan polaritas kosong karena akan dianotasi manual
        return f"{text}########\n"
    
    # Bagi dataset menjadi train (80%) dan test (20%)
    train_size = int(0.8 * len(df))
    train_df = df[:train_size]
    test_df = df[train_size:]
    
    # Tulis ke file train
    with open(train_file, 'w', encoding='utf-8') as f:
        for _, row in train_df.iterrows():
            f.write(format_for_absa(row))
    
    # Tulis ke file test
    with open(test_file, 'w', encoding='utf-8') as f:
        for _, row in test_df.iterrows():
            f.write(format_for_absa(row))
    
    print(f"Dataset telah disiapkan:")
    print(f"- Train file: {train_file}")
    print(f"- Test file: {test_file}")
    print(f"\nFormat file: text####aspect_terms####polarities")
    print("Silakan anotasi aspek dan sentimen secara manual menggunakan format:")
    print("- Aspect terms: gunakan [B-ASP]aspect[E-ASP] untuk menandai aspek")
    print("- Polarities: positive, negative, atau neutral untuk setiap aspek")

if __name__ == '__main__':
    prepare_absa_dataset()
