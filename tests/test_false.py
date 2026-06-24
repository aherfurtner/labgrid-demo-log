def test_false_command(lxshell):
    stdout, stderr, returncode = lxshell.run("false")
    assert returncode != 0
    assert stdout == []
    assert stderr == []
