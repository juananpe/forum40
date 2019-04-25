from flask import Flask
from flask_restplus import Api, Resource, fields
from core.proxy_wrapper import ReverseProxied
import keras
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
import pickle
import os
import numpy as np
import ptvsd

MAX_SEQUENCE_LENGTH = 1000
META_CLASSES = ['meta', 'non-meta']

# Load keras model and tokenizer model
model: keras.Model = keras.models.load_model('model/omp.h5')
model._make_predict_function()
tokenizer: Tokenizer = None
with open('model/tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
api = Api(app, version='0.1', title='Meta-Comment-Classification-API',
          description="An API for classifying user comments")

comment_model = api.model(
    'comment', {
        'title': fields.String('Title of the comment.'),
        'text': fields.String('Text of the comment.')})

comments_model = api.model('comments', {
    'comments': fields.List(fields.Nested(comment_model))
})


def __get_data_tensor(texts):
    # finally, vectorize the text samples into a 2D integer tensor
    sequences = tokenizer.texts_to_sequences(texts)
    word_index = tokenizer.word_index
    print('Found %s unique tokens.' % len(word_index))
    return pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH), word_index


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


def classify(text):
    pad_sequences, _ = __get_data_tensor([text])
    prediction = model.predict(pad_sequences)
    ylabel = META_CLASSES[np.argmax(prediction)]
    print(ylabel)
    return {'label': ylabel,
            'confidence': prediction[0].tolist()}


def classify_many(texts):
    pad_sequences, _ = __get_data_tensor(texts)
    prediction = model.predict(pad_sequences)
    label_indexes = np.argmax(prediction, axis=1)
    result_labels = [{'label': META_CLASSES[index],
                      'confidence':prediction[i].tolist()} for i, index in enumerate(label_indexes)]
    return result_labels


@api.route('/comment')
class MetaCommentClassifier(Resource):

    @api.expect(comment_model)
    def post(self):
        comment_title = api.payload.get('title', '')
        comment_text = api.payload.get('text', '')
        comment_text = concat(comment_title, comment_text)
        if comment_text:
            return classify(comment_text)
        return 'no comment text provided'


@api.route('/comments')
class MetaCommentsClassifier(Resource):
    @api.expect(comments_model)
    def post(self):
        comments = api.payload.get('comments', [])
        comment_texts = [
            concat(c.get('title', ''), c.get('text', ''))for c in comments
        ]
        results = classify_many(comment_texts)
        return results, 200


# run app manuelly
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5060, debug=True)
