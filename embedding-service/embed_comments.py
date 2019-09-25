import pymongo, argparse, logging
from BertFeatureExtractor import BertFeatureExtractor
from pymongo import UpdateOne

from utils import concat

# create logger
logger = logging.getLogger('Embedding logger')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def process_batch(comment_batch):
    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]
    comment_embeddings = be.extract_features(comment_texts)
    batch_update_comments = []
    for i, comment_embedding in enumerate(comment_embeddings):

        # get comment object id
        comment_id = comment_batch[i]["_id"]

        # update mongo db
        batch_update_comments.append(
            UpdateOne({"_id": comment_id}, {"$set": {
                'embedding' : comment_embedding["embedding"],
                'embedded' : True
            }})
        )
    
    comments.bulk_write(batch_update_comments)



if __name__== "__main__":

# CLI parser


    parser = argparse.ArgumentParser(description='Embed comments in MongoDB.')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='MongoDB host (default: localhost)')
    parser.add_argument('port', type=int, default=27017, nargs='?',
                        help='MongoDB port (default: 27017)')
    parser.add_argument('--embed-all', dest='all', type=bool, default=False, nargs=1,
                        help='(Re-)embed all data (default: False)')
    parser.add_argument('--device', type=str, default='cpu', nargs='?',
                        help='Pytorch device for tensor operations (default: cpu, else cuda)')
    parser.add_argument('--batch-size', dest='batch_size', type=int, default=8, nargs='?',
                        help='Batch size for tensor operations (default: 8).')
    parser.add_argument('--keep-CLS', dest='keep_cls', type=bool, default=True, nargs=1,
                        help='include CLS when calculating embeddings for all the tokens (default: True).')
    parser.add_argument('--use-tokens', dest='use_token', type=bool, default=True, nargs=1,
                        help='use tokens or CLS (default: True).')
    parser.add_argument('--layers', dest='use_layers', type=int, default=4, nargs='?',
                        help='how many previous layers from the last to be used (default=4).')

    args = parser.parse_args()

    # Connect to DB
    client = pymongo.MongoClient(args.host, args.port)
    db = client.omp
    batch_size = args.batch_size

    print("Loading BERT model")
    be = BertFeatureExtractor(batch_size=batch_size, device=args.device,keep_cls=args.keep_cls,use_layers=args.use_layers, use_token=args.use_token)

    comments = db.Comments

    embed_all = args.all

    n_comments = comments.count()

    logger.info("Comments in the database: " + str(n_comments))

    if embed_all:
        embed_query = {}
    else:
        embed_query = {"embedded": {"$ne": True}}

    n_to_embed = comments.find(embed_query).count()
    logger.info("Comments to embed: " + str(n_to_embed))

    batch_i = 0
    i = 0
    comment_batch = []
    for comment in comments.find(embed_query,{"_id" : 1, "title" : 1, "text" : 1},
            cursor_type=pymongo.CursorType.EXHAUST,snapshot=True):
        if not comment['title'] and not comment['text']:
            continue
        i += 1
        comment_batch.append(comment)
        if i % batch_size == 0:
            batch_i += 1
            logger.info("Batch: " + str(batch_i) + ";  comment " + str(i) + " of " + str(n_to_embed))
            # get embeddings
            process_batch(comment_batch)
            # reset batch
            comment_batch = []
            break

    if comment_batch:
        process_batch(comment_batch)

