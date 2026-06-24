def test_true_command(lxshell):
    stdout, stderr, returncode = lxshell.run("true")
    assert returncode == 0
    assert stdout == []
    assert stderr == []
