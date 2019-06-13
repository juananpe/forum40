def get(intervall):
    return [
		#// Stage 1
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

		#// Stage 2
		{
			"$project": {
			    "_id" :0,
			    "time" : 1,
			    "sum" :{
			        "$sum" : 1
			    },
			}
		},

		#// Stage 3
		{
			"$group": {
			    "_id" : { 
			        "time" : "$time",
			    },
			    
			    "sum": { "$sum": "$sum" }
			}
		},

		#// Stage 4
		{
			"$sort": {
			    "_id" : 1
			}
		},

		#// Stage 5
		{
			"$project": {
			    "_id" : 0,
			    "time" : "$_id.time",
			    "count" : "$sum"
			}
		},

	]