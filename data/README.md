# Experimental results

This directory contains SMEDecode experimental results in CSV and Excel format.

## Result files

| File | Contents |
|---|---|
| [six_configuration_ablation.csv](six_configuration_ablation.csv) | Ablation results: total execution time for Base, K, KV and Full, together with percentage results. |
| [SMEDecode_results.xlsx](SMEDecode_results.xlsx) | Experimental results reported in the manuscript. |
| [native_checks/](native_checks/) | Runtime-check results for execution time, numerical accuracy, instruction counts and execution controls. |

## Workbook contents

| Worksheet | Results |
|---|---|
| `Baseline_Comparison` | SMEDecode comparisons with MeAtten, fused and non-fused XNNPACK, ACL and SMEAtten. |
| `Cumulative_Ablation` | Execution time and throughput for the ablation implementation states. |
| `Core_Scaling` | SMEDecode and SMEAtten results at different worker counts. |
| `Scaling_Controls` | Register computation, local K/V reads, NUMA placement and dispatch controls. |
| `Instruction_Counts` | FP32 FMOPA and retired instruction counts. |
| `Representative_Shapes` | SMEDecode and SMEAtten results for different head dimensions and KV groups. |
| `Key_Block_Sensitivity` | SMEAtten results for different key-block sizes. |
| `Precision_Validation` | FP32 and BF16 numerical errors and acceptance results. |
| `Exponent_Control` | Results for the original and common exponential functions. |

## Fields and units

`L` is the key count, `N` the task count and `R` the decoding calls after data preparation. `Hq` and `Hkv` are the query-head and KV-head counts. `d` is the head dimension, and `workers` is the worker count.

| Field | Meaning | Unit |
|---|---|---|
| `C_ms` | Data preparation time | ms |
| `D_ms` | Accumulated decoding time | ms |
| `T_ms` | Continuous total execution time | ms |
| `GFLOP_s` | Floating-point throughput | GFLOP/s |

Prefixes identify the implementation associated with a field. Total execution time is measured over a continuous interval.

Percentage fields in the ablation CSV store percent values: `4.61` means `4.61%`. Percentage-formatted cells in the workbook store ratios.

The precision fields contain semantic, ideal-reference, absolute and near-zero numerical errors. Blank cells denote fields that do not apply to the record.
