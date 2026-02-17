#!/bin/bash
#SBATCH --job-name=dLDSC_pipeline
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --output=pipeline_%j.out
#SBATCH --error=pipeline_%j.err

# 1. Unlock the tools and put Conda in a Hazmat suit
module load 2025
module load Miniconda3/25.5.1-1

# 1. Clone the repository if it doesn't exist
if [ ! -d "d-ldsc" ]; then
    echo "0. d-ldsc repository not found. Cloning..."
    git clone https://github.com/astheeggeggs/d-ldsc.git
fi

# 2. Bring ingredients to the kitchen prep table ($TMPDIR)
echo "Copying data to scratch..."
cp -r /home/sercan/dominance/dominance_pleiotropy/* "$TMPDIR"/

# 3. Move to the prep table
cd "$TMPDIR"

# 4. Cook the meal!
echo "Running the master pipeline..."
echo -e "y\ny\n" | ./run_pipeline.sh

# 5. Get the results
echo "Saving results..."
rsync -av "$TMPDIR"/LD_scores/ /home/sercan/dominance/dominance_pleiotropy/LD_scores/
rsync -av "$TMPDIR"/ldsc_results/ /home/sercan/dominance/dominance_pleiotropy/ldsc_results/
rsync -av "$TMPDIR"/sumstats_merged/ /home/sercan/dominance/dominance_pleiotropy/sumstats_merged/
rsync -v "$TMPDIR"/*.csv /home/sercan/dominance/dominance_pleiotropy/