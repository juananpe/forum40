def get(id, intervall):
    return [
		#// Stage 1
		{
			"$match": {
			    "labels" : {
			        "$elemMatch" : {
			                "labelId": id,
			                "manualLabels.label" : 1
			        }
			    }
			}
		},

		#// Stage 2
		{
			"$project": {
			    "_id" : 1,
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
			"$project": {
			    "_id" : 0,
			    "time" : 1,
			    "sum" :{
			        "$sum" : 1
			    },
			}
		},

		#// Stage 4
		{
			"$group": {
			    "_id" : { 
			        "time" : "$time",
			    },
			    
			    "sum": { "$sum": "$sum" }
			}
		},

		#// Stage 5
		{
			"$sort": {
			    "_id" : 1
			}
		},

		#// Stage 6
		{
			"$project": {
			    "_id" : 0,
			    "time" : "$_id.time",
			    "count" : "$sum"
			}
		},

	]