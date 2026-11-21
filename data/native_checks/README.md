# Native experimental results

These files contain the November 19, 2026 measurements on the Arm SME compute nodes.
Each method and selected configuration has one timing sample. The ablation uses the six manuscript configurations and all four implementation states.

| File | Contents |
|---|---|
| `results.csv` | Preparation, decoding and continuous total time for all 89 method/configuration records |
| `time_reductions.csv` | Recorded time-reduction percentages |
| `precision_results.csv` | Numerical errors for the three selected FP32/BF16 cases |
| `instruction_results.csv` | Instruction counts, FMOPA counts and numerical checks for seven computation paths |
| `core_controls.csv` | Register computation, owner-local K/V reads and dispatch controls |

Times use milliseconds in `results.csv` and nanoseconds in the original control fields. `L` is the key count, `N` the task count, `R` the decoding calls per task, `d` the head dimension and `Hkv` the KV-head count. `job` and `host` identify the actual measurement source.

Time reduction in percent is `(reference_time - method_time) / reference_time * 100`. Positive values indicate less time; negative values indicate more time. Key-block reductions use 16 keys, and exponential replacements use the matching original exponential.

The [six-configuration ablation results](../six_configuration_ablation.csv) provide the aggregate from two independent measurements.

The fused XNNPACK baseline was recorded in job 2180267 on cn19457. Its SMEDecode companion was recorded after the benchmark-header correction in job 2180412 on cn12136. Their measurement sources remain separate in the tables.

The [runtime logs](../../logs/native_suite/) accompany the non-ablation experiments. The [manuscript workbook](../SMEDecode_results.xlsx) retains the results reported in the paper.
