#!/usr/bin/env python3

import json
import argparse

def merge_jsons(json_files, output_file):
    merged_data = []

    # Loop through each JSON file and append its data to the list
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            merged_data.append(data)

    # Save the merged data as a new JSON file
    with open(output_file, 'w') as f:
        json.dump(merged_data, f, indent=4)

    print(f'Merged JSON saved as {output_file}')

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Merge JSON files into a single file with a list as the root object.')
    
    parser.add_argument(
        'json_files', 
        type=str, 
        nargs='+',  # Accepts one or more input files
        help='List of JSON files to merge'
    )
    
    parser.add_argument(
        'output', 
        type=str, 
        help='Output file to save the merged JSON'
    )

    # Parse arguments
    args = parser.parse_args()

    # Merge the JSON files
    merge_jsons(args.json_files, args.output)

if __name__ == "__main__":
    main()

