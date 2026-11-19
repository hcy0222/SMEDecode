# SMEDecode

SMEDecode performs attention decoding on Arm SME. `bench_aarch64` is the statically linked AArch64 Linux executable for the SMEDecode versus independently reproduced SMEAtten comparison used in the manuscript. The executable is copied from the archived comparison build. See [the manuscript on Overleaf](https://www.overleaf.com/project/6abc585ad54da187b60b59df) (project access required).

## Run a functional check

From the repository root on Linux, run:

```sh
python3 smoke_test.py
```

The script requires four available CPU IDs. On Arm64 it runs the executable directly and needs SME/SVE2 with a 512-bit streaming vector length. On other architectures it uses `qemu-aarch64` with SME emulation. The executable generates its inputs and checks both methods against an FP64 reference for four reduced cases. The script uses temporary files for the run. It checks execution and numerical results in a reduced workload. The full performance run requires the original server and its allocation and NUMA binding inputs.

## Experiment data

The [experiment data](data/README.md) include aggregate results for the configurations reported in the manuscript. The [data workbook](data/SMEDecode_results.xlsx) contains the performance comparisons, six-configuration ablation, core scaling, instruction counts, representative shapes, key-block sensitivity, precision validation and exponential-function control.

[Third-party notices](THIRD_PARTY_NOTICES.txt)
