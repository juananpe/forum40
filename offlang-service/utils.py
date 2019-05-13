import math, re
import numpy as np
import keras

def concat(title: str, text: str) -> str:
    """
    Concatenates comment's title and text
    :param title: comment title
    :param text: comment text
    :return: concatenated comment text
    """
    title = title if title else ''
    text = text if text else ''
    return (title + ' ' + text).strip()


def twitter_tokenizer(textline):
    textLine = re.sub(r'http\S+', 'URL', textline)
    textline = re.sub('@[\w_]+', 'USER_MENTION', textline)
    textline = re.sub('\|LBR\|', '', textline)
    textline = re.sub('\.\.\.+', '...', textline)
    textline = re.sub('!!+', '!!', textline)
    textline = re.sub('\?\?+', '??', textline)
    words = re.compile('[\U00010000-\U0010ffff]|[\w-]+|[^ \w\U00010000-\U0010ffff]+', re.UNICODE).findall(
        textline.strip())
    words = [w.strip() for w in words if w.strip() != '']
    # print(words)
    return (words)


class EmbeddingGenerator(keras.utils.Sequence):
    def __init__(self, sentences, ft_model, max_sequence_length=75, batch_size=256):
        # data
        self.data = sentences
        self.indices = np.arange(len(self.data))
        self.batch_size = batch_size
        self.max_sequence_length = max_sequence_length
        self.ft_model = ft_model
        self.word_embedding_dims = ft_model.get_dimension()
        self.padding_embedding = [0] * self.word_embedding_dims

    def __len__(self):
        return math.ceil(len(self.data) / self.batch_size)

    def __getitem__(self, idx):
        inds = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_x, batch_y = self.process_text_data(inds)
        return batch_x, batch_y

    def sequence_to_embedding(self, word_array):
        # pruning
        max_l = self.max_sequence_length
        if len(word_array) > max_l:
            word_array = word_array[:max_l]
        # padding
        words_to_pad = max_l - len(word_array)
        word_array = np.append(word_array, ['PADDING_TOKEN'] * words_to_pad)
        embedding_list = []
        for w_i, word in enumerate(word_array):
            if word == 'PADDING_TOKEN':
                embedding_list.append(self.padding_embedding)
            else:
                embedding_list.append(self.ft_model.get_word_vector(word))
        return embedding_list

    def process_text_data(self, indexes):

        input_u = []
        output_v = [0] * len(indexes)  # dummy output ...

        for i, index in enumerate(indexes):

            instance = self.data[index]
            if isinstance(instance, str):
                instance = twitter_tokenizer(instance)

            embeddings_u = self.sequence_to_embedding(instance)

            input_u.append(embeddings_u)

        batch_embedding_sequence = np.array(input_u)

        # separate encoders:
        return ([batch_embedding_sequence], np.array(output_v))

def classify(model, ft, texts, CLASSES):
    prediction = model.predict_generator(EmbeddingGenerator(texts, ft))
    label_indexes = np.argmax(prediction, axis=1)
    result_labels = [{'label': CLASSES[index],
                      'confidence': prediction[i].tolist()} for i, index in enumerate(label_indexes)]
    return result_labels
