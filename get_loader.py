import json
import os
import pandas as pd
import torch
from PIL import Image
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset
from nltk.tokenize import word_tokenize
from torchvision.transforms import transforms


class Vocabulary:
    def __init__(self, freq_threshold):
        self.itos = {0: "<PAD>", 1: "<SOS>", 2: "<EOS>", 3: "<UNK>"}
        self.stoi = {"<PAD>": 0, "<SOS>": 1, "<EOS>": 2, "<UNK>": 3}
        self.freq_threshold = freq_threshold

    def __len__(self):
        return len(self.itos)

    @staticmethod
    def tokenizer_eng(text):
        return [tok.lower() for tok in word_tokenize(text)]

    def build_vocabulary(self, sentence_list):
        frequencies = {}
        idx = 4

        for sentence in sentence_list:
            for word in self.tokenizer_eng(sentence):
                if word not in frequencies:
                    frequencies[word] = 1
                else:
                    frequencies[word] += 1
                if frequencies[word] == self.freq_threshold:
                    self.stoi[word] = idx
                    self.itos[idx] = word
                    idx += 1

    def numericalize(self, text):
        tokenized_text = self.tokenizer_eng(text)
        return [
            self.stoi[token] if token in self.stoi else self.stoi["<UNK>"]
            for token in tokenized_text
        ]

    def load_vocab(self, vocab_file):
        with open(vocab_file, 'r') as f:
            vocab = json.load(f)
            self.itos = vocab['itos']
            self.stoi = vocab['stoi']


def save_vocab(captions, vocab_file, freq_threshold=5):
    # Leggi le didascalie dal file
    df = pd.read_csv(captions, sep=',')

    # Istanzia l'oggetto Vocabulary
    vocab = Vocabulary(freq_threshold=freq_threshold)

    # Costruisci il vocabolario usando le frasi nella colonna 'caption'
    vocab.build_vocabulary(df['caption'])

    # Salva solo il dizionario 'itos' in un file JSON
    with open(vocab_file, 'w') as f:
        json.dump({'itos': vocab.itos, 'stoi': vocab.stoi}, f)

# save_vocab("flickr8k_images/captions.txt", 'vocab.json')


class FlickrDataset(Dataset):
    def __init__(self, root_dir, captions_file, vocab_file, transform=None):
        self.root_dir = root_dir
        self.df = pd.read_csv(captions_file, skipinitialspace=True, engine='python')

        # Pulisci eventuali spazi extra e rimuovi le virgolette
        self.df['caption'] = self.df['caption'].astype(str).str.replace(',', '', regex=False)
        self.df['image'] = self.df['image'].astype(str).str.strip()
        self.df['caption'] = self.df['caption'].astype(str).str.strip()
        self.transform = transform

        # Get img, caption columns
        self.imgs = self.df["image"]
        self.captions = self.df["caption"]

        # Initialize vocabulary and load from file
        self.vocab = Vocabulary(freq_threshold=0)
        self.vocab.load_vocab(vocab_file)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        caption = self.captions[index]
        img_id = self.imgs[index]
        img = Image.open(os.path.join(self.root_dir, img_id)).convert("RGB")

        if self.transform is not None:
            img = self.transform(img)

        numericalized_caption = [self.vocab.stoi["<SOS>"]]
        numericalized_caption += self.vocab.numericalize(caption)
        numericalized_caption.append(self.vocab.stoi["<EOS>"])

        return img, torch.tensor(numericalized_caption)



class MyCollate:
    def __init__(self, pad_idx):
        self.pad_idx = pad_idx

    def __call__(self, batch):
        imgs = [item[0].unsqueeze(0) for item in batch]
        imgs = torch.cat(imgs, dim=0)
        targets = [item[1] for item in batch]
        targets = pad_sequence(targets, batch_first=False, padding_value=self.pad_idx)

        return imgs, targets


def get_loader(
        root_folder,
        annotation_file,
        vocab_file,
        transform,
        batch_size=32,
        num_workers=8,
        shuffle=True,
        pin_memory=True,
):
    dataset = FlickrDataset(root_folder, annotation_file, vocab_file, transform=transform)

    pad_idx = dataset.vocab.stoi["<PAD>"]

    loader = DataLoader(
        dataset=dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=shuffle,
        pin_memory=pin_memory,
        collate_fn=MyCollate(pad_idx=pad_idx),
    )

    return loader, dataset

# if __name__ == "__main__":
#     transform = transforms.Compose(
#         [transforms.Resize((224, 224)), transforms.ToTensor(),]
#     )
#
#     loader, dataset = get_loader(
#         "flickr8k_images/Images/", "flickr8k_images/cleaned_captions.txt", transform=transform
#     )
#
#     for idx, (imgs, captions) in enumerate(loader):
#         print(imgs.shape)
#         print(captions.shape)
