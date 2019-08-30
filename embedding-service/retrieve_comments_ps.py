import pymongo, math, pprint, logging
import nmslib, pickle
import sys
from utils import concat
import sklearn.metrics as sm
import numpy as np
import argparse
from bson import ObjectId

logger = logging.getLogger('Comments Retrieval Logger')
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



class RetrieveComment:
	def __init__(self,host = "mongo", port = 27017, nearest_neighbours=10):
		self.client = pymongo.MongoClient(host, port)
		self.db = self.client.omp
		self.comments = self.db.Comments
		logger.info("Loading Index")
		self.index = nmslib.init()
		self.index.loadIndex("model/comment_vectors.index", load_data=True)
		logger.info("Index Loaded")
		logger.info("Loading comment vectors")
		self.comment_id_mapping = pickle.load(open("model/comment_vectors.mapping", "rb"))
		logger.info("Comment vectors loaded")
		self.id_comment_mapping = {v: k for k, v in self.comment_id_mapping.items()}
		self.nearest_neighbours=nearest_neighbours

    ## this id is stored in the mongo_db server
	def get_embeddings(self,_id):
		if(type(_id)==str):
			_id = ObjectId(_id)
		print(_id)
		#query_id = self.id_comment_mapping[_id]
		query_comment = self.comments.find_one({"_id": _id})
		return query_comment["embedding"]
		

	def get_nearest_ids(self,_id):
		if(type(_id)==str):
			_id = ObjectId(_id)

		query_comment = self.comments.find_one({"_id":_id})
		ids, distances = self.index.knnQuery(query_comment["embedding"], k=(self.nearest_neighbours+1))
		comment_db_id=[]
		for _id_ in ids:
			if (self.id_comment_mapping[_id_] != _id):
				comment_db_id.append(str(self.id_comment_mapping[_id_]))
		return comment_db_id
		



if __name__== "__main__":
        
    parser = argparse.ArgumentParser(description='comment retrieval')
    parser.add_argument('--id', type=str, nargs='?', default='1',
                        help='id of the comment')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='MongoDB host')
    parser.add_argument('port', type=int, default=27017, nargs='?',
                        help='MongoDB port')
    args = parser.parse_args()
    comment_id = args.id
    get_comment=RetrieveComment('localhost',27017)
    
    embeddings=get_comment.get_embeddings(comment_id)
    if(embeddings!=-1):
    	logger.info("the length of the embeddings are "+str(len(embeddings)))
    ids=get_comment.get_nearest_ids(comment_id)
    if(ids!=-1):
    	logger.info("the nearest_neighbours ids to the comment id: "+comment_id)
    	pprint.pprint(ids)
    


