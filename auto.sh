#!/bin/bash

archive_filename=$1
directory="/var/lib/wp-scripts"
output_filename="$directory/output_results-$(date +%s).json"
input_dir="$directory/website-report-$(date +%s)/"
output_dir="$directory/wpscan-api-results-$(date +%s)/"

if [[ $(echo $archive_filename | grep tar) == '' ]]; then
	echo "Specify .tar file"
	exit 1
fi
mkdir $input_dir
mkdir $output_dir
tar -xf "$archive_filename" -C $input_dir 
input_dir="${input_dir}website_report/success/"

readarray -t file_names < <(ls "$input_dir")

echo "Analyzing:"
for file_name in ${file_names[@]}; do
    if [[ $(echo $file_name | grep -P '\.json$') == '' ]]; then
        continue
    fi

    input_file="${input_dir}${file_name}"
    output_file="${output_dir}${file_name}"
    /opt/wpscan-api/wpscan-api.py $input_file > "${output_file}"
    tail -c 80 "${output_file}"
done

echo "Creating result file ($output_filename):"
readarray -t file_names < <(ls "$output_dir")
for file_name in "${file_names[@]}"; do
    if [[ $(echo $file_name | grep -P '\.json$') == '' ]]; then
        continue
    fi  
    output_file="${output_dir}${file_name}"
    cat "$output_file" | tr '\n' ' ' >> $output_filename 
    echo -n ',' >> $output_filename

    #if [[ $engagement_id == '' ]]; then
    #    engagement_id=$(dojo-upload.sh -f $output_file -t "Wpscan API Scan" \
    #        -p "Casino Website" | grep 'Engagement: ' | cut -d ' ' -f2)
    #else
    #    dojo-upload.sh -f $output_file -t "Wpscan API Scan" -p "Casino Website" -e $engagement_id \
    #        | tail -n 1 | head -c 50
    #    echo
    #fi
done

output_file_content=$(cat "$output_filename")
echo "$output_file_content" | sed 's/^/[/g' | sed 's/,$/]/g' > $output_filename

echo "Uploading results: "
/opt/useful-scripts/dojo-upload.sh -f $output_filename -t "Wpscan API Scan" -p "Casino Website"
