def get(id, intervall):
    return [
                # Stage 1
                {
                    "$match": {
                        "labels.labelId" : id,
                    }
                },

                # Stage 2
                {
                    "$project": {
                        "_id" : 1,
                        "labels": {
                            "$map" : {
                                "input" : {
                                    "$filter": {
                                        "input" : "$labels",
                                        "as" : "label",
                                        "cond": { "$eq": [ "$$label.labelId", id]}
                                    }
                                },
                                "as": "label",
                                "in" : {
                                "value" : { "$arrayElemAt": ["$$label.manualLabels.label", 0 ]}  
                                }
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

                # Stage 3
                {
                    "$unwind": {
                        "path" : "$labels",
                    }
                },

                # Stage 4
                {
                    "$project": {
                        "_id" :1,
                        "time" : 1,
                        "sum" :{
                            "$sum" : 1
                        },
                        "pos": {
                            "$cond": [ { "$eq": ["$labels.value", 1 ] }, 1, 0]
                        }
                    }
                },

                # Stage 5
                {
                    "$group": {
                        "_id" : "$time",
                        "pos": { "$sum": "$pos" },
                        "sum": { "$sum": "$sum" }
                    }
                },

                # Stage 6
                {
                    "$addFields": {
                        "neg" : { "$subtract": [ "$sum", "$pos" ] }
                    }
                },

                # Stage 7
                {
                    "$sort": {
                        "_id" : 1
                    }
                },

            ]

