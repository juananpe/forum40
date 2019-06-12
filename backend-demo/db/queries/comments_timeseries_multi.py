def get(ids, intervall):
    return [
		# Stage 1
		{
			"$match": {
				"labels" : {
				    "$elemMatch" : {
			                "labelId": {
			                     "$in": ids,
			                },
			                "manualLabels.label" : 1
			         }
				}
			}
		},

		#// Stage 2
		{
			"$project": {
			    "_id" : 1,
			                        "labels": {
			                            "$map" : {
			                                "input" : {
			                                    "$filter": {
			                                        "input" : "$labels",
			                                        "as" : "label",
			                                        "cond": { "$in": [ "$$label.labelId", ids]}
			                                    }
			                                },
			                                "as": "label",
			                                "in" : {
			                                "value" : "$$label.labelId"}  
			                                }
			                          
			                        },
			                        "time": {
			                            "$subtract": [
			                                { "$toLong": "$timestamp" },
			                                { "$mod": [ { "$toLong": "$timestamp" }, intervall ] }
			                            ]
			                        }
			 }
		},

		#// Stage 3
		{
			"$unwind": {
			    "path" : "$labels",
			    "preserveNullAndEmptyArrays" : False #// optional
			}
		},

		#// Stage 4
		{
			"$project": {
			                        "_id" :1,
			                        "time" : 1,
			                        "label" : "$labels.value",
			                        "sum" :{
			                            "$sum" : 1
			                        },
			                    }
		},

		#// Stage 5
		{
			"$group": {
			                        "_id" : { 
			                            "time" : "$time",
			                        	"label" : "$label"
			                        },
			                        
			                        "sum": { "$sum": "$sum" }
			                    }
		},

		#// Stage 6
		{
			"$sort": {
			                        "_id" : 1
			                    }
		},

		#// Stage 7
		{
			"$project": {
			    "time" : "$_id.time",
			    "label" : "$_id.label",
			    "count" : "$sum",
			    "_id" : 0
			}
		},

	]


