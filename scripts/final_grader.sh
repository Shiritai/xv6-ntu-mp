#!/bin/bash

RESULT=result
mkdir -p $RESULT
test_cnt=20

function sanitize_newlines() {
    local input="$1"
    printf '%s' "${input//[$'\n\r\t']/}"
}

function get_from_score() {
    res=$("$@" | tail -n 1 | sed 's/Score: \([0-9]*\)\/\([0-9]*\)/\1/' || echo 0)
    sanitize_newlines $res
}

export -f sanitize_newlines
export -f get_from_score

if [[ "$OSTYPE" == "darwin"* ]]; then
    cpus=$(sysctl -n hw.ncpu)
else
    cpus=$(nproc)
fi

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

test_item(){
    item=$1
    save_file="$RESULT/$item.txt"
    export FINAL_GRADE=1
    ./mp2.sh test "$item" > "$save_file"
    res=$(get_from_score cat "$save_file")
    echo "$res"
}

test_items(){
    item=$1
    from=$2
    to=$3
    expected=$4

    save_dir="${RESULT}/${item}"
    mkdir -p "$save_dir"
    res=0
    for turn in $(seq "$from" "$to"); do
        cur=0
        save_turn_dir="${save_dir}/${turn}"
        mkdir -p "$save_turn_dir"

        while read _cur; do
            cur=$(awk "BEGIN {print ${cur} + ${_cur}}")
        done < <(
            seq $test_cnt | xargs -P "$cpus" -I {} bash -c \
                'save_file='$save_turn_dir'/{}.txt; \
                export FINAL_GRADE=1; \
                ./mp2.sh test '$item' '$turn' > $save_file; \
                echo $(get_from_score cat $save_file)'
        )

        cur=$(awk "BEGIN {print ${cur} / ${test_cnt}}")
        echo "Score for $item (case $turn): $cur" > "$save_turn_dir/result.txt"
        res=$(awk "BEGIN {print $res + $cur}")

        if awk "BEGIN {exit !($cur == 0)}"; then
            echo "Case $turn is completely failed, score: $cur" >> "$save_dir/result.txt"
        elif awk "BEGIN {exit !($cur < $expected)}"; then
            echo "Case $turn is partially passed, score: $cur" >> "$save_dir/result.txt"
        fi
    done
    echo "$res"
}

LATE_SUBMISSION_RATE=$(get_delay_rate)
echo "Late submission rate (in time: 1, decrease 0.2 per late submission day): $LATE_SUBMISSION_RATE"

SLAB=$(test_item slab)
echo "Slab structure grade: $SLAB"

FUNC=$(test_items func 0 24 3)
echo "Functionality test grade: $FUNC"

thresh=66

if awk "BEGIN {exit !($FUNC >= $thresh)}"; then
    echo "Functionality test score is at least $thresh, run bonus test"

    LIST=$(test_item list)
    echo "Bonus (list api): $LIST"

    CACHE=$(test_item cache)
    echo "Bonus (in-cache): $CACHE"
else
    echo "Functionality test score is not greater than $thresh, skip bonus test"
    LIST=0
    CACHE=0
fi

if [[ -d test/private ]]; then
    PRIVATE=$(test_items private 0 3 5)
    echo "Private test grade: $PRIVATE"
else
    PRIVATE=0
    echo "Private test directory DNE!"
fi

SCORE=$(awk "BEGIN {print ($SLAB + $FUNC + $LIST + $CACHE + $PRIVATE) * $LATE_SUBMISSION_RATE}")

if awk "BEGIN {exit !($SCORE >= 100)}"; then
    cat test/congratulations.txt
fi

STUDENT_ID=$(sanitize_newlines "$(cat ./student_id.txt)")

echo "Student $STUDENT_ID got score: $SCORE, record score as:"

echo "student_id,slab,func,list,cache,private,late_submission_rate,score"
echo "$STUDENT_ID,$SLAB,$FUNC,$LIST,$CACHE,$PRIVATE,$LATE_SUBMISSION_RATE,$SCORE" | tee -a "${STUDENT_ID}-report.txt"

