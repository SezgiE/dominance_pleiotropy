import sys
import os
import subprocess
import time
import glob
import shutil

def run_dldsc_pipeline(task_index, sumstats_dir, tmp_dir, out_dir, ldscore_path, dldsc_script):
    
    """Iterates through preprocessed sumstats and runs d-LDSC."""
    os.makedirs(out_dir, exist_ok=True)

    # Find all preprocessed files
    search_pattern = os.path.join(sumstats_dir, "*_gwas_merged.chisq.gz")
    sumstat_files = glob.glob(search_pattern)

    if not sumstat_files:
        print(f"Error: No summary statistic files found in {sumstats_dir}")
        return

    #  Safety check: make sure the task ID isn't higher than the number of files
    if task_index >= len(sumstat_files):
        print(f"Task index {task_index} is out of range. Only {len(sumstat_files)} files found. Exiting.")
        return

    # Pick the ONE specific file for this compute node
    original_file_path = sumstat_files[task_index]

    # Extract phenotype code 
    filename = os.path.basename(original_file_path)
    phenotype = filename.replace("_gwas_merged.chisq.gz", "")

    print(f"--- Running d-LDSC for phenotype: {phenotype} ---")

    # Create a clean workspace in the scratch disk
    task_tmp_dir = os.path.join(tmp_dir, f"ldsc_{phenotype}")
    os.makedirs(task_tmp_dir, exist_ok=False)

    print("Copying input file to $TMPDIR...")
    fast_input_path = os.path.join(task_tmp_dir, filename)
    shutil.copy2(original_file_path, fast_input_path)
    tmp_out_prefix = os.path.join(task_tmp_dir, f"{phenotype}_dom_h2")


    # Dynamically find the path to the legacy environment (Python 2.7) for get_h2.py
    python_exec = os.path.expanduser("~/.conda/envs/d-ldsc-legacy/bin/python")

    # Construct the command using the direct path to the Python 2.7 executable
    dldsc_cmd = f"""
    {python_exec} {dldsc_script} \\
        --additive \\
        --dominance \\
        --ref-ld-chr {ldscore_path} \\
        --w-ld-chr {ldscore_path} \\
        --n-blocks 200 \\
        --write-h2 \\
        --h2 {fast_input_path} \\
        --chisq-max 10000000000 \\
        --out {tmp_out_prefix} \\
        --pheno-name {phenotype}
    """
    start_time = time.time()
    try:
        print("Running d-LDSC...")
        subprocess.run(dldsc_cmd, shell=True, check=True)
        print(f"SUCCESS: d-LDSC analysis completed for {phenotype}")
        
        # Copy all generated files back to the permanent storage
        print("Copying results back to permanent storage...")

        for generated_file in glob.glob(f"{tmp_out_prefix}*"):
            shutil.copy2(generated_file, out_dir)
    
    except subprocess.CalledProcessError as e:
        print(f"ERROR: d-LDSC failed for phenotype {phenotype}. Skipping to next.")

    elapsed_time = time.time() - start_time
    print(f"Finished analysis for {phenotype} in {elapsed_time:.2f} seconds\n")


# ==========================================
# ==========================================


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <task_index> <tmp_dir> <out_dir>")
        sys.exit(1)
        
    task_index = int(sys.argv[1]) - 1 
    
    cluster_tmp_dir = sys.argv[2]
    
    results_dir = sys.argv[3]
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)
    
    sumstats_dir = os.path.join(base_dir, "sumstats_merged")
    d_ld_scores_path = os.path.join(base_dir, "LD_scores", "1000G.EUR.QC.chr@") 
    d_ldsc_script = os.path.join(base_dir, "d-ldsc", "get_h2.py")


    # Call the pipeline
    run_dldsc_pipeline(
        task_index=task_index,
        sumstats_dir=sumstats_dir,
        tmp_dir=cluster_tmp_dir,
        out_dir=results_dir,
        ldscore_path=d_ld_scores_path,
        dldsc_script=d_ldsc_script
    )

