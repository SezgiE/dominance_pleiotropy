import json
import os
import subprocess
import time
import glob

def run_dldsc_pipeline(sumstats_dir, out_dir, ldscore_path, dldsc_script):
    
    """Iterates through preprocessed sumstats and runs d-LDSC."""
    os.makedirs(out_dir, exist_ok=True)

    # Find all preprocessed files
    search_pattern = os.path.join(sumstats_dir, "*_gwas_merged.chisq.gz")
    sumstat_files = glob.glob(search_pattern)

    if not sumstat_files:
        print(f"Error: No summary statistic files found in {sumstats_dir}")
        return

    print(f"Found {len(sumstat_files)} traits to analyze. Starting d-LDSC pipeline...\n")

    for file_path in sumstat_files:
        start_time = time.time()

        # Extract phenotype code 
        filename = os.path.basename(file_path)
        phenotype = filename.replace("_gwas_merged.chisq.gz", "")

        print(f"--- Running d-LDSC for phenotype: {phenotype} ---")

        out_prefix = os.path.join(out_dir, f"{phenotype}_dom_h2")

        # Dynamically find the path to the legacy environment (Python 2.7) for get_h2.py
        raw_data = subprocess.check_output(['conda', 'env', 'list', '--json'])
        envs = json.loads(raw_data)['envs']
        python_exec = next(os.path.join(p, "bin/python") for p in envs if "d-ldsc-legacy" in p)

        # Construct the command using the direct path to the Python 2.7 executable
        dldsc_cmd = f"""
        {python_exec} {dldsc_script} \\
            --additive \\
            --dominance \\
            --ref-ld-chr {ldscore_path} \\
            --w-ld-chr {ldscore_path} \\
            --n-blocks 200 \\
            --write-h2 \\
            --h2 {file_path} \\
            --chisq-max 10000000000 \\
            --out {out_prefix} \\
            --pheno-name {phenotype}
        """

        try:
            # Run the command assuming the environment is already properly configured
            subprocess.run(dldsc_cmd, shell=True, check=True)
            print(f"SUCCESS: d-LDSC analysis completed for {phenotype}")
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: d-LDSC failed for phenotype {phenotype}. Skipping to next.")

        elapsed_time = time.time() - start_time
        print(f"Finished analysis for {phenotype} in {elapsed_time:.2f} seconds\n")


# ==========================================
# ==========================================


if __name__ == "__main__":
    
    # 1. Set working directory where this script is located
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)
    
    # 2. Define relative paths
    sumstats_dir = os.path.join(base_dir, "sumstats_merged")
    results_dir = os.path.join(base_dir, "ldsc_results")
    
    # Matches the output folder from get_d-LD_scores.sh
    d_ld_scores_path = os.path.join(base_dir, "LD_scores", "1000G.EUR.QC.chr@") 
    
    # Points to your cloned repository
    d_ldsc_script = os.path.join(base_dir, "d-ldsc", "get_h2.py")

    # 3. Call the pipeline
    run_dldsc_pipeline(
        sumstats_dir=sumstats_dir,
        out_dir=results_dir,
        ldscore_path=d_ld_scores_path,
        dldsc_script=d_ldsc_script
    )

