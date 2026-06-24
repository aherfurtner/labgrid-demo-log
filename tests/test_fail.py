def test_intentional_failure(lxshell):
    _, _, returncode = lxshell.run("false")
    assert returncode == 0
