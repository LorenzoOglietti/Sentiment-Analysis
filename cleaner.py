import csv

import pandas as pd

path ="flickr8k_images\captions.txt"
# Leggi e correggi eventuali virgole all'interno delle virgolette
with open(path, 'r', encoding='utf-8') as infile, open('flickr8k_images/cleaned_captions.txt', 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile, delimiter=',', quotechar='"')
    writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        # Opzione per rimuovere manualmente virgole dai campi di testo
        row = [field.replace(',', '') if field.startswith('"') and field.endswith('"') else field for field in row]
        writer.writerow(row)

# Ora leggi il file pulito con Pandas
df = pd.read_csv('flickr8k_images\cleaned_captions.txt', delimiter=',', quotechar='"', skipinitialspace=True, engine='python')

print(df.head())
