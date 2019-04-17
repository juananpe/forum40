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

# Allow other computers to attach to ptvsd at this IP address and port.
# ptvsd.enable_attach(address=('0.0.0.0', 3000), redirect_output=True)

# Pause the program until a remote debugger is attached
# ptvsd.wait_for_attach()

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
    'comment', {'text': fields.String('The text of the comment.')})


@api.route('/comment')
class HelloWorld(Resource):

    @api.expect(comment_model)
    def post(self):
        comment_text = api.payload.get('text', '')
        if comment_text:
            pad_sequences, _ = self.__get_data_tensor([comment_text])
            prediction = model.predict(pad_sequences)
            ylabel = META_CLASSES[np.argmax(prediction)]
            print(ylabel)
            return {'msg': comment_text,
                    'label': ylabel,
                    'confidence': prediction[0].tolist()}
        return 'no comment text provided'

    def __get_data_tensor(self, texts):
        # finally, vectorize the text samples into a 2D integer tensor
        sequences = tokenizer.texts_to_sequences(texts)
        word_index = tokenizer.word_index
        print('Found %s unique tokens.' % len(word_index))
        return pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH), word_index


# run app manuelly
if __name__ == "__main__":
    print('hallo')
    app.run(host='0.0.0.0', port=5060, debug=True)
