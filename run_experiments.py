#!/usr/bin/env python3
"""Run the published experiment binaries on the paper's Arm SME platform."""
import argparse
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent
EXPERIMENTS = ('smeatten', 'meatten', 'xnnpack-fused', 'xnnpack-nonfused',
               'acl', 'ablation', 'shapes', 'key-block', 'common-exp',
               'scaling', 'scaling-reference', 'instructions')


def cpu_node(cpu):
    nodes = list(Path('/sys/devices/system/cpu/cpu%d' % cpu).glob('node[0-9]*'))
    if len(nodes) != 1:
        raise RuntimeError('Cannot determine NUMA domain for CPU %d' % cpu)
    return int(nodes[0].name[4:])


def native_environment():
    if platform.system() != 'Linux' or platform.machine() != 'aarch64':
        raise RuntimeError('Native experiments require AArch64 Linux')
    job = os.environ.get('CCS_JOB_ID', '')
    if not job.isdecimal() or int(job) == 0 or not platform.node().startswith('cn'):
        raise RuntimeError('Run inside a compute-node allocation; CCS_JOB_ID is required')
    libc = ctypes.CDLL(None)
    vl, svl = libc.prctl(51, 0, 0, 0, 0), libc.prctl(64, 0, 0, 0, 0)
    if vl < 0 or svl < 0 or vl & 65535 != 64 or svl & 65535 != 64:
        raise RuntimeError('SVE and streaming vector lengths must both be 512 bits')
    if os.sysconf('SC_PAGE_SIZE') != 4096:
        raise RuntimeError('The binaries require 4096-byte base pages')
    return job, sorted(os.sched_getaffinity(0))


def worker_mapping(cpus):
    allowed = set(cpus)
    nodes = [n for n in range(16) if set(range(38*n, 38*n+37)) <= allowed][:8]
    if len(nodes) != 8:
        raise RuntimeError('Need eight NUMA domains with the original 37-worker CPU ranges')
    workers = [(c, n) for n in nodes for c in range(38*n, 38*n+37)]
    used = {c for c, _ in workers}
    controls = [c for c in cpus if c not in used and c % 38 != 37]
    if not controls:
        raise RuntimeError('No allocated coordinator CPU outside the worker ranges')
    return nodes, workers, controls[0]


