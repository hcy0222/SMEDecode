# Runtime-check results

These CSV files contain execution-time, numerical-accuracy and instruction-count results for the released programs.

| File | Contents |
|---|---|
| [results.csv](results.csv) | Preparation, decoding and continuous total execution time, with correctness results. |
| [time_reductions.csv](time_reductions.csv) | Time-reduction percentages. |
| [precision_results.csv](precision_results.csv) | FP32 and BF16 numerical errors. |
| [instruction_results.csv](instruction_results.csv) | Retired instruction counts, FP32 FMOPA counts and numerical errors. |
| [core_controls.csv](core_controls.csv) | Register computation, local K/V reads and dispatch controls. |

`results.csv` uses milliseconds. The timing fields in `core_controls.csv` use nanoseconds. Percentage columns in `time_reductions.csv` store percent values.

`L` is the key count, `N` the task count and `R` the decoding calls per task. `d` is the head dimension, `Hkv` the KV-head count and `workers` the worker count.

The [ablation results](../six_configuration_ablation.csv) and [manuscript workbook](../SMEDecode_results.xlsx) provide the corresponding experimental results.
