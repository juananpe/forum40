import pymongo, keras, fastText
from utils import concat
import numpy as np

def process_batch(comment_batch):
    print(comment_batch)
    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]

    # do stuff here ...
    offlang_labels = classify(comment_texts)

    for i, label in enumerate(offlang_labels):

        # get label object id
        comment_id = comment_batch[i]["_id"]

        # initialize labels field for comment
        if "labels" in comment_batch[i]:
            labels_object = {"labels" : comment_batch[i]["labels"]}
        else:
            labels_object = {"labels" : []}

        # remove existing labels of current label object id
        new_labels_list = []
        for l in labels_object["labels"]:
            if l["labelId"] != label_id:
                new_labels_list.append(l)
        labels_object["labels"] = new_labels_list

        # add new label classification
        confidence = label["confidence"]
        labels_object["labels"].append(
            {
                "labelId" : label_id,
                "classified" : int(np.argmax(confidence)),
                "confidence" : confidence
            }
        )

        # update mongo db
        comments.update_one({"_id": comment_id}, {"$set": labels_object}, upsert=False)

    # debug
    print(offlang_labels)


client = pymongo.MongoClient("localhost", 27017)
db = client.omp

labels = db.Labels

# db.getCollection("Labels").find({"classname" : "offtopic"})
# db.getCollection("Comments").find({"labels.labelId" : ObjectId("5cadf564694377c8a2f450d5")})


label_id = labels.insert_one(offlang_label).inserted_id


comments = db.Comments

comment_batch = []
batch_size=100
i = 0
for comment in comments.find():
    comment_batch.append(comment)
    i += 1
    if i % batch_size == 0:
        process_batch(comment_batch)
        comment_batch = []
        # break

if comment_batch:
    process_batch(comment_batch)