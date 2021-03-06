from config.secrets import secrets

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

# Database connection
DB_HOST = 'db'
DB_PORT = 5432
DB_NAME = 'forum40'
DB_USER = 'postgres'
DB_PASSWORD = secrets['db_password'].decode('utf8')

# JWT
JWT_KEY = secrets['jwt_key']
