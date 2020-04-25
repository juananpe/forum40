Embedding service
=================

Provides a simple API for computing embeddings given texts:
* compute embeddings for a list of strings (BERT-based)

Indexing and retrieval of embeddings are handled with 
a different API as defined in the backend-service.

Start this service as a separate webservice, e.g. on ltgpu1:

# Create a new python environment, and activate it
# `cd embedding-service`
# `pip install -r requirements.txt`
# Optional: Look for a free CUDA device id
# Start the service: `CUDA_VISIBLE_DEVICES=0 gunicorn -b 0.0.0.0:5060 --worker-connections 500 --timeout 400 app:app` 

