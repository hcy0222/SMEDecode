"""Run the AArch64 comparison on generated inputs in reduced smoke mode."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


def main():
    cpus = sorted(os.sched_getaffinity(0))[:4]
    if len(cpus) != 4:
        raise SystemExit("Four available Linux CPU IDs are required.")
    prefix = []
    if platform.machine() not in {"aarch64", "arm64"}:
        prefix = ["qemu-aarch64", "-cpu",
                  "max,sme=on,sme-default-vector-length=64,sve-default-vector-length=64"]

    profile_id = "1" * 64
    binding = [
        "FC_PROFILE_V1", "mode emulated", f"profile_sha256 {profile_id}", "job_id 0",
        f"node {platform.node()}", "allocation 4", *(f"cpu {cpu}" for cpu in cpus),
        f"coordinator_cpu {cpus[0]}", "hardware 32768 786432 67108864", "workers 3",
        *(f"worker {cpu} -1 1.0 1.0" for cpu in cpus[1:]), "end",
    ]
    with tempfile.TemporaryDirectory(prefix="smedecode-smoke-") as directory:
        path = Path(directory)
        executable = path / "bench_aarch64"
        shutil.copyfile(Path(__file__).with_name(executable.name), executable)
        executable.chmod(0o700)
        binding_path = path / "binding.txt"
        binding_path.write_text("\n".join(binding) + "\n", encoding="ascii")
        output = path / "output"
        subprocess.run(
            [*prefix, str(executable), "emulated", str(binding_path), profile_id,
             str(output), "0", "smoke"],
            check=True,
        )
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if (
            summary["status"] != "FORMAL_COMPARE_PROCESS_ACCEPTED"
            or summary["configurations"] != 4
            or summary["integrity_gates"] != 8
            or summary["workers_joined"] != 3
            or summary["mode"] != "emulated"
        ):
            raise SystemExit("The benchmark did not complete all smoke checks.")

    print("SMEDecode and SMEAtten passed the four reduced cases and FP64 reference checks.")


if __name__ == "__main__":
    main()
