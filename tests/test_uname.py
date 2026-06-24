def test_uname_command(lxshell):
    stdout, stderr, returncode = lxshell.run("uname")
    assert returncode == 0
    assert stdout == ["Linux"]
    assert stderr == []

    stdout, stderr, returncode = lxshell.run("uname -a")
    assert returncode == 0
    assert stdout
    assert "Linux" in stdout[0]
    assert stderr == []
