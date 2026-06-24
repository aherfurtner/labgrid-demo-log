import attr
from labgrid.driver.commandmixin import CommandMixin
from labgrid.driver.common import Driver
from labgrid.factory import target_factory
from labgrid.protocol import CommandProtocol
from labgrid.step import step


@target_factory.reg_driver
@attr.s(eq=False)
class FakeShellDriver(CommandMixin, Driver, CommandProtocol):
    @step(title="write", tag="console", args=["data"])
    def _fake_console_write(self, data):
        del data

    @step(title="read", result=True, tag="console")
    def _fake_console_read(self, payload):
        # ConsoleLoggingReporter writes bytes from console-tagged read/stop steps.
        return payload

    def _simulate_command(self, cmd):
        if cmd == "uname":
            return (["Linux"], [], 0)
        if cmd == "uname -a":
            return (["Linux fake-target 6.1.0-labgrid #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux"], [], 0)
        if cmd == "true":
            return ([], [], 0)
        if cmd == "false":
            return ([], [], 1)
        if cmd.startswith("echo "):
            return ([cmd[5:].strip().strip('"').strip("'")], [], 0)
        if cmd == "cat /proc/version":
            return (["Linux version 6.1.0-labgrid-fake"], [], 0)
        return ([f"fake-shell executed: {cmd}"], [], 0)

    def _run(self, cmd, *, timeout=30.0, codec="utf-8", decodeerrors="strict"):
        del timeout, codec, decodeerrors
        stdout, stderr, rc = self._simulate_command(cmd)

        self._fake_console_write(f"{cmd}\r\n".encode("utf-8"))

        console_lines = [f"root@fake:~# {cmd}"]
        console_lines.extend(stdout)
        console_lines.extend(f"stderr: {line}" for line in stderr)
        if rc != 0:
            console_lines.append(f"[exit:{rc}]")
        self._fake_console_read(("\r\n".join(console_lines) + "\r\n").encode("utf-8"))

        return (stdout, stderr, rc)

    @Driver.check_active
    @step(args=["cmd"], result=True)
    def run(self, cmd, timeout=30.0, codec="utf-8", decodeerrors="strict"):
        return self._run(cmd, timeout=timeout, codec=codec, decodeerrors=decodeerrors)

    @Driver.check_active
    @step()
    def get_status(self):
        return 1