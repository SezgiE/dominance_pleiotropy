import os
import glob
import pandas as pd

def compile_heritability_results(results_dir, excel_path, output_csv):
    """
    Extracts heritability values and strictly validates phenotype codes.
    """
    print("1. Loading trait descriptions from Excel...")
    try:
        df_excel = pd.read_excel(excel_path)
        trait_map = dict(zip(df_excel['phenotype_code'], df_excel['description']))
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return

    print(f"2. Scanning for .h2 results in {results_dir}...")
    search_pattern = os.path.join(results_dir, "*_dom_h2.h2")
    h2_files = glob.glob(search_pattern)
    
    if not h2_files:
        print("No .h2 files found. Check your results directory path.")
        return
        
    print(f"Found {len(h2_files)} result files. Extracting and validating data...")
    
    compiled_data = []
    
    for file_path in h2_files:
        filename = os.path.basename(file_path)
        phenotype_code = filename.replace("_dom_h2.h2", "")
        trait_name = trait_map.get(phenotype_code, "Unknown")
        
        try:
            with open(file_path, 'r') as f:
                # Read the line, strip whitespace/newlines, and split by any whitespace
                row_data = f.readline().strip().split()
            
            # Ensure the row actually has enough columns
            if len(row_data) >= 25:
                internal_code = row_data[0]
                
                # --- THE DOUBLE CHECK ---
                if phenotype_code != internal_code:
                    print(f"Mismatch Error in {filename}: Filename says '{phenotype_code}', but internal data says '{internal_code}'. Skipping.")
                    continue 
                # ------------------------
                
                compiled_data.append({
                    'Trait_ID': phenotype_code,
                    'Trait_Name': trait_name,
                    'Additive_h2': row_data[9],
                    'Additive_SE': row_data[10],
                    'Dominance_h2': row_data[23],
                    'Dominance_SE': row_data[24]
                })
            else:
                print(f"Warning: {filename} has missing columns. Skipping.")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("3. Saving compiled dataset...")
    final_df = pd.DataFrame(compiled_data)
    
    if not final_df.empty:
        final_df = final_df.sort_values(by='Trait_ID')
        final_df.to_csv(output_csv, index=False)
        print(f"Done! Successfully saved {len(final_df)} validated traits to {output_csv}")
    else:
        print("Warning: No data was successfully extracted.")


# ==========================================
# ==========================================

if __name__ == "__main__":
   
    # 1. Set working directory where this script is located
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)
    
    results_dir = os.path.join(base_dir, "ldsc_results")
    excel_path = os.path.join(base_dir, "UKB_sumstats_Neale", "a_sumStats.xlsx") 
    output_csv = os.path.join(base_dir, "dominance_h2_results.csv")

    compile_heritability_results(
        results_dir=results_dir, 
        excel_path=excel_path, 
        output_csv=output_csv
    )