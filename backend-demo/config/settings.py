# Flask settings

# Flask-Restplus settings
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False

# Swagger settings
SWAGGER_UI_DOC_EXPANSION = 'none'

# Embedding container URL
EMBEDDING_SERVICE_URL = 'http://embedding:5060/embed'
EMBEDDING_INDEX_PATH = "models"

# Model training
NUMBER_SAMPLES_FOR_NEXT_TRAINING = 10
NUMBER_MIN_SAMPLES_PER_CLASS = 10
