#!/bin/bash

function get_from_score() {
    "$@" | tail -n 1 | sed 's/Score: \([0-9]*\)\/\([0-9]*\)/\1/' || echo 0
}

get_from_score ./mp2.sh test slab | tee tmp.txt
SLAB=$(cat tmp.txt)
echo "Slab structure grade: $SLAB"

get_from_score ./mp2.sh test func | tee tmp.txt
FUNC=$(cat tmp.txt)
echo "Functionality test grade: $FUNC"

thresh=66

if [[ $FUNC -ge $thresh ]]; then
    echo "Functionality test score is at least $thresh, run bonus test"
    get_from_score ./mp2.sh test list | tee tmp.txt
    LIST=$(cat tmp.txt)
    echo "Bonus (list api): $LIST"
    get_from_score ./mp2.sh test cache | tee tmp.txt
    CACHE=$(cat tmp.txt)
    echo "Bonus (in-cache): $CACHE"
    BONUS=$(( LIST + CACHE ))
else
    echo "Functionality test score is not greater than $thresh, skip bonus test"
    BONUS=0
fi

get_from_score ./mp2.sh test private | tee tmp.txt
PRIVATE=$(cat tmp.txt)
echo "Private test grade: $PRIVATE"

SCORE=$(( SLAB + FUNC + BONUS + PRIVATE ))

if [[ $SCORE -ge 100 ]]; then
    cat test/congratulations.txt
fi

STUDENT_ID=$(cat ./student_id.txt)

echo "Student $STUDENT_ID got score: $SCORE"

echo $SCORE > score.txt
