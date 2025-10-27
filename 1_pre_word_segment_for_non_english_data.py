# -*- coding: utf-8 -*-
# file: pre_segment_non_enlish_data.py
# time: 2022/8/4
# author: yangheng <hy345@exeter.ac.uk>
# github: https://github.com/yangheng95
# huggingface: https://huggingface.co/yangheng
# google scholar: https://scholar.google.com/citations?user=NPq5a_0AAAAJ&hl=en
# Copyright (C) 2021. All Rights Reserved.

def pre_word_segment(file=None, seg_fn=None):
    import pandas as pd
    
    # Baca file CSV
    df = pd.read_csv('dataset/gabungan_dataset.csv')
    
    # Ambil kolom yang berisi teks (sesuaikan dengan nama kolom di dataset Anda)
    texts = df['Cleaned_Tweet'].tolist()
    
    # Proses segmentasi untuk setiap teks
    segmented_texts = []
    for text in texts:
        if isinstance(text, str):
            # Segmentasi teks
            segmented = ' '.join(seg_fn(text))
            segmented_texts.append(segmented)
        else:
            segmented_texts.append('')
    
    # Simpan hasil segmentasi ke DataFrame baru
    df['Segmented_Text'] = segmented_texts
    
    # Simpan hasil ke file baru
    output_file = file.replace('.csv', '_segmented.csv')
    df.to_csv(output_file, index=False)
    
    print('Segmentation done! Results saved to:', output_file)


if __name__ == '__main__':
    # Before annotating non-blank segmented text, you need to segment the data.
    # You can try other word segmentation tools here and PR to this repo.

    # Gunakan metode tokenisasi sederhana
    def simple_tokenize(text):
        if not isinstance(text, str):
            return []
        # Pisahkan berdasarkan spasi dan tanda baca
        import re
        # Pisahkan tanda baca dari kata
        text = re.sub(r'([.,!?;:])', r' \1 ', text)
        # Hilangkan karakter khusus dan angka
        text = re.sub(r'[^a-zA-Z\s.,!?;:]', ' ', text)
        # Pisahkan berdasarkan spasi
        tokens = [token.strip() for token in text.split() if token.strip()]
        return tokens
    
    # Gunakan tokenizer sederhana
    seg_fn = simple_tokenize
    
    # Proses file gabungan_dataset.csv
    input_file = 'dataset/gabungan_dataset.csv'
    print(f"Processing file: {input_file}")
    pre_word_segment(file=input_file, seg_fn=seg_fn)
