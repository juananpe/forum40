# Flask settings

# Flask-Restplus settings
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = False

# Swagger settings
SWAGGER_UI_DOC_EXPANSION = 'none'

# JSON Web Token 
JWT_SECRET_KEY = 'eh9Df9G27gahgHJ7g2oGQz6Ug5he6ud5shd'

# Embedding container URL
EMBEDDING_SERVICE_URL = 'http://embedding:5060/embed'
# EMBEDDING_SERVICE_URL = 'http://ltdemos.informatik.uni-hamburg.de/embedding-service'
EMBEDDING_INDEX_PATH = "models"

# Model training
NUMBER_SAMPLES_FOR_NEXT_TRAINING = 10