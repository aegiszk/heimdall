import json
import numpy as np

with open('workspace/sierra_atlas_2026-09-23/master_atlas_audit_results.json') as f:
    master_data = json.load(f)

with open('workspace/sierra_atlas_2026-09-23/cl_rty_ym_trials.json') as f:
    cl_rty_ym = json.load(f)

# Combine trials
all_trials = master_data['all_trials'] + cl_rty_ym
print(f'Total trials across all 12 instruments: {len(all_trials)}')

pvals = [t['pval_hac'] for t in all_trials]
m_tests = len(pvals)
sorted_indices = np.argsort(pvals)

# Benjamini-Hochberg FDR (q=0.10)
q_fdr = 0.10
fdr_threshold = 0.0
fdr_sig = [False] * m_tests
for rank, idx in enumerate(sorted_indices, 1):
    crit = (rank / m_tests) * q_fdr
    if pvals[idx] <= crit:
        fdr_sig[idx] = True
        fdr_threshold = max(fdr_threshold, pvals[idx])

# Bonferroni (alpha = 0.05)
bonf_sig = [p <= (0.05 / m_tests) for p in pvals]

for i, t in enumerate(all_trials):
    t['fdr_sig_q010'] = bool(fdr_sig[i])
    t['bonf_sig_a005'] = bool(bonf_sig[i])

uncorr_sig = sum(p < 0.05 for p in pvals)
fdr_count = sum(fdr_sig)
bonf_count = sum(bonf_sig)
pot_econ = sum(t['economic_class'] == 'POTENTIALLY_ECONOMIC' for t in all_trials)
pot_econ_fdr = sum(t['economic_class'] == 'POTENTIALLY_ECONOMIC' and t['fdr_sig_q010'] for t in all_trials)
pot_econ_bonf = sum(t['economic_class'] == 'POTENTIALLY_ECONOMIC' and t['bonf_sig_a005'] for t in all_trials)

print(f'Uncorrected HAC p < 0.05: {uncorr_sig}')
print(f'Benjamini-Hochberg FDR (q=0.10): {fdr_count}')
print(f'Holm-Bonferroni (alpha=0.05): {bonf_count}')
print(f'Potentially Economic (spread > friction): {pot_econ}')
print(f'Potentially Economic AND FDR sig: {pot_econ_fdr}')
print(f'Potentially Economic AND Bonferroni sig: {pot_econ_bonf}')

print('\nAll Bonferroni Surviving Trials:')
for t in all_trials:
    if t['bonf_sig_a005']:
        tid = t['trial_id']
        spr = t['q_spread_bps']
        frc = t['friction_bps']
        thac = t['t_stat_hac']
        p = t['pval_hac']
        ecl = t['economic_class']
        print(f'{tid:50s} | Spread: {spr:+6.2f} bps | Fric: {frc:4.2f} | HAC t: {thac:+5.2f} | p: {p:.2e} | Class: {ecl}')

master_data['all_trials'] = all_trials
master_data['trials_evaluated'] = len(all_trials)
master_data['multiple_testing_summary'] = {
    'total_trials': len(all_trials),
    'uncorrected_p005_count': uncorr_sig,
    'fdr_q010_count': fdr_count,
    'bonferroni_a005_count': bonf_count,
    'potentially_economic_count': pot_econ,
    'potentially_economic_fdr_count': pot_econ_fdr,
    'potentially_economic_bonf_count': pot_econ_bonf,
}

with open('workspace/sierra_atlas_2026-09-23/master_atlas_audit_results.json', 'w') as f:
    json.dump(master_data, f, indent=2)
print('Saved updated master_atlas_audit_results.json')
