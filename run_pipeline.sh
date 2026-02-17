#!/bin/bash
# Force this specific script to use the right Python and Conda
unset PYTHONPATH
unset PYTHONHOME
source /sw/arch/RHEL9/EB_production/2025/software/Miniconda3/25.5.1-1/etc/profile.d/conda.sh

# Exit immediately if any command exits with a non-zero status
set -e

echo "========================================================"
echo "  Dominance Heritability Estimator based on d-LDSC by Palmer et al. (2023)  "
echo "========================================================"
echo ""

# ---------------------------------------------------------
# STEP 0: Repository & Environment Setup
# ---------------------------------------------------------
eval "$(conda shell.bash hook)"

# 1. Clone the repository if it doesn't exist
if [ ! -d "d-ldsc" ]; then
    echo "0. d-ldsc repository not found. Cloning..."
    git clone https://github.com/astheeggeggs/d-ldsc.git
fi

# 2. Setup the MAIN environment (Python 3.8 for your data processing)
if ! conda info --envs | grep -q 'main-py3'; then
    echo " -> Creating MAIN environment (Python 3.8)..."

    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        conda create -n main-py3 python=3.8 --platform=osx-64 -y
    else
        conda create -n main-py3 python=3.8 -y
    fi
    conda activate main-py3
    pip install "pandas" "numpy" "openpyxl" "xlrd==1.2.0"
    conda deactivate
fi

# 3. Setup the environment for LD_score calculation (Python 3.8 with downgraded libaries for get_ldscores.py)
if ! conda info --envs | grep -q 'ld_score-py3'; then
    echo " -> Creating environment for LD Score calculation (Python 3.8 with downgraded libaries)..."

    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        conda create -n ld_score-py3 python=3.8 --platform=osx-64 -y
    else
        conda create -n ld_score-py3 python=3.8 -y
    fi
    conda activate ld_score-py3
    pip install "pandas<1.0.0" "numpy<1.20" "bitarray==2.6.0" "scipy" "nose" "pybedtools" "openpyxl" "xlrd==1.2.0"
    conda deactivate
fi

# 4. Setup the Python 2.7 environment get_h2.py
if ! conda info --envs | grep -q 'd-ldsc-legacy'; then
    echo " -> Creating Python 2.7 environment for d-LDSC heritability calculation (get_h2.py)..."
    
    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        # Force Intel architecture on Mac
        CONDA_SUBDIR=osx-64 conda create -n d-ldsc-legacy -c conda-forge -c bioconda -c defaults python=2.7 bitarray scipy numpy pandas pybedtools nose openpyxl xlrd=1.2.0 -y
        
        # Lock the environment to osx-64 so future package updates don't break it
        conda run -n d-ldsc-legacy conda config --env --set subdir osx-64
    else
        # Standard native Linux/Cluster installation
        conda create -n d-ldsc-legacy -c conda-forge -c bioconda -c defaults python=2.7 bitarray scipy numpy pandas pybedtools nose openpyxl xlrd=1.2.0 -y
    fi
fi

echo " -> Environments successfully verified!"
echo ""


# ---------------------------------------------------------
# STEP 1: LD Scores
# ---------------------------------------------------------
read -p "1. Do you already have the calculated LD and d-LD scores? (y/n): " has_ld
if [[ "$has_ld" =~ ^[Nn]$ ]]; then
    echo " -> Running get_d-LD_scores.sh..."
    conda activate ld_score-py3
    bash get_d-LD_scores.sh
    conda deactivate
else
    echo " -> Skipping LD score calculation."
fi
echo ""


# ---------------------------------------------------------
# STEP 2: Summary Statistics
# ---------------------------------------------------------
read -p "2. Do you already have the merged summary statistics? (y/n): " has_sumstats
if [[ "$has_sumstats" =~ ^[Nn]$ ]]; then
    echo " -> Running get_sumStats.py..."
    conda run -n main-py3 python get_sumStats.py
else
    echo " -> Skipping summary statistics download and merging."
fi
echo ""


# ---------------------------------------------------------
# STEP 3: Heritability Calculation
# ---------------------------------------------------------
echo "3. Starting dominance heritability calculations..."
# The wrapper script runs in Python 3, but triggers the Python 2.7 environment internally
conda run -n main-py3 python get_dominance_heritability.py
echo " -> Heritability calculations complete."
echo ""


# ---------------------------------------------------------
# STEP 4: Compile Results
# ---------------------------------------------------------
echo "4. Compiling .h2 files into a single CSV..."
conda run -n main-py3 python compile_h2_results.py

echo "========================================================"
echo " PIPELINE COMPLETE! Your final results are ready. "
echo "========================================================"