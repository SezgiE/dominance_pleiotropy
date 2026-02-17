#!/bin/bash
# Exit immediately if any command exits with a non-zero status
set -e

echo "========================================================"
echo "  Dominance Heritability Estimator based on d-LDSC by Palmer et al. (2023)  "
echo "========================================================"
echo ""

# Initialize conda 
source "$(conda info --base)/etc/profile.d/conda.sh"

# ---------------------------------------------------------
# STEP 0: Repository & Environment Setup
# ---------------------------------------------------------

# 1. Clone the repository if it doesn't exist
if [ ! -d "d-ldsc" ]; then
    echo "d-ldsc repository not found. Cloning..."
    git clone https://github.com/astheeggeggs/d-ldsc.git
else 
    echo "d-ldsc repository already exists. Skipping clone."
fi


# 2. Setup the MAIN environment (Python 3.8 for your data processing)
if ! conda info --envs | grep -q 'main-py3'; then
    echo " -> Creating MAIN environment (Python 3.8)..."

    # Required packages for your main data processing scripts
    PKGS_M="python=3.8 pandas numpy openpyxl xlrd=1.2.0"

    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        conda create -n main-py3 "$PKGS_M" --platform=osx-64 -y
    else
        conda create -n main-py3 "$PKGS_M" -y
    fi

fi


# 3. Setup the environment for LD_score calculation (Python 3.8 with downgraded libaries for get_ldscores.py)
if ! conda info --envs | grep -q 'ld_score-py3'; then
    echo " -> Creating environment for LD Score calculation (Python 3.8 with downgraded libaries)..."

    # Required packages with specific versions for get_ldscores.py
    PKGS_LD="python=3.8 pandas<1.0.0 numpy<1.20 bitarray==2.6.0 
    scipy nose pybedtools openpyxl xlrd==1.2.0"

    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        conda create -n ld_score-py3 "$PKGS_LD" --platform=osx-64 -y
    else
        conda create -n ld_score-py3 "$PKGS_LD" -y
    fi

fi


# 4. Setup the Python 2.7 environment get_h2.py
if ! conda info --envs | grep -q 'd-ldsc-legacy'; then
    echo " -> Creating Python 2.7 environment for d-LDSC heritability calculation (get_h2.py)..."
    
    # Required packages for get_h2.py (Python 2.7 compatible versions)
    PKGS_LEGACY="python=2.7 bitarray scipy numpy pandas pybedtools nose openpyxl xlrd=1.2.0"

    OS_NAME=$(uname -s)
    if [ "$OS_NAME" = "Darwin" ]; then
        # Force Intel architecture on Mac
        CONDA_SUBDIR=osx-64 conda create -n d-ldsc-legacy -c conda-forge -c bioconda -c defaults $PKGS_LEGACY -y

    else
        # Standard native Linux/Cluster installation
        conda create -n d-ldsc-legacy -c conda-forge -c bioconda -c defaults $PKGS_LEGACY -y
    fi
    
fi


# Dynamically grab the paths for your environments
ENV_MAIN=$(conda env list --json | grep "main-py3" | tr -d '", ' | cut -d: -f2)
ENV_LDSC=$(conda env list --json | grep "ld_score-py3" | tr -d '", ' | cut -d: -f2)

# Set the Python executables based on those paths
PYTHON_LDSC="${ENV_LDSC}/bin/python"
PYTHON_MAIN="${ENV_MAIN}/bin/python"

echo " -> Environments successfully verified!"
echo ""


# ---------------------------------------------------------
# STEP 1: LD Scores
# ---------------------------------------------------------
read -p "1. Do you already have the calculated LD and d-LD scores? (y/n): " has_ld
if [[ "$has_ld" =~ ^[Nn]$ ]]; then
   
    echo " -> Running get_d-LD_scores.py..."
    $PYTHON_LDSC get_ldscores.py

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
    $PYTHON_MAIN get_sumStats.py

else
    echo " -> Skipping summary statistics download and merging."
fi
echo ""


# ---------------------------------------------------------
# STEP 3: Heritability Calculation
# ---------------------------------------------------------
echo "3. Starting dominance heritability calculations..."

$PYTHON_MAIN get_dominance_heritability.py

echo " -> Heritability calculations complete."
echo ""


# ---------------------------------------------------------
# STEP 4: Compile Results
# ---------------------------------------------------------
echo "4. Compiling .h2 files into a single CSV..."

$PYTHON_MAIN compile_h2_results.py

echo "========================================================"
echo " PIPELINE COMPLETE! Your final results are ready. "
echo "========================================================"

