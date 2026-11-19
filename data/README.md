# SMEDecode experimental results

[SMEDecode_results.xlsx](SMEDecode_results.xlsx) contains the experimental results reported in the SMEDecode manuscript.

## Worksheets

| Worksheet | Manuscript location | Data |
|---|---|---|
| `Baseline_Comparison` | Figure 6 and performance comparison | Five baseline groups with 18 configurations each: MeAtten, XNNPACK fused, XNNPACK nonfused, ACL with 256-key blocks, and SMEAtten. Each record includes its contemporaneous SMEDecode measurements. |
| `Cumulative_Ablation` | Figure 7, Table 4 and ablation text | Six configurations: L = 10240, N = 296 or 592, and R = 1, 16 or 256. Each configuration has four implementation states. |
| `Core_Scaling` | Figure 8 and core-scaling text | SMEDecode and SMEAtten at 37, 74, 148 and 296 workers; L = 2048 or 10240; R = 1 or 256; N = 296. |
| `Scaling_Controls` | Core-scaling text | Register computation, owner-local K/V reads, decoding with the reported NUMA placements, and dispatch with owner scanning. |
| `Instruction_Counts` | Table 3 | FP32 FMOPA and retired instruction counts for the seven reported implementation paths. |
| `Representative_Shapes` | Table 5 and representative-shape text | The 12 reported head-dimension and KV-group configurations, with paired SMEDecode and SMEAtten measurements. |
| `Key_Block_Sensitivity` | Experimental setup | The 18 configurations and the 16-, 32- and 256-key SMEAtten blocks. |
| `Precision_Validation` | Precision and shape validation | The 32 reported FP32 and BF16 correctness configurations and their measured errors. |
| `Exponent_Control` | Performance-comparison text | Original and common exponential functions at L = 2048 or 10240, N = 296 and R = 256. |

## Fields and units

`L` is the number of keys. `N` is the task count. `R` is the number of decoding calls after each preparation. `Hq` and `Hkv` are the query-head and KV-head counts. `d` is the head dimension. `workers` is the number of worker threads.

Times are in milliseconds. `C_ms` is data preparation, `D_ms` is accumulated complete decoding over the specified calls, and `T_ms` is continuous total execution time. The corresponding prefixed fields identify SMEDecode and its paired baseline. The total is measured in a continuous window, and each stage retains its own statistic.

Throughput is in GFLOP/s. It is calculated as:

```text
GFLOP/s = 4 * N * R * Hq * L * d / (T_ms * 1,000,000)
```

`T_speedup` is paired baseline total time divided by SMEDecode total time. `T_speedup_vs_37` is total time at 37 workers divided by total time at the row's worker count, for the same method and configuration.

Reduction, change and relative-time columns store numeric ratios and use percentage display formatting:

```text
time reduction = 1 - new time / reference time
throughput increase = new throughput / reference throughput - 1
relative key-block time = block total time / 16-key total time
key-block time change = relative key-block time - 1
```

Blank cells denote fields that do not apply to that record. Numeric precision is retained in the cells; the manuscript displays rounded values.

## Calculation methods

For the MeAtten, SMEAtten, XNNPACK and representative-shape comparisons, process-level timing samples use the median. Statistics across execution orders and independent measurements use the original geometric means. XNNPACK's fused and nonfused paths each have their own paired SMEDecode measurements.

ACL absolute times use paired arithmetic means. Its reduction columns retain the paired log-ratio statistic. `T_speedup` is the ratio of the displayed absolute-time statistics. The reduction columns and absolute-time columns retain their respective calculation methods.

Cumulative ablation uses the arithmetic mean of process medians with equal weighting of independent measurements. Throughput and step changes are calculated from those times. The states are `Base`, `K_layout`, `K_V_layout` and `Full`. They represent the base implementation, the key-segment layout, the additional V grouping, and the complete implementation with domain-based preparation and per-worker notification.

Core scaling uses the geometric mean of the ordinary timing statistics. Scaling-control times and register-compute throughput use the reported geometric means. `NUMA_domains` lists the domains used by that record. `reference_D_ms` and `time_over_reference` identify the matching standard-placement or ordinary-decoding reference.

Key-block sensitivity retains the original geometric means of timing statistics and ratios. Instruction counts report one complete prepared decoding call. Retired instructions use the median of three batches, after empty-window correction, with the manuscript's integer rounding also provided. FP32 FMOPA counts are from the executed instruction trace.

Precision errors are the per-configuration maxima from the measured outputs. `semantic_scaled_RMS` uses the precision-specific semantic reference. `ideal_FP64_scaled_RMS` uses the ideal FP64 reference. `absolute_RMS` and `near_zero_absolute_RMS` retain the original absolute-error definitions. The normalization denominator is `max(RMS(reference), 0.01)`. The recorded semantic, ideal BF16 and near-zero thresholds are 1e-4, 0.02 and 1e-6. The validation also contains 22 negative controls, all 22 rejected.

The exponential-function sheet retains the paired original and common-function measurements. The function-change columns compare common-function decoding time with the matching original-function time.
