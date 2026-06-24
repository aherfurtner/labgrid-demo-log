def test_echo_command(lxshell):
    stdout, stderr, returncode = lxshell.run('echo "hello"')
    assert returncode == 0
    assert stdout == ["hello"]
    assert stderr == []
