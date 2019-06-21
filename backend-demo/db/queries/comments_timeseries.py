def _stage1(id, keywords):
    query = {}
    if id:
        query = {
    		"$match": {
			    "labels" : {
			        "$elemMatch" : {
			                "labelId": id,
			                "manualLabels.label" : 1
			            }
			        }
			    }
		    }
    else:
        query = {
			"$match": { 
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