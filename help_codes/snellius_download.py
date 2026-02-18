import os
import sys
import time
import shutil
import subprocess
import pandas as pd


def load_wget_commands(add_file_path, dom_file_path):
    # Load the additive and dominance Excel files
    a_df = pd.read_excel(add_file_path)
    d_df = pd.read_excel(dom_file_path)
    
    # Create dictionaries mapping phenotype_code -> wget command
    add_wget_dict = dict(zip(a_df['phenotype_code'], a_df['wget']))
    dom_wget_dict = dict(zip(d_df['phenotype_code'], d_df['wget']))
    
    # Convert keys to sets for highly efficient comparison
    a_codes_set = set(add_wget_dict.keys())
    d_codes_set = set(dom_wget_dict.keys())
    
    # Check  both files have the exact same phenotype codes
    if a_codes_set != d_codes_set:
        missing_in_d = a_codes_set - d_codes_set
        missing_in_a = d_codes_set - a_codes_set
        raise ValueError(
            f"Error: Phenotype codes do not match between files!\n"
            f"Codes missing in Dominance file: {missing_in_d}\n"
            f"Codes missing in Additive file: {missing_in_a}"
        )
    
        # Sort the phenotype codes for consistent processing order
    phenotype_codes = sorted(list(a_codes_set))
    
    return add_wget_dict, dom_wget_dict, phenotype_codes


def execute_wget(wget_cmd, output_dir):
    """Executes wget and returns the exact path to the downloaded file."""
    # Extract filename defined after '-O '
    filename = wget_cmd.split('-O ')[-1].strip()
    filepath = os.path.join(output_dir, filename)
    
    # Execute download securely
    subprocess.run(wget_cmd, shell=True, cwd=output_dir, check=True)
    return filepath


def preprocess_sumstats(file_add, file_dom, file_ref, file_out):
    """
    Merges additive and dominance summary statistics and filters them down to the  HapMap3 variants.
    """
    print("1. Loading HapMap3 SNP list...")
    hapmap3 = pd.read_csv(file_ref, sep='\t', usecols=['variant', 'A1', 'A2', 'SNP'])
    
    print("2. Loading Additive GWAS SumStats...")
    data_add = pd.read_csv(
        file_add, 
        sep='\t', 
        compression='gzip', 
        usecols=['variant', 'n_complete_samples', 'tstat']
    ).rename(columns={'n_complete_samples': 'N', 'tstat': 'Z_A'})
    
    print("3. Loading Dominance GWAS SumStats...")
    data_dom = pd.read_csv(
        file_dom, 
        sep='\t', 
        compression='gzip', 
        usecols=['variant', 'dominance_tstat']
    ).rename(columns={'dominance_tstat': 'Z_D'})
    
    print("4. Merging data...")
    data_merged = pd.merge(data_add, data_dom, on='variant', how='inner')
    data_final = pd.merge(hapmap3, data_merged, on='variant', how='inner')
    
    print("5. Formatting and saving...")
    # Drop any rows with missing t-statistics (if any)
    data_final = data_final.dropna(subset=['Z_A', 'Z_D'])
    
    # Select final columns in the exact order d-ldsc expects
    data_out = data_final[['SNP', 'A1', 'A2', 'Z_A', 'Z_D', 'N']]
    
    # Write to a gzipped file
    data_out.to_csv(file_out, sep='\t', index=False, compression='gzip')
    
    print(f"Done! Saved {len(data_out)} SNPs to {file_out}")


def run_single_trait(task_index, add_excel, dom_excel, ref_file, temp_dir, output_dir):
    """Executes the pipeline for ONE specific trait based on the SLURM array index."""
    
    os.makedirs(output_dir, exist_ok=True)
    add_dict, dom_dict, phenotype_codes = load_wget_commands(add_excel, dom_excel)
    
    # Grab ONLY the phenotype assigned to this specific array task
    try:
        code = phenotype_codes[task_index]
    except IndexError:
        print(f"Task index {task_index} is out of range. Exiting.")
        return

    # Create a UNIQUE temporary directory just for this trait so parallel jobs don't clash
    temp_dir = f"./temp_sumstats_{code}"
    os.makedirs(temp_dir, exist_ok=True)
    
    start_time = time.time()
    print(f"--- Starting workflow for phenotype: {code} ---")
    
    add_filepath, dom_filepath = None, None
    
    try:
        print("Downloading summary statistics...")
        add_filepath = execute_wget(add_dict[code], temp_dir)
        dom_filepath = execute_wget(dom_dict[code], temp_dir)
        
        out_filepath = os.path.join(output_dir, f"{code}_gwas_merged.chisq.gz")
        
        print("Preprocessing sumstats...")
        preprocess_sumstats(add_filepath, dom_filepath, ref_file, out_filepath)

    except Exception as e:
        print(f"ERROR processing phenotype {code}: {e}")
        
    finally:
        # Delete the unique temp directory and everything inside it
        print("Cleaning up temporary sumstats...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        elapsed_time = time.time() - start_time
        print(f"Finished cycle for {code} in {elapsed_time:.2f} seconds\n")

# ==========================================
# ==========================================

if __name__ == "__main__":
    # Check if a task ID was passed from the terminal
    if len(sys.argv) < 2:
        print("Usage: python script.py <task_index>")
        sys.exit(1)
        
    # SLURM arrays usually start at 1, but Python lists start at 0. 
    # We subtract 1 to align them perfectly.
    task_index = int(sys.argv[1]) - 1 
    tmp_dir = sys.argv[2]  # Grab the scratch path from bash
    out_dir = sys.argv[3]  # Grab the final save path from bash
    

    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)

    additive_excel = os.path.join(base_dir, "UKB_sumstats_Neale", "a_sumStats.xlsx")
    dominance_excel = os.path.join(base_dir, "UKB_sumstats_Neale", "d_sumStats.xlsx")
    hapmap3_ref = os.path.join(base_dir, "ref_genome", "hm3_no_MHC_MAF_01_INFO_9.txt")
    
    run_single_trait(task_index, additive_excel, dominance_excel, hapmap3_ref, tmp_dir, out_dir)