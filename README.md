# SMEDecode

SMEDecode performs attention decoding on Arm SME.

## Experiment executables

`bench_aarch64` is a statically linked AArch64 Linux benchmark executable. It contains two FP32 attention implementations: SMEDecode and an independently reproduced SMEAtten. The comparison uses 32 query heads sharing one KV head, with a head dimension of 128.

The executable retains the main-comparison implementations and provides a native check mode. It also supports the four small configurations invoked by `smoke_test.py`. Dedicated programs for the other manuscript experiments are provided in `bin/`.

| Files | Experiment |
|---|---|
| `bench_aarch64` | SMEDecode and independently reproduced SMEAtten |
| `bin/meatten`, `bin/smedecode_meatten` | MeAtten comparison |
| `bin/xnnpack_fused`, `bin/smedecode_xnnpack_fused` | Fused XNNPACK comparison |
| `bin/xnnpack_nonfused`, `bin/smedecode_xnnpack_nonfused` | Non-fused XNNPACK comparison |
| `bin/acl` | SMEDecode and the blocked/full-matrix ACL paths |
| `bin/ablation_base`, `bin/ablation_k`, `bin/ablation_kv`, `bin/ablation_full` | Four cumulative ablation states; six configurations: L=10240, N=296/592, R=1/16/256 |
| `bin/core_scaling` | Core scaling and the compute, read, dispatch and NUMA-placement controls |
| `bin/scaling_reference` | Scalar FP64 reference generation for core scaling |
| `bin/shapes_d64`, `bin/shapes_d128` | The 12 representative shapes |
| `bin/key_block_16`, `bin/key_block_32`, `bin/key_block_256` | SMEAtten key-block sensitivity |
| `bin/original_exp`, `bin/common_exp` | The two exponential-function controls |
| `bin/instructions_sme`, `bin/instructions_me`, `bin/instructions_xnn_f`, `bin/instructions_xnn_nf`, `bin/instructions_acl`, `bin/instructions_trace` | Instruction and FMOPA measurements for the seven manuscript paths |
| `lib/precision_pool.so`, `lib/precision_d*_target.so`, `lib/precision_math_d*_target.so` | Runtime binaries for the 32 FP32/BF16 configurations |
| `lib/libacl_t11.so` | The ACL `arm_gemm` runtime used by the ACL programs |

The ablation release entry points run the six configurations above. Their measurement front ends were restricted to these configurations while retaining the adopted math and adapter objects. The precision entry libraries load their math libraries from the package's `lib/` directory.

Worker placement uses the machine's observed CPU-to-NUMA mapping. The MeAtten, XNNPACK and ACL benchmark drivers were rebuilt to read that mapping; their adopted math and adapter objects were retained.

Implementation source files and build intermediates are not included.

## Run a functional check

From the repository root on Linux, run:

```sh
python3 smoke_test.py
```

The script requires four available CPU IDs. On Arm64 it runs the executable directly and needs SME/SVE2 with a 512-bit streaming vector length. On other architectures it uses `qemu-aarch64` with SME emulation. The executable generates its inputs and checks both methods against an FP64 reference for four reduced cases. The script uses temporary files for the run. It checks execution and numerical results in a reduced workload. The full performance run requires the original server and its allocation and NUMA binding inputs.

## Run manuscript experiments

`run_experiments.py` prepares the binding inputs and invokes the selected experiment binaries. By default it runs a reduced native check with one timing sample per method and configuration. `test_precision.py` checks three selected FP32/BF16 configurations against FP64 references, also with one timing sample. Both scripts use the Python standard library and retain outputs in the specified directory.

