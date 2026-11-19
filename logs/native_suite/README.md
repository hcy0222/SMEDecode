# Native runtime logs

These archives contain the November 19, 2026 runtime logs for the non-ablation experiments. Original program output, timing records, numerical checks, page-placement records and worker diagnostics retain their recorded contents.

| Archive | Log files | Configurations or paths |
|---|---:|---|
| [smeatten.zip](smeatten.zip) | 904 | 3 inputs, SMEDecode and SMEAtten |
| [meatten.zip](meatten.zip) | 907 | 3 inputs, MeAtten and SMEDecode |
| [acl.zip](acl.zip) | 6 | 3 inputs, SMEDecode and both ACL paths |
| [core_scaling.zip](core_scaling.zip) | 1488 | 37, 148 and 296 workers |
| [key_block.zip](key_block.zip) | 2704 | 3 inputs, 16/32/256-key blocks |
| [exponential.zip](exponential.zip) | 1804 | 2 inputs, original and common exponentials |
| [xnnpack_fused.zip](xnnpack_fused.zip) | 911 | 3 inputs, baseline and corrected companion |
| [xnnpack_nonfused.zip](xnnpack_nonfused.zip) | 908 | 3 inputs, baseline and companion |
| [shapes.zip](shapes.zip) | 37 | 3 head-dimension/KV-group configurations |
| [precision.zip](precision.zip) | 6 | 3 FP32/BF16 configurations |
| [instructions.zip](instructions.zip) | 17 | 1 input, 7 paths in counter and trace modes |

Shared `environment_JOB.json` and `scheduler_JOB.json` files record the actual allocation, platform checks and job terminal state once for each job.

Job 2180267 completed the fused baseline, then its companion exited before attention computation because a 343-CPU benchmark header was selected instead of the fused program's 379-CPU header. The corrected companion and the remaining paths completed in subsequent jobs; the initial output is retained in `xnnpack_fused.zip`.

The [experimental result tables](../../data/native_checks/) retain configuration identifiers, times and their actual job/node sources.
