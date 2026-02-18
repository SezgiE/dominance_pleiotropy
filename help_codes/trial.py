import os
import shutil

# 1. Setup your paths
os.chdir("/Users/sezgi/Documents/dominance_heritability")  # Ensure we're in the script's directory

input_dir = "./ref_genome/1000G_EUR_Phase3"  # Folder where your .bim files live
output_file = "./ref_genome/1000G_merged_all.txt"
file_prefix = "1000G.EUR.QC"             # The part of the name before the chromosome number

print(f"Starting merge into: {output_file}")

header = b"CHR\trsid\tCM\tBP\tA1\tA2\n"

# 2. Open the master output file in 'append' or 'write' mode
with open(output_file, 'wb') as outfile:
    
    outfile.write(header)
    
    # Loop through Chromosomes 1 to 22
    for i in range(1, 23):
        # Construct the exact file name (e.g., 1000G.EUR.QC.1.bim)
        bim_path = f"{input_dir}/{file_prefix}.{i}.bim"
        
        if os.path.exists(bim_path):
            print(f"Merging Chromosome {i}...")
            # Stream the data directly from the input to the output
            with open(bim_path, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)
        else:
            print(f"WARNING: File not found - {bim_path}")

print("\nSuccess! All .bim files have been merged.")


    raw_data = subprocess.check_output(['conda', 'env', 'list', '--json'])
    envs = json.loads(raw_data)['envs']
    python_exec = next(os.path.join(p, "bin/python") for p in envs if "d-ldsc-legacy" in p)