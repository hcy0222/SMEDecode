#!/usr/bin/env python3
"""Check three FP32/BF16 cases; use --formal for all manuscript configurations."""
import argparse
from array import array
import ctypes as C
import datetime as dt
import json
import math
import os
from pathlib import Path
from run_experiments import ROOT, native_environment, cpu_node


def check(rc, operation):
    if rc:
        raise RuntimeError('%s failed: %d' % (operation, rc))


class Team:
    def __init__(self, dim, cpus, node):
        self.lib = C.CDLL(str(ROOT/'lib/precision_pool.so'), use_errno=True)
        signatures = {
            'group_open': (C.c_void_p, [C.c_char_p, C.POINTER(C.c_int), C.c_int, C.c_int]),
            'group_init': (C.c_int, [C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_int, C.c_uint32, C.c_int]),
            'group_implementation': (C.c_int, [C.c_void_p, C.c_int]),
            'group_dispatch': (C.c_int, [C.c_void_p, C.c_int, C.c_int]),
            'group_sample': (C.c_int, [C.c_void_p, C.c_int, C.POINTER(C.c_uint64), C.POINTER(C.c_uint64)]),
            'group_dump': (C.c_int, [C.c_void_p, C.c_char_p, C.c_int]),
            'group_snapshot': (C.c_int, [C.c_void_p, C.c_char_p]),
            'group_close': (C.c_int, [C.c_void_p])}
        for name, (result, arguments) in signatures.items():
            fn = getattr(self.lib, name)
            fn.restype, fn.argtypes = result, arguments
        library = str(ROOT/('lib/precision_d%d_target.so' % dim)).encode()
        self.handle = self.lib.group_open(library, (C.c_int*8)(*cpus), node, 1)
        if not self.handle:
            raise RuntimeError('Cannot initialize precision worker team')

    def dispatch(self, operation):
        check(self.lib.group_dispatch(self.handle, operation, 1), 'worker operation %d' % operation)

    def dump(self, path, mode):
        path.mkdir()
        check(self.lib.group_dump(self.handle, os.fsencode(path), mode), 'save numerical values')

    def sample(self, repeats):
        clocks = (C.c_uint64*3)()
        calls = C.c_uint64()
        check(self.lib.group_sample(self.handle, repeats, clocks, C.byref(calls)), 'prepare and decode')
        if not clocks[0] < clocks[1] < clocks[2] or calls.value != 16*repeats:
            raise RuntimeError('Incorrect complete-call count or clock ordering')
        return dict(C_ns=clocks[1]-clocks[0], D_ns=clocks[2]-clocks[1],
                    T_ns=clocks[2]-clocks[0], calls=calls.value)


def values(path, code, count):
    result = array(code)
    result.frombytes(path.read_bytes())
    if len(result) != count or not all(math.isfinite(x) for x in result):
        raise RuntimeError('Invalid numerical output: '+str(path))
    return result


def error(got, reference):
    rms = math.sqrt(math.fsum((a-b)**2 for a, b in zip(got, reference))/len(got))
    scale = math.sqrt(math.fsum(b*b for b in reference)/len(reference))
    return rms/max(scale, 0.01), rms, scale


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True, help='new directory outside the repository')
    ap.add_argument('--formal', action='store_true', help='run all 32 manuscript configurations')
    ap.add_argument('--samples', type=int, choices=(1, 8),
                    help='one sample for numerical acceptance, eight for the measurement workload')
    args = ap.parse_args()
    if args.samples is None:
        args.samples = 8 if args.formal else 1
    if not args.formal and args.samples != 1:
        ap.error('The reduced check uses one sample; --formal selects the full workload')
    selected = {(128, 1, 2048, 0, 1), (64, 1, 10240, 2, 16), (128, 8, 10240, 2, 1)}
    job, cpus = native_environment()
    if len(cpus) != 9 or len({cpu_node(c) for c in cpus}) != 1:
        ap.error('Allocate nine CPUs in one NUMA domain')
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        ap.error('Choose an output directory outside the repository')
    out.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {cpus[-1]})
    record = dict(job=job, cpus=cpus, samples=args.samples,
                  scope='formal' if args.formal else 'reduced_check',
                  started=dt.datetime.now(dt.timezone.utc).isoformat(), cases=[])
    for dim in (64, 128):
        for groups in (1, 8):
            for length in (2048, 10240):
                if not args.formal and not any(t[:3] == (dim, groups, length) for t in selected):
                    continue
                scenario = out/('d%d_g%d_L%d' % (dim, groups, length))
                scenario.mkdir()
                team = Team(dim, cpus[:8], cpu_node(cpus[0]))
                check(team.lib.group_init(team.handle, length, 256, groups, 0, 0x13579bdf, 0), 'input generation')
                team.dispatch(4)
                for impl in (0, 2):
                    if not args.formal and not any(t[:4] == (dim, groups, length, impl) for t in selected):
                        continue
                    check(team.lib.group_implementation(team.handle, impl), 'precision selection')
                    team.dispatch(5)
                    refs = scenario/('references_i%d' % impl)
                    team.dump(refs, 2)
                    references = [(values(refs/('r%02d_semantic.f64' % r), 'd', 32*dim),
                                   values(refs/('r%02d_ideal.f64' % r), 'd', 32*dim)) for r in range(16)]
                    for repeats in (1, 16):
                        if not args.formal and (dim, groups, length, impl, repeats) not in selected:
                            continue
                        row = dict(d=dim, Hkv=groups, L=length, R=repeats,
                                   precision='FP32' if impl == 0 else 'BF16',
                                   semantic_scaled_rms=0.0, ideal_scaled_rms=0.0, samples=[])
                        for sample in range(args.samples):
                            folder = scenario/('i%d_R%d_s%d' % (impl, repeats, sample))
                            timing = team.sample(repeats)
                            team.dispatch(6)
                            team.dispatch(4)
                            team.dump(folder, 0)
                            check(team.lib.group_snapshot(team.handle, os.fsencode(folder/'workers.json')), 'worker record')
                            for r, (semantic, ideal) in enumerate(references):
                                got = values(folder/('r%02d_out.f32' % r), 'f', 32*dim)
                                a, absolute, scale = error(got, semantic)
                                b, _, _ = error(got, ideal)
                                if a > 1e-4 or (scale < 0.01 and absolute > 1e-6) or (impl and b > 0.02):
                                    raise RuntimeError('Numerical comparison failed: '+str(folder))
                                row['semantic_scaled_rms'] = max(row['semantic_scaled_rms'], a)
                                row['ideal_scaled_rms'] = max(row['ideal_scaled_rms'], b)
                            row['samples'].append(timing)
                            team.dispatch(7)
                        record['cases'].append(row)
                        (out/'test_record.json').write_text(json.dumps(record, indent=2)+'\n')
                        print(json.dumps({k: v for k, v in row.items() if k != 'samples'}), flush=True)
                team.dispatch(8)
                check(team.lib.group_close(team.handle), 'worker join')
    if len(record['cases']) != (32 if args.formal else 3):
        raise RuntimeError('Incomplete precision configuration coverage')
    record.update(status='numerical_checks_passed', completed=dt.datetime.now(dt.timezone.utc).isoformat())
    (out/'test_record.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    main()
