from db import mongo

#comments
def getCommentsByQuery(query):
    coll = mongo.db.Comments
    return coll.find(query)

def getCommentById(oid):
    coll = mongo.db.Comments
    try:
        return coll.find_one({"_id" : oid})
    except:
        return {"msg": "{} is not a valid ObjectId".format(str(id))}, 400

# label
def getLabelIdByName(name):
    coll = mongo.db.Labels
    label = coll.find_one({"description" : name}, {"_id": 1})
    return label["_id"] if label else None

# auth

