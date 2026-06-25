def test_pingpong_between_dut_and_local_shells(lxshell, hostshell):
    dut_out_1, dut_err_1, dut_rc_1 = lxshell.run('echo "dut-1"')
    assert dut_rc_1 == 0
    assert dut_out_1 == ["dut-1"]
    assert dut_err_1 == []

    local_out_1, local_err_1, local_rc_1 = hostshell.run('echo "local-1"')
    assert local_rc_1 == 0
    assert local_out_1 == ["local-1"]
    assert local_err_1 == []

    dut_out_2, dut_err_2, dut_rc_2 = lxshell.run('echo "dut-2"')
    assert dut_rc_2 == 0
    assert dut_out_2 == ["dut-2"]
    assert dut_err_2 == []

    local_out_2, local_err_2, local_rc_2 = hostshell.run('echo "local-2"')
    assert local_rc_2 == 0
    assert local_out_2 == ["local-2"]
    assert local_err_2 == []
