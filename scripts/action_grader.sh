#!/bin/bash

function get_from_score() {
    "$@" | tail -n 1 | sed 's/Score: \([0-9]*\)\/\([0-9]*\)/\1/' || echo 0
}

get_delay_rate() {
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    exclude_email=shingekinocore@gmail.com

    score="0"
    git log --all --format="%H %ae %ad" | \
    while read commit_hash author_email commit_date; do
        case "$author_email" in
            student*@github.com|"$exclude_email")
                ;;
            *)
                commit_mon=$(echo "$commit_date" | awk '{print $2}')
                commit_day=$(echo "$commit_date" | awk '{print $3}')
                commit_year=$(echo "$commit_date" | awk '{print $5}')
                case "$commit_mon" in
                    Mar) mon_num="03";;
                    Apr) mon_num="04";;
                    *) mon_num="12";;
                esac
                commit_date_num="${commit_year}${mon_num}$(printf "%02d" $commit_day)"
                if [ "$commit_date_num" -le "20250403" ]; then
                    score="1"
                elif [ "$commit_date_num" -eq "20250404" ]; then
                    score="0.8"
                elif [ "$commit_date_num" -eq "20250405" ]; then
                    score="0.6"
                elif [ "$commit_date_num" -eq "20250406" ]; then
                    score="0.4"
                elif [ "$commit_date_num" -eq "20250407" ]; then
                    score="0.2"
                fi
                echo $score
                break
                ;;
        esac
    done
}

LATE_SUBMISSIONT_RATE=$(get_delay_rate)
echo "Late submission rate (in time: 1, decrease 0.2 per late submission day): $LATE_SUBMISSIONT_RATE"

./mp2.sh test slab | tee tmp.txt
SLAB=$(get_from_score cat tmp.txt)
echo "Slab structure grade: $SLAB"
echo

./mp2.sh test func | tee tmp.txt
FUNC=$(get_from_score cat tmp.txt)
echo "Functionality test grade: $FUNC"
echo

thresh=66

if [[ $FUNC -ge $thresh ]]; then
    echo "Functionality test score is at least $thresh, run bonus test"
    echo
    ./mp2.sh test list | tee tmp.txt
    LIST=$(get_from_score cat tmp.txt)
    echo "Bonus (list api): $LIST"
    echo
    ./mp2.sh test cache | tee tmp.txt
    CACHE=$(get_from_score cat tmp.txt)
    echo "Bonus (in-cache): $CACHE"
    echo
else
    echo "Functionality test score is not greater than $thresh, skip bonus test"
    echo
    LIST=0
    CACHE=0
fi

./mp2.sh test private | tee tmp.txt
PRIVATE=$(get_from_score cat tmp.txt)
echo "Private test grade: $PRIVATE"
echo

SCORE=$(awk "BEGIN {print ($SLAB + $FUNC + $LIST + $CACHE + $PRIVATE) * $LATE_SUBMISSIONT_RATE}")

if [[ $SCORE -ge 100 ]]; then
    cat test/congratulations.txt
fi

STUDENT_ID=$(cat ./student_id.txt)

echo "Student $STUDENT_ID got score: $SCORE, record score as:"

echo "student_id,slab,func,list,cache,private,late_submission_rate,score"
echo "$STUDENT_ID,$SLAB,$FUNC,$LIST,$CACHE,$PRIVATE,$LATE_SUBMISSIONT_RATE,$SCORE" | tee -a "${STUDENT_ID}-report.txt"

