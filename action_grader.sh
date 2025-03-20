#!/bin/bash

function get_from_score() {
    "$@" | tail -n 1 | sed 's/Score: \([0-9]*\)\/\([0-9]*\)/\1/' || echo 0
}

./mp2.sh test slab | tee tmp.txt
SLAB=$(get_from_score cat tmp.txt)
echo "Slab structure grade: $SLAB"

./mp2.sh test func | tee tmp.txt
FUNC=$(get_from_score cat tmp.txt)
echo "Functionality test grade: $FUNC"

thresh=66

if [[ $FUNC -ge $thresh ]]; then
    echo "Functionality test score is at least $thresh, run bonus test"
    ./mp2.sh test list | tee tmp.txt
    LIST=$(get_from_score cat tmp.txt)
    echo "Bonus (list api): $LIST"
    ./mp2.sh test cache | tee tmp.txt
    CACHE=$(get_from_score cat tmp.txt)
    echo "Bonus (in-cache): $CACHE"
    BONUS=$(( LIST + CACHE ))
else
    echo "Functionality test score is not greater than $thresh, skip bonus test"
    BONUS=0
fi

./mp2.sh test private | tee tmp.txt
PRIVATE=$(get_from_score cat tmp.txt)
echo "Private test grade: $PRIVATE"

SCORE=$(( SLAB + FUNC + BONUS + PRIVATE ))

if [[ $SCORE -ge 100 ]]; then
    cat test/congratulations.txt
fi

STUDENT_ID=$(cat ./student_id.txt)

echo "Student $STUDENT_ID got score: $SCORE"

echo $SCORE > score.txt
