import os
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
    
    # Since they are identical, we only need one list. 
    # Sorting it ensures reproducible and consistent ordering for downstream steps.
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
    # usecols ensures we only load exactly what we need, saving massive amounts of RAM
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


def run_pipeline(add_excel, dom_excel, ref_file, temp_dir="./temp_sumstats", output_dir="./sumstats_merged"):
    
    """Main execution loop for the cluster."""
    # Ensure directories exist
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print("Initializing pipeline and validating input files...")
    add_dict, dom_dict, phenotype_codes = load_wget_commands(add_excel, dom_excel)
    print(f"Validation successful. Found {len(phenotype_codes)} matching phenotypes.\n")
    
    for code in phenotype_codes:
        start_time = time.time()
        print(f"--- Starting workflow for phenotype: {code} ---")

        # Initialize to None to safely handle cleanup if downloads fail immediately
        add_filepath = None
        dom_filepath = None
        
        try:
            print("Downloading summary statistics...")
            add_filepath = execute_wget(add_dict[code], temp_dir)
            dom_filepath = execute_wget(dom_dict[code], temp_dir)
            
            # Define output destination
            out_filename = f"{code}_gwas_merged.chisq.gz"
            out_filepath = os.path.join(output_dir, out_filename)
            
            print("Preprocessing sumstats...")
            preprocess_sumstats(add_filepath, dom_filepath, ref_file, out_filepath)

        except Exception as e:
            # If anything fails (network error, corrupted bgz, missing columns), 
            # Log it and move to the next trait.
            print(f"ERROR processing phenotype {code}: {e}")
            
        finally:
            # 5. Delete sumstat files completely
            print("Cleaning up temporary sumstats...")
            if add_filepath and os.path.exists(add_filepath):
                os.remove(add_filepath)
            if dom_filepath and os.path.exists(dom_filepath):
                os.remove(dom_filepath)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Finished cycle for {code} in {elapsed_time:.2f} seconds\n")

    # After the loop finishes entirely, delete the temp directory
    print("All phenotypes processed. Removing the temporary directory...")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Successfully deleted {temp_dir}\n")


# ==========================================
# ==========================================

if __name__ == "__main__":
    import os
    
    # 1. Set working directory where this script is located
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)

    # 2. Define relative paths to input files
    additive_excel_path = os.path.join(base_dir, "UKB_sumstats_Neale", "a_sumStats.xlsx")
    dominance_excel_path = os.path.join(base_dir, "UKB_sumstats_Neale", "d_sumStats.xlsx")
    hapmap3_reference_path = os.path.join(base_dir, "ref_genome", "snp_hm3_adj.txt")
    
    run_pipeline(
        add_excel=additive_excel_path, 
        dom_excel=dominance_excel_path, 
        ref_file=hapmap3_reference_path
    )

