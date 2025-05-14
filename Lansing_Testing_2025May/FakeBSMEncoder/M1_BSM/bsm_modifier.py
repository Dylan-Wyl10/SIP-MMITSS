# bsm_modifier.py
import os

def modify_bsm_file(input_path):
    # Create output filename
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_v2{ext}"

    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            line = line.strip()
            if "9d136" in line:
                line = line.replace("9d136", "9d236", 1)  # Replace only first occurrence
            outfile.write(line + '\n')
            
input_file = "Warren_N2S.txt"
modify_bsm_file(input_file)
