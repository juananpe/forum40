import math, re
import numpy as np

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


# do stuff here ...
def classify(model, ft, texts, CLASSES):
    prediction = model.predict_generator(EmbeddingGenerator(texts, ft))
    label_indexes = np.argmax(prediction, axis=1)
    result_labels = [{'label': CLASSES[index],
                      'confidence': prediction[i].tolist()} for i, index in enumerate(label_indexes)]
    return result_labels
