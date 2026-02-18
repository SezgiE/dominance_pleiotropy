#!/bin/bash
#SBATCH --job-name=gwas_process
#SBATCH --time=02:00:00
#SBATCH --array=1-1030%50
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16        
#SBATCH --mem=28G               
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err

# 1. Unlock the tools and put Conda
PYTHON_EXEC="$HOME/.conda/envs/main-py3/bin/python"

# Set up paths
HOME_DIR="/home/sercan/dominance/dominance_pleiotropy"
OUT_DIR="$HOME_DIR/sumstats_merged"

# Ensure the final output directory exists safely before the jobs run wild
mkdir -p "$OUT_DIR"

echo "Task $SLURM_ARRAY_TASK_ID starting..."

# 1. Run Python from your home directory, but tell it to use $TMPDIR for the heavy lifting
cd "$HOME_DIR"

# Pass the $TMPDIR and the final output directory to your Python script
"$PYTHON_EXEC" snellius_download.py $SLURM_ARRAY_TASK_ID "$TMPDIR" "$OUT_DIR"