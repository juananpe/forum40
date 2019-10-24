import pymongo, keras, fastText
from forum import concat, classify
import numpy as np

def process_batch(comment_batch):
    print(comment_batch)
    comment_texts = [concat(c["title"], c["text"]) for c in comment_batch]
    offlang_labels = classify(model, ft, comment_texts, OFFLANG_CLASSES)
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

offlang_label = {
    "type" : "binary",
    "classname" : [
        "other",
        "offensive"
    ],
    "description" : "offensive language",
    "scale" : "ordinal",
    "staffId" : ""
}

label_id = labels.insert_one(offlang_label).inserted_id


OFFLANG_CLASSES = ["other", "offensive"]
print("Loading fasttext model")
ft = fastText.load_model("model/wiki.de.bin")
print("Loading keras model")
model: keras.Model = keras.models.load_model("model/classification_model_tl_twitterclasses7m_1000_suf_bu.h5")
model._make_predict_function()

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