#!/bin/bash
### d-LD Score Calculation - Sezgi Ercan - 09/02/2026

## Reference genome used: "1000G_Phase3_plinkfiles.tgz" from https://doi.org/10.5281/zenodo.10515792
## HapMap3 SNP list used: "w_hm3.snplist.gz" from https://doi.org/10.5281/zenodo.7773502

# Set locale to C for consistent sorting and processing
export LC_ALL=C

# 1. Set the working directory to exactly where this script lives
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR" || exit

echo "Working directory set to: $BASE_DIR"

# 2. Define local paths
HAPMAP3_SNPS="./ref_genome/w_hm3.snplist"
# Keep ld_scores as a subfolder
OUTPUT_DIR="./LD_scores" 

# Cloned d-ldsc repository folder
DLDSC_SCRIPT="./d-ldsc/get_ldscores.py" 

# Create the output directory if it doesn't already exist
mkdir -p "$OUTPUT_DIR"

# 3. Initialize Conda inside a bash script
eval "$(conda shell.bash hook)"
conda activate d-ldsc

# 4. d-LD-Score calculation for each chromosome
echo "Starting d-LD score calculations..."
for i in {1..22}; do
  echo "Processing Chromosome ${i}..."
  python "$DLDSC_SCRIPT" \
    --bfile "./ref_genome/1000G_P3_EUR/1000G.EUR.QC.${i}" \
    --additive \
    --dominance \
    --ld-wind-cm 1 \
    --extract "$HAPMAP3_SNPS" \
    --out "${OUTPUT_DIR}/1000G.EUR.QC.chr${i}"
done

echo "d-LD score calculation is done."
echo "Results are saved in ${OUTPUT_DIR}"