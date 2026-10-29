"""EcTool regressions: no IOC, EtherCAT device or real caput is used."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EcToolTests(unittest.TestCase):
    def test_compile_against_installed_epics_headers(self):
        compiler, softioc = shutil.which('c++'), shutil.which('softIoc')
        if not compiler or not softioc:
            self.skipTest('C++ compiler and EPICS headers required')
        roots = [p for p in Path(softioc).resolve().parents
                 if (p / 'include/aSubRecord.h').exists()]
        if not roots:
            self.skipTest('EPICS headers not found beside softIoc')
        include = roots[0] / 'include'
        import platform
        os_name = 'Darwin' if platform.system() == 'Darwin' else 'Linux'
        compiler_name = 'clang' if os_name == 'Darwin' else 'gcc'
        command = [compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only']
        for folder in [include, include / 'os' / os_name, include / 'compiler' / compiler_name]:
            command += ['-isystem', str(folder)]
        subprocess.run(command + [str(ROOT / 'src/ethercatTool.cpp')],
                       check=True, capture_output=True, text=True)

    def test_record_initialization_and_metadata_snapshot(self):
        compiler = shutil.which('c++')
        if not compiler:
            self.skipTest('C++ compiler required')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for header in ['aSubRecord.h', 'dbAccess.h', 'dbAddr.h', 'dbDefs.h',
                           'epicsEvent.h', 'epicsExport.h', 'epicsMutex.h',
                           'epicsThread.h', 'registryFunction.h']:
                (path / header).write_text('#include "epics_stubs.h"\n')
            source = path / 'record.cpp'
            source.write_text(r'''
#include "ethercatTool.cpp"
#include <cassert>
int main() {
    aSubRecord r = {};
    strcpy(r.name, "IOC:m0-EcTool");
    double master=0, command=5, slave=4, channel=1, argument=0, trigger=1;
    r.a=&master; r.b=&command; r.d=&slave; r.e=&channel; r.i=&argument; r.u=&trigger;
    r.fta=r.ftb=r.ftd=r.fte=r.fti=r.ftu=DBF_DOUBLE;
    r.ftr=r.fts=r.ftt=DBF_STRING;
    r.inpr.type=r.inps.type=r.inpt.type=PV_LINK;
    r.inpr.value.pv_link.pvname="prefix";
    r.inps.value.pv_link.pvname="epics";
    r.inpt.value.pv_link.pvname="version";
    testDatabase["prefix"]="IOC:";
    testDatabase["epics"]="7.0.8";
    testDatabase["version"]="9.0.0-rc1";
    initEtherCATTool(&r);
    assert(r.dpvt);
    EcToolContext *first=static_cast<EcToolContext *>(r.dpvt);
    testDatabase["prefix"]="ATTACKER:";
    testDatabase["version"]="../../tmp";
    assert(runEtherCATTool(&r)==0);
    assert(first->job.back()=="IOC:");
    assert(first->job[4]=="/ioc/modules/ecmccfg/9.0.0-rc1/R7.0.8/ecToolEthercatMaster.sh");
    assert(testSignals==1 && first->busy);
    assert(runEtherCATTool(&r)==-1 && testSignals==1); // busy rejects, no requeue
    first->busy=false;
    command=999;
    assert(runEtherCATTool(&r)==-1 && testSignals==1); // no stale job execution
    trigger=0;
    assert(runEtherCATTool(&r)==0 && testSignals==1);
    aSubRecord second=r;
    initEtherCATTool(&second);
    assert(!second.dpvt); // traversal in startup config fails closed
    testDatabase["version"]="9.0.0";
    initEtherCATTool(&second);
    assert(second.dpvt && second.dpvt!=r.dpvt);
    assert(static_cast<EcToolContext *>(second.dpvt)->prefix=="ATTACKER:");
    assert(first->prefix=="IOC:"); // independent per-record startup snapshots
}
''')
            subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
                            '-I', directory, '-I', str(ROOT / 'tests/fixtures/ectool'),
                            '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'record')],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(path / 'record')], check=True, capture_output=True, text=True)

    def test_command_builder_and_spawn(self):
        compiler = shutil.which('c++')
        if not compiler:
            self.skipTest('C++ compiler required')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            source = path / 'test.cpp'
            source.write_text(r'''
#include "ecToolCommand.h"
#include <cassert>
#include <limits>
#include <unistd.h>
int main(int argc, char **argv) {
    using namespace ecTool;
    Arguments a, env;
    const std::string dir = "/ioc/modules/ecmccfg/v9/R7.0.8";
    const int commands[] = {5,11,20,70621,70622};
    const char *scripts[] = {"ecToolEthercatMaster.sh", "ecToolEthercatSlaves.sh",
        "ecToolReadHwDiag.sh", "ecToolEL7062_triggTune.sh", "ecToolEL7062_readBackParams.sh"};
    for (int i=0; i<5; ++i) {
        assert(build(dir, "IOC:", 0, commands[i], 4, 2, 0, a));
        Arguments expected;
        expected.push_back("/bin/bash"); expected.push_back("--noprofile");
        expected.push_back("--norc"); expected.push_back("--");
        expected.push_back(dir + "/" + scripts[i]); expected.push_back("0");
        if (i>=2) expected.push_back("4");
        if (i>=3) expected.push_back("2");
        expected.push_back("IOC:");
        assert(a == expected);
    }
    const int states[] = {1,2,3,4,8};
    const char *names[] = {"INIT","PREOP","BOOT","SAFEOP","OP"};
    for (int i=0; i<5; ++i) {
        assert(build(dir, "IOC:", 3, 10, 65535, 0, states[i], a));
        assert(a.size()==5 && a[0]=="/opt/etherlab/bin/ethercat" &&
               a[1]=="states" && a[2]=="-m3" && a[3]=="-p65535" && a[4]==names[i]);
    }
    assert(!build(dir,"IOC:",0,10,0,0,7,a));
    assert(!build(dir,"IOC:",0,123,0,0,0,a));
    assert(!build(dir,"IOC:",0,70621,0,3,0,a));
    assert(!build(dir,"IOC:",0,20,65536,0,0,a));
    assert(!build(dir,"-S",0,5,0,0,0,a));
    const double bad[] = {-1, 0.5, std::numeric_limits<double>::infinity(),
                          std::numeric_limits<double>::quiet_NaN(), 2147483648.0};
    for (unsigned i=0; i<sizeof(bad)/sizeof(*bad); ++i)
        assert(!build(dir,"IOC:",bad[i],5,0,0,0,a));
    assert(versionComponent("9.0.0-rc1+test"));
    assert(!versionComponent("..") && !versionComponent("../../tmp") &&
           !versionComponent("v1;id") && !versionComponent("$(id)"));
    assert(!safeEnvironmentEntry("BASH_ENV=/tmp/hook"));
    assert(!safeEnvironmentEntry("ENV=hook") && !safeEnvironmentEntry("SHELLOPTS=x"));
    assert(!safeEnvironmentEntry("BASH_FUNC_caput%%=bad"));
    assert(safeEnvironmentEntry("PATH=/usr/bin:/bin"));
    // Execute the production spawn routine against an inert script; shell
    // metacharacters in a prefix must survive literally in a single argument.
    assert(build(argv[1], ";touch marker;$(touch marker) `touch marker` *",0,5,0,0,0,a));
    env.push_back("PATH=/usr/bin:/bin");
    assert(execute(a,env)==0);
    assert(access("marker",F_OK)!=0);
    a.clear(); a.push_back("/nonexistent-ecmc-audit-executable");
    assert(execute(a,env)!=0);
    a.clear(); a.push_back("/bin/bash"); a.push_back("-c"); a.push_back("exit 17");
    assert(execute(a,env)==17);
}
''')
            (path / 'ecToolEthercatMaster.sh').write_text(
                '#!/bin/bash\nprintf "%s\\n" "$#" "$1" "$2" > received\n')
            subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra',
                            '-I', str(ROOT / 'src'), str(source), '-o', str(path / 'test')],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(path / 'test'), directory], cwd=directory, check=True)
            self.assertEqual((path / 'received').read_text().splitlines(),
                             ['2', '0', ';touch marker;$(touch marker) `touch marker` *'])

    def test_helpers_with_stubbed_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            log = path / 'calls.jsonl'
            stub = path / 'stub'
            # Absolute interpreter avoids relying on a particular Python PATH.
            import sys
            stub.write_text(f'#!{sys.executable}\n' + r'''
import json, os, sys
with open(os.environ['EC_TEST_LOG'], 'a') as f:
    f.write(json.dumps([os.path.basename(sys.argv[0])] + sys.argv[1:]) + '\n')
if os.path.basename(sys.argv[0]) == 'ethercat' and 'upload' in sys.argv:
    print(os.environ.get('EC_TEST_DATA', '0x00 0'))
''')
            stub.chmod(0o700)
            for name in ['ethercat', 'caput', 'python3']:
                (path / name).symlink_to(stub)
            # Only substitute the absolute device executable in temporary
            # copies. Script control flow and argument handling stay unchanged.
            for script in (ROOT / 'scripts').glob('ecTool*.sh'):
                text = script.read_text().replace('/opt/etherlab/bin/ethercat', str(path / 'ethercat'))
                (path / script.name).write_text(text)
                subprocess.run(['/bin/bash', '-n', str(path / script.name)], check=True)
            env = dict(os.environ, PATH=directory + ':/usr/bin:/bin', EC_TEST_LOG=str(log))
            for key in ['BASH_ENV', 'ENV', 'SHELLOPTS', 'BASHOPTS']:
                env.pop(key, None)
            prefix = 'IOC:;$(touch marker)`touch marker` *'
            cases = {'ecToolEthercatMaster.sh': ['0', prefix],
                     'ecToolEthercatSlaves.sh': ['0', prefix],
                     'ecToolReadHwDiag.sh': ['0', '4', prefix],
                     'ecToolEL7062_triggTune.sh': ['0', '4', '1', prefix],
                     'ecToolEL7062_readBackParams.sh': ['0', '4', '2', prefix]}
            for script, arguments in cases.items():
                with self.subTest(script=script):
                    log.write_text('')
                    result = subprocess.run(['/bin/bash', str(path / script), *arguments],
                                            cwd=path, env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    calls = [json.loads(line) for line in log.read_text().splitlines()]
                    caputs = [call for call in calls if call[0] == 'caput']
                    self.assertTrue(caputs)
                    for call in caputs:
                        pv = call[2] if call[1] == '-S' else call[1]
                        self.assertTrue(pv.startswith(prefix), call)
                    self.assertFalse((path / 'marker').exists())
            for script, arguments in cases.items():
                log.write_text('')
                bad = ['0;touch marker', *arguments[1:]]
                result = subprocess.run(['/bin/bash', str(path / script), *bad], cwd=path,
                                        env=env, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(log.read_text(), '')
            # Malformed device output must not enter Bash arithmetic evaluation.
            env['EC_TEST_DATA'] = '0x00 a[$(touch${IFS}marker)]'
            result = subprocess.run(['/bin/bash', str(path / 'ecToolEL7062_readBackParams.sh'),
                                     '0', '4', '1', 'IOC:'], cwd=path, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((path / 'marker').exists())


if __name__ == '__main__':
    unittest.main()
