#!/bin/bash

archive_filename=$1
input_dir="/tmp/website-report-$(date +%s)/"
output_dir="/tmp/wpscan-api-results-$(date +%s)/"

if [[ $(echo $archive_filename | grep tar) == '' ]]; then
	echo "Specify .tar file"
	exit 1
fi

mkdir $input_dir
mkdir $output_dir
tar -xf "$archive_filename" -C $input_dir 
input_dir="$input_dir/website_report/"

readarray -t file_names < <(ls "$input_dir")

echo "Analyzing:"
for file_name in ${file_names[@]}; do
    if [[ $(echo $file_name | grep -P '\.json$') == '' ]]; then
        continue
    fi

    input_file="${input_dir}${file_name}"
    output_file="${output_dir}${file_name}"
    wpscan-api.py $input_file | tee "${output_file}" | head -c 50
    echo
done

echo "Uploading:"
readarray -t file_names < <(ls "$output_dir")
for file_name in "${file_names[@]}"; do
    if [[ $(echo $file_name | grep -P '\.json$') == '' ]]; then
        continue
    fi  
    name_postfix=$(echo "$file_name" | cut -d '.' -f1)
    output_file="${output_dir}${file_name}"
    if [[ $engagement_id == '' ]]; then
        engagement_id=$(dojo-upload.sh -f $output_file -t "Wpscan API Scan" \
            -p "Casino Website" | grep 'Engagement: ' | cut -d ' ' -f2)
    else
        dojo-upload.sh -f $output_file -t "Wpscan API Scan" -p "Casino Website" -e $engagement_id \
            | tail -n 1 | head -c 50
        echo
    fi
done

