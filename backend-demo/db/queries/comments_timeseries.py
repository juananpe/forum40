from datetime import datetime

_stage0 = {
	"$match" : {
		"labels": {"$exists": 1}
	}
}

def _stage1(id, keywords):
    query = {}
    if id:
        query = {
    		"$match": {
				"timestamp" : { "$gt" : datetime.strptime('2015-05-31-22','%Y-%m-%d-%H'), "$lt" : datetime.strptime('2016-05-31-22','%Y-%m-%d-%H') },
			    "labels" : {
			        "$elemMatch" : {
			                "labelId": id,
								"$or" : [ 
									{ "manualLabels.label" : 1}, 
									{ "$and" : 
										[{"classified" : 0}, {"confidence" : {"$ne" : []}}]}
									]
								}
							}
						}
					}
    else:
        query = {
			"$match": { 
				"timestamp" : { "$gt" : datetime.strptime('2015-05-31-22','%Y-%m-%d-%H'), "$lt" : datetime.strptime('2016-05-31-22','%Y-%m-%d-%H') },
            }
		}

    if keywords:
        searchwords = " ".join(x for x in keywords)
        textFilter_query = { 
            "$search" : searchwords,
            "$caseSensitive": False
        }
        query["$match"]["$text"] = textFilter_query
    return query

_stage3 = {
            "$sort": {
                    "_id" : 1
                }
            }

def getCommentsGroupedByDay(id, keywords):
    return [
		_stage0,
		_stage1(id, keywords),
		{
			"$group": {
			    "_id":{
			      "year":{"$year":{"date":"$timestamp","timezone":"Europe/Berlin"}},
			      "month":{"$month":{"date":"$timestamp","timezone":"Europe/Berlin"}},
			      "dayOfMonth":{"$dayOfMonth":{"date":"$timestamp","timezone":"Europe/Berlin"}}
			    },
			    "count":{"$sum":1}
			 }
		},
        _stage3
	]

def getCommentsGroupedByMonth(id, keywords):
    return [
		_stage0,
		_stage1(id, keywords),
		{
			"$group": {
			    "_id":{
			      "year":{"$year":{"date":"$timestamp","timezone":"Europe/Berlin"}},
			      "month":{"$month":{"date":"$timestamp","timezone":"Europe/Berlin"}},
			    },
			    "count":{"$sum":1}
			 }
		},
        _stage3
	]

def getCommentsGroupedByYear(id, keywords):
    return [
		_stage0,
        _stage1(id, keywords),
		{
			"$group": {
			    "_id":{
			      "year":{"$year":{"date":"$timestamp","timezone":"Europe/Berlin"}},
			    },
			    "count":{"$sum":1}
			 }
		},
        _stage3
	]