def binding(path, job, cpus, workers, control, magic='FC_PROFILE_V1',
            field='profile_sha256', identity='1'*64):
    text = [magic, 'mode native', '%s %s' % (field, identity),
            'job_id '+job, 'node '+platform.node(), 'allocation %d' % len(cpus)]
    text += ['cpu %d' % c for c in cpus]
    text += ['coordinator_cpu %d' % control, 'hardware 32768 786432 67108864',
             'workers %d' % len(workers)]
    text += ['worker %d %d 1 1' % (c, n) for c, n in workers]
    path.write_text('\n'.join(text+['end'])+'\n')
    return identity


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('experiment', choices=EXPERIMENTS)
    ap.add_argument('--output', type=Path, required=True, help='new output directory outside the repository')
    ap.add_argument('--round', type=int, choices=(1, 2), default=1)
    ap.add_argument('--process', type=int, choices=(0, 1))
    ap.add_argument('--workers', type=int, choices=(37, 74, 148, 296), default=296,
                    help='worker count for core scaling')
    ap.add_argument('--spread', action='store_true', help='spread scaling workers across eight NUMA domains')
    ap.add_argument('--reference-dir', type=Path, help='directory produced by scaling-reference')
    ap.add_argument('--kml-lib', type=Path, help='directory containing the original libkblas.so.1')
    ap.add_argument('--instruction-mode', choices=('counter', 'trace', 'both'), default='both')
    args = ap.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        ap.error('Choose an output directory outside the repository')
    if platform.system() != 'Linux' or platform.machine() != 'aarch64':
        ap.error('These binaries require AArch64 Linux')
    if args.experiment == 'scaling-reference':
        out.mkdir(parents=True, exist_ok=False)
        for length in (2048, 10240):
            subprocess.run([str(ROOT/'bin/scaling_reference'), str(length), '296',
                            str(out/('L%d.f64' % length))], check=True)
        print('Generated both scalar FP64 reference files in '+str(out))
        return
    job, cpus = native_environment()
    if args.experiment == 'scaling':
        if not args.reference_dir:
            ap.error('scaling requires --reference-dir; generate references on the login host first')
        for length in (2048, 10240):
            p = args.reference_dir.resolve()/('L%d.f64' % length)
            if p.stat().st_size != 296*4096*8:
                ap.error('Incomplete scaling reference file: '+str(p))
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    if args.kml_lib:
        env['LD_LIBRARY_PATH'] = str(args.kml_lib.resolve())+':'+env.get('LD_LIBRARY_PATH', '')
    metadata = dict(experiment=args.experiment, job=job, host=platform.node(),
                    cpus=cpus, started=dt.datetime.now(dt.timezone.utc).isoformat(), commands=[])

    def run(label, command, existing=False):
        destination = out/label
        if existing:
            destination.mkdir()
        command = [str(x) for x in command]
        command = [str(destination) if x == '{output}' else x for x in command]
        print(label, flush=True)
        row = dict(label=label, command=command, started=dt.datetime.now(dt.timezone.utc).isoformat())
        metadata['commands'].append(row)
        t0 = time.monotonic()
        with (out/(label+'.log')).open('wb') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        row.update(exit_code=result.returncode, seconds=time.monotonic()-t0,
                   ended=dt.datetime.now(dt.timezone.utc).isoformat())
        (out/'test_record.json').write_text(json.dumps(metadata, indent=2)+'\n')
        if result.returncode:
            raise RuntimeError('%s exited %d; see %s' % (label, result.returncode, out/(label+'.log')))

    if args.experiment == 'instructions':
        if not shutil.which('numactl'):
            ap.error('Instruction measurements require numactl')
        cpu = cpus[0]
        node = cpu_node(cpu)
        methods = [('sme', 0), ('sme', 1), ('me', 0), ('xnn_f', 0),
                   ('xnn_nf', 1), ('acl', 4), ('acl', 3)]
        modes = ('counter', 'trace') if args.instruction_mode == 'both' else (args.instruction_mode,)
        for mode in modes:
            for binary, method in methods:
                command = ['numactl', '--physcpubind=%d' % cpu, '--membind=%d' % node]
                if mode == 'trace':
                    command.append(ROOT/'bin/instructions_trace')
                command += [ROOT/('bin/instructions_'+binary), method, node, mode]
                run('%s_%d_%s' % (binary, method, mode), command)
    else:
        expected = 379 if args.experiment.startswith('xnnpack-') else 343
        if len(cpus) != expected:
            ap.error('%s requires exactly %d allocated CPUs' % (args.experiment, expected))
        nodes, workers, control = worker_mapping(cpus)
        env.update(NSLS_WORKER_CPUS=','.join(str(c) for c, _ in workers),
                   NSLS_CONTROL_CPU=str(control), NSLS_WORKER_NODES=','.join(map(str, nodes)),
                   TASK05_EXPECTED_NODE=platform.node())
        process = args.round-1 if args.process is None else args.process
        if args.experiment == 'shapes':
            path = out/'binding.txt'
            path.write_text('ITEM6_NATIVE_A01 %s %s %d 296 %d\n' %
                            (job, platform.node(), len(cpus), control)+
                            ''.join('%d %d\n' % row for row in workers))
            for dim, groups in ((64, 1), (128, 1), (128, 8)):
                run('d%d_g%d' % (dim, groups), [ROOT/('bin/shapes_d%d' % dim), groups, path, '{output}', process])
        elif args.experiment == 'acl':
            run('acl', [ROOT/'bin/acl', args.round, process+1, '{output}'], existing=True)
        else:
            magic, field, identity = 'FC_PROFILE_V1', 'profile_sha256', '1'*64
            counterparts = {
                'meatten': ('FC_PROFILE_MEATTEN_INDEPENDENT', 'meatten_independent', 'smedecode_meatten'),
                'xnnpack-fused': ('FC_PROFILE_TASK05_INDEPENDENT', 'xnnpack_fused_independent', 'smedecode_xnnpack_fused'),
                'xnnpack-nonfused': ('FC_PROFILE_V6_TASK04', 'v6_task_04', 'smedecode_xnnpack_nonfused')}
            if args.experiment in counterparts:
                magic, identity, counterpart = counterparts[args.experiment]
                field = 'mapping_identity'
                baseline = args.experiment.replace('-', '_')
                run(baseline, [ROOT/('bin/'+baseline), args.round, '{output}'], existing=True)
                binaries = [('smedecode', ROOT/('bin/'+counterpart))]
            elif args.experiment == 'ablation':
                binaries = [(arm, ROOT/('bin/ablation_'+arm)) for arm in ('base', 'k', 'kv', 'full')]
            elif args.experiment == 'key-block':
                binaries = [('keys%d' % k, ROOT/('bin/key_block_%d' % k)) for k in (16, 32, 256)]
            elif args.experiment == 'common-exp':
                binaries = [(name, ROOT/('bin/'+name)) for name in ('original_exp', 'common_exp')]
            elif args.experiment == 'scaling':
                field, identity = 'profile_id', 'release_scaling'+('_spread8' if args.spread else '')
                if args.spread:
                    counts = [args.workers//8+(i < args.workers % 8) for i in range(8)]
                    workers = [(38*n+j, n) for i, n in enumerate(nodes) for j in range(counts[i])]
                else:
                    workers = workers[:args.workers]
                env['SCALE_REFERENCE_ROOT'] = str(args.reference_dir.resolve())
                binaries = [('scaling', ROOT/'bin/core_scaling')]
            else:
                binaries = [('smeatten', ROOT/'bench_aarch64')]
            path = out/'binding.txt'
            binding(path, job, cpus, workers, control, magic, field, identity)
            for label, binary in binaries:
                command = [binary, 'native', path, identity, '{output}', process, 'formal']
                if args.experiment == 'scaling':
                    command.append(10240 if args.spread else 0)
                run(label, command)
    metadata.update(completed=dt.datetime.now(dt.timezone.utc).isoformat(), status='completed')
    (out/'test_record.json').write_text(json.dumps(metadata, indent=2)+'\n')


if __name__ == '__main__':
    main()
