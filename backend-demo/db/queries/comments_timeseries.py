def _stage1(id):
    if id:
        return  {
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
        return  {
			"$match": {
			    "labels" : {
			        "$elemMatch" : {
			                "manualLabels.label" : 1
			            }
			        }
			    }
		    }

_stage3 = {
            "$sort": {
                    "_id" : 1
                }
            }

def getCommentsGroupedByDay(id):
    return [
		_stage1(id),
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

def getCommentsGroupedByMonth(id):
    return [
		_stage1(id),
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

def getCommentsGroupedByYear(id):
    return [
        _stage1(id),
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