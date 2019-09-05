import pymongo, argparse, logging
from pymongo import UpdateOne

# create logger
logger = logging.getLogger('Embedding logger')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


# CLI parser
parser = argparse.ArgumentParser(description='Embed comments in MongoDB.')
parser.add_argument('host', type=str, default='localhost', nargs='?',
                    help='MongoDB host (default: localhost)')
parser.add_argument('port', type=int, default=27017, nargs='?',
                    help='MongoDB port (default: 27017)')

args = parser.parse_args()

# Connect to DB
client = pymongo.MongoClient(args.host, args.port)
db = client.omp

comments = db.Comments

batch_size = 2048
i = 0
batch_updates = []
for comment in comments.find({}, {"_id" : 1, "embedding" : 1}, cursor_type=pymongo.CursorType.EXHAUST, snapshot=True):
    i += 1
    comment_id = comment["_id"]
    updates = {}
    if "embedding" in comment:
        batch_updates.append(UpdateOne({"_id": comment_id}, {"$set": {"embedded": True}}))
    else:
        batch_updates.append(UpdateOne({"_id": comment_id}, {"$set": {"embedded": False}}))

    if len(batch_updates) == batch_size:
        logger.info("Registering embedding " + str(i))
        bulk_results = comments.bulk_write(batch_updates)
        batch_updates = []

if batch_updates:
    bulk_results = comments.bulk_write(batch_updates)
