# Native acceptance

These records cover the main comparison between SMEDecode and independently reproduced SMEAtten on Arm SME Linux. The comparison used the archived build distributed as [bench_aarch64](../bench_aarch64).

| Independent run | Native job | Configurations | Program exit code | Audit exit code | FP64 reference checks |
| --- | --- | --- | --- | --- | --- |
| 1 | 2043598 | 18 | 0 | 0 | Passed |
| 2 | 2043742 | 18 | 0 | 0 | Passed |

Both execution orders within each run passed the output checks against FP64 reference values and the audit of configuration coverage. This summary records acceptance for the two independent runs.
