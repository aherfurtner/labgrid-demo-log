def test_hostshell_echo_command(hostshell):
    stdout, stderr, returncode = hostshell.run('echo "host-ok"')
    assert returncode == 0
    assert stdout == ["host-ok"]
    assert stderr == []
