#!/bin/sh
# for i in metacomment
# do
#   python updateLabel.py --labelname $i
# done



#sentimentnegative sentimentpositive sentimentneutral inappropriate discriminating possiblyfeedback personalstories argumentsused meta-comment


for i in offtopic sentimentnegative sentimentpositive sentimentneutral inappropriate discriminating possiblyfeedback personalstories argumentsused meta-comment
do
  python MeasurePerformance.py --labelname $i
done
