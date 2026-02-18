import pandas as pd

# Load your Excel file
df_dom = pd.read_excel("/Users/sezgi/Downloads/Neale Lab - UKB Dominance TSVs - in AWS-2.xlsx")
df_add = pd.read_excel('/Users/sezgi/Downloads/neale_clean_A.xlsx')


# Filter to ONLY keep rows where the 'file' column contains 'both_sexes'
dom_filtered = df_dom[df_dom['file'].str.contains('both_sexes', na=False)]
dom_filtered['sex'] = 'both_sexes'

dom_filtered = dom_filtered.rename(
    columns={
        "phenotype": "phenotype_code",
        "description": "description",
        "sex": "sex",
        "file": "file",
        "wget": "wget",
    }
)

add_filtered = df_add[df_add['Sex'] == 'both_sexes']
add_filtered = add_filtered[~add_filtered['File'].str.contains('.v2.tsv.bgz', na=False, regex=False)]

add_filtered = add_filtered.rename(columns={
    'Phenotype Code': 'phenotype_code',
    'Phenotype Description': 'description',
    "Sex":"sex",
    "File":"file",
    'wget command': 'wget'
})


# 1. Find the exact matching phenotype codes in BOTH dataframes
common_codes = set(dom_filtered['phenotype_code']).intersection(set(add_filtered['phenotype_code']))

# 2. Filter both dataframes to ONLY keep rows that exist in the common_codes set
dom_final = dom_filtered[dom_filtered['phenotype_code'].isin(common_codes)].copy()
add_final = add_filtered[add_filtered['phenotype_code'].isin(common_codes)].copy()

# 3. Sort them alphabetically by phenotype_code so they match perfectly row-for-row
dom_final = dom_final.sort_values('phenotype_code').reset_index(drop=True)
add_final = add_final.sort_values('phenotype_code').reset_index(drop=True)

final_cols = ['phenotype_code', 'description', 'sex', 'file', 'wget']

dom_final = dom_final[final_cols]
add_final = add_final[final_cols]


# Print a quick summary to make sure the math checks out!
print(f"Total matching phenotypes found: {len(common_codes)}")
print(f"Final Additive rows: {len(add_final)}")
print(f"Final Dominance rows: {len(dom_final)}")

# 4. Save the perfectly clean, matching files to your computer!
dom_final.to_excel("/Users/sezgi/Downloads/d_sumStats.xlsx", index=False)
add_final.to_excel("/Users/sezgi/Downloads/a_sumStats.xlsx", index=False)

print("Here are the duplicate additive traits:")
print(add_final[add_final.duplicated(subset=['phenotype_code'], keep=False)][['phenotype_code', 'description']])

#