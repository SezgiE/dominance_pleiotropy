#!/usr/bin/env python3
# d-LD Score Calculation - Sezgi Ercan - 09/02/2026
# Reference genome & HapMap3 SNP list used: https://doi.org/10.5281/zenodo.10515792

import os
import sys
import subprocess


# Set locale to C for consistent sorting and processing
os.environ['LC_ALL'] = 'C'

# 1. Set the working directory to exactly where this script lives
base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
print(f"Working directory set to: {base_dir}")

# 2. Define local paths
hapmap3_snps = "./ref_genome/hm3_no_MHC_MAF_01_INFO_9_rsID.txt"
output_dir = "./LD_scores" 
dldsc_script = "./d-ldsc/get_ldscores.py" 

# Create the output directory if it doesn't already exist
os.makedirs(output_dir, exist_ok=True)

# 3. d-LD-Score calculation for each chromosome

print("Starting d-LD score calculations...")

for i in range(1, 23):
    print(f"Processing Chromosome {i}...")
    cmd = [
        sys.executable, dldsc_script,
        "--bfile", f"./ref_genome/1000G_EUR_Phase3/1000G.EUR.QC.{i}",
        "--additive",
        "--dominance",
        "--ld-wind-cm", "1",
        "--extract", hapmap3_snps,
        "--out", f"{output_dir}/1000G.EUR.QC.chr{i}"
    ]
    subprocess.run(cmd, check=True)

print("d-LD score calculation is done.")
print(f"Results are saved in {output_dir}")