| Default native check | Configurations |
|---|---|
| Performance comparisons and key-block sensitivity | (L,N,R) = (2048,296,1), (6144,296,16), (10240,592,256) |
| Cumulative ablation | L=10240, N=296/592, R=1/16/256; all six configurations, four states |
| Representative shapes | (d,Hkv,L,R) = (64,1,2048,1), (128,1,10240,16), (128,8,10240,1); N=296 |
| Core scaling | L=2048, N=296, R=1 at the selected worker count |
| Exponential-function control | L=2048/10240, N=296, R=256 |
| Precision | (precision,d,Hkv,L,R) = (FP32,128,1,2048,1), (BF16,64,1,10240,16), (BF16,128,8,10240,1); 16 requests |
| Instruction measurements | One L=2048 input, seven paths; one counter batch and one trace per path |

Add `--formal` to either script to run its full manuscript workload and retained sample counts. A reduced check completes one execution order; numerical checks and warm-up calls remain outside the timing sample.

Run native experiments from the repository root inside a compute-node allocation on the paper's Arm SME server. The programs require SVE/SVE2 and SME with 512-bit vector lengths, 4096-byte base pages, eight allocated NUMA domains with 37 worker CPUs each for the 296-worker experiments, and sufficient memory for the selected workload. BF16 precision tests additionally require the corresponding BF16 instructions. The scheduler provides `CCS_JOB_ID`.

| Selection | Allocated CPUs | Workers |
|---|---:|---:|
| `smeatten`, `meatten`, `acl`, `ablation`, `shapes`, `key-block`, `common-exp` | 343 | 296 |
| `xnnpack-fused`, `xnnpack-nonfused` | 379 | 296 |
| `scaling` | 343 | 37, 74, 148 or 296 |
| `instructions` | At least one CPU | One |
| `test_precision.py` | Nine CPUs in one NUMA domain | Eight |

Dynamic executables and libraries require the AArch64 system loader, glibc and libm. MeAtten uses the server's KML `libkblas.so.1`; its installed directory can be supplied with `--kml-lib`. ACL loads the included `lib/libacl_t11.so`. Instruction measurements also require `numactl`, access to hardware instruction counters and permission to trace the child process. Third-party license notices are included below.

For example, run the six-configuration ablation in a 343-CPU allocation:

```sh
python3 run_experiments.py ablation --output /path/to/new-ablation-results
```

Choose another experiment using the names listed by `python3 run_experiments.py --help`. Each invocation uses a new output directory outside this repository and stops if a program fails. The default is one execution order. `--round` and `--process` select an order in the corresponding retained drivers when an explicit order is needed.

Before core scaling, generate its scalar references on the AArch64 login host:

```sh
python3 run_experiments.py scaling-reference --output /path/to/new-scaling-references
```

Then run core scaling in a 343-CPU compute-node allocation:

```sh
python3 run_experiments.py scaling --workers 37 --reference-dir /path/to/new-scaling-references --output /path/to/new-scaling-results
```

Select 37, 74, 148 or 296 workers with `--workers`. Add `--spread` to run the L=10240 NUMA-distribution control across eight domains.

Run precision checks in a nine-CPU allocation:

```sh
python3 test_precision.py --samples 1 --output /path/to/new-precision-checks
```

The default checks the three precision configurations in the table with one sample each. `--formal --samples 8` runs eight measurements for each of the 32 manuscript configurations. Numerical checks use the manuscript's semantic error criterion, including its near-zero rule, and the BF16 comparison with the ideal FP32 reference.

## Test records

- `logs/smoke_test.log` records the four reduced functional checks executed with QEMU in WSL using the published executable and test script.
- `logs/native_acceptance.md` records execution and numerical acceptance from the original Arm SME comparison experiments.
- `logs/release_checks.log` records packaging, script-entry and runtime-loading checks for this binary suite.
- `logs/native_test.log` records the November 19, 2026 compute-node test of the published release: four reduced main-comparison configurations, seven computation paths in both counter and trace modes, and 32 precision configurations with one sample each. All numerical checks passed.

## Experimental results

The [experimental results](data/README.md) cover the configurations reported in the manuscript. The [results workbook](data/SMEDecode_results.xlsx) contains the performance comparisons, six-configuration ablation, core scaling, instruction counts, representative shapes, key-block sensitivity, precision validation and exponential-function control.

[Third-party notices](THIRD_PARTY_NOTICES.txt)
