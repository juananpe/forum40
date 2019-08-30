#!/bin/sh
for i in sentimentpositive sentimentneutral inappropriate discriminating possiblyfeedback personalstories argumentsused meta-comment
do
  python updateLabel.py --labelname $i
done

#sentimentnegative sentimentpositive sentimentneutral inappropriate discriminating possiblyfeedback personalstories argumentsused meta-comment
