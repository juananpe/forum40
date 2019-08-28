import pymongo, argparse, pprint, logging
from collections import Counter
import numpy as np
from update_training import *
from timeit import default_timer as timer


# create logger
logger = logging.getLogger('Classifier logger')
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


# argument parsing
parser = argparse.ArgumentParser(description='Update category labels.')
parser.add_argument('--labelname', type=str, nargs='?', default='offtopic',
                    help='name of the category to update')
args = parser.parse_args()

# db connection
client = pymongo.MongoClient("localhost", 27017)
db = client.omp
labels = db.Labels
comments = db.Comments

label = labels.find_one({"classname" : args.labelname})
label_id = label["_id"]

logger.info("Labelname: " + args.labelname + " (" + str(label_id) + ")")

try:
    labeled_comments = comments.find({"labels.labelId" : label_id})
except:
    logging.error("No comments for label " + args.labelname)
    exit(1)


#start = timer()
# training data compilation
annotation_dataset = []
annotation_counts = Counter()
for labeled_comment in labeled_comments:
    for current_label in labeled_comment["labels"]:
        if current_label["labelId"] == label["_id"]:
            if "manualLabels" in current_label:
                manual_label = current_label["manualLabels"][0]['label']
                annotation_counts[manual_label] += 1
                labeled_instance = (labeled_comment["embedding"],manual_label)
                annotation_dataset.append(labeled_instance)
#end = timer()



logger.info("Manual annotations found: " + str(annotation_counts))
#logger.info("Each comment take "+str((start-end)/annotations_counts)+" seconds of collection time")
logger.info("Length of datset: " + str(len(annotation_dataset)))

new_model=TrainPredict()


logger.info("Training started")

start=timer()
new_model.train(annotation_dataset,args.labelname)
end=timer()

logger.info("Each comment take "+str((start-end)/annotations_counts)+" seconds of training time")


# db update
batch_size=10000

def process_batch(comment_batch):

    comments_object, embeddings = zip(*comment_batch)
    start=timer()
    comment_labels = new_model.predict(embeddings,args.labelname)
    end =timer()
    logger.info("Each comment take "+str((start-end)/batch_size)+" seconds of prediction time")

    #comment_labels = [[0.1, 0.9]] * len(embeddings)
    start=timer()
        
    for i, comment in enumerate(comments_object):

        comment_id = comment["_id"]
        confidence = comment_labels[i].tolist()

        # initialize labels field for comment
        if "labels" in comment:
            labels_object = {"labels" : comment["labels"]}
        else:
            labels_object = {"labels" : []}

        # manipulate machine classification entry
        target_label_object = None
        for current_label in labels_object["labels"]:
            if current_label["labelId"] == label_id:
                target_label_object = current_label

        # initialize if not present
        if not target_label_object:
            target_label_object = {
                "labelId": label_id
            }
            labels_object["labels"].append(target_label_object)

        # set results
        target_label_object["classified"] = int(np.argmax(confidence))
        target_label_object["confidence"] = confidence

        # update mongo db
        comments.update_one({"_id": comment_id}, {"$set": labels_object}, upsert=False)
    end=timer()
    logger.info("Each comment take "+str((start-end)/batch_size)+" seconds of writing time")



        # print output for debug
        # if "labels" in comment:
        #     # pprint.pprint(comment["labels"])
        #     pprint.pprint({"$set": labels_object})
        #     print("----------------")


# batch update db
comment_batch = []
i = 0
for comment in comments.find():

    if not "embedding" in comment:
        continue

    comment_batch.append((comment, comment["embedding"]))
    i += 1

    if i % batch_size == 0:
        process_batch(comment_batch)
        comment_batch = []
        print("comments_processed "+str(i))
        #break

# last batch
if comment_batch:
    process_batch(comment_batch)
