# SMEDecode

SMEDecode performs attention decoding on Arm SME.

## Executable

`bench_aarch64` is a statically linked AArch64 Linux benchmark executable. It contains two FP32 attention implementations: SMEDecode and an independently reproduced SMEAtten. The comparison uses 32 query heads sharing one KV head, with a head dimension of 128.

The file is the executable from the archived main comparison. It supports that comparison and the four reduced configurations invoked by `smoke_test.py`.

MeAtten, XNNPACK and ACL comparison programs, and the dedicated programs for the other experiments, are not included in this executable. Their reported experimental results are provided in the [results workbook](data/SMEDecode_results.xlsx).

## Run a functional check

From the repository root on Linux, run:

```sh
python3 smoke_test.py
```

The script requires four available CPU IDs. On Arm64 it runs the executable directly and needs SME/SVE2 with a 512-bit streaming vector length. On other architectures it uses `qemu-aarch64` with SME emulation. The executable generates its inputs and checks both methods against an FP64 reference for four reduced cases. The script uses temporary files for the run. It checks execution and numerical results in a reduced workload. The full performance run requires the original server and its allocation and NUMA binding inputs.

## Test records

- `logs/smoke_test.log` records the four reduced functional checks executed with QEMU in WSL using the published executable and test script.
- `logs/native_acceptance.md` records execution and numerical acceptance from the original Arm SME comparison experiments.

## Experimental results

The [experimental results](data/README.md) cover the configurations reported in the manuscript. The [results workbook](data/SMEDecode_results.xlsx) contains the performance comparisons, six-configuration ablation, core scaling, instruction counts, representative shapes, key-block sensitivity, precision validation and exponential-function control.

[Third-party notices](THIRD_PARTY_NOTICES.txt)
