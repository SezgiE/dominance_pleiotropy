#!/usr/bin/env python3
# d-LD Score Calculation - Sezgi Ercan - 09/02/2026

# For "variants.tsv.gz" file: https://nealelab.github.io/UKBB_ldsc/downloads.html#full_gwas_results
""" This file contains annotations on each variant in the 
    additive and dominance UKBB GWAS, calculated across the 
    analysis subset of 361,194 samples. """
# HapMap3 SNP list used: https://doi.org/10.5281/zenodo.10515792

import os
import pandas as pd


def filter_variants(ref_1K_EUR_file, hapmap3_file, variant_file, output_file):
    """Filtering UKBB GWAS variants to HapMap3 SNPs (NO MHC REGION), 
        with MAF > 0.01 and INFO > 0.9, and keeping only diallelic variants.
    
    Args:
        ref_1K_EUR_file: Path to 1K EUR SNP list file
        hapmap3_file: Path to HapMap3 SNP list file
        gwas_file: Path to GWAS variants file (variants.tsv.gz)
        output_file: Path to save filtered output
    """
    
    print("1. Loading HapMap3 SNP list...")
    hapmap3 = pd.read_csv(hapmap3_file, names=["rsid"], header=None)

    print("2. Loading Additive GWAS SumStats...")
    data_var = pd.read_csv(
        variant_file,
        sep="\t",
        compression="gzip",
        usecols=["variant", "chr", "rsid", "ref", "alt", "info", "minor_AF"],
    )

    print("3. Merging datasets...")
    data_merged = pd.merge(hapmap3, data_var, on="rsid", how="inner")

    data_merged = data_merged[
        (data_merged["minor_AF"] > 0.01) & (data_merged["info"] > 0.9)
    ]

    data_merged = data_merged[
        (data_merged["ref"].str.len() == 1) & (data_merged["alt"].str.len() == 1)
    ]

    print("4. Loading 1K_EUR SNP list...")
    ref_1K_EUR = pd.read_csv(ref_1K_EUR_file, sep="\t", usecols=["rsid"])
    data_merged = pd.merge(data_merged, ref_1K_EUR, on="rsid", how="inner")

    # Rename columns to match the format required for d-LDSC
    data_merged = data_merged.rename(
        columns={
            "variant": "variant",
            "rsid": "SNP",
            "ref": "A2",
            "alt": "A1",
            "minor_AF": "maf",
            "info": "info",
        }
    )

    # Keep only rsID column for the second output file for d-LDSC --extract-variants option
    data_merged_rsID = data_merged[["SNP"]]

    print("5. Saving filtered data...")
    data_merged.to_csv(os.path.join(output_file, "hm3_no_MHC_MAF_01_INFO_9.txt"), 
                       sep="\t", index=False)
    data_merged_rsID.to_csv(os.path.join(output_file, "hm3_no_MHC_MAF_01_INFO_9_rsID.txt"), 
                            sep="\t", index=False, header=False)
    
    print(f"Successfully saved variants to {output_file}")


if __name__ == "__main__":

     # 1. Set working directory where this script is located
    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)
    
    # 2. Define relative paths
    # Note: Ensure that "1000G_merged_all.txt" is created by merging the .bim files from 1000G_EUR_Phase3.
    ref_1K_EUR_dir = os.path.join(base_dir, "ref_genome/1000G_merged_all.txt")
    hapmap3_path = os.path.join(base_dir, "ref_genome/hm3_no_MHC.list.txt")
    variants_path = os.path.join(base_dir, "ref_genome/variants.tsv.gz")
    output_path = os.path.join(base_dir, "ref_genome")
    
    filter_variants(ref_1K_EUR_dir,hapmap3_path, variants_path, output_path)

