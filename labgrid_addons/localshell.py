import subprocess

import attr
from labgrid.driver.commandmixin import CommandMixin
from labgrid.driver.common import Driver
from labgrid.factory import target_factory
from labgrid.protocol import CommandProtocol
from labgrid.step import step


@target_factory.reg_driver
@attr.s(eq=False)
class LocalShellDriver(CommandMixin, Driver, CommandProtocol):
    shell = attr.ib(default="/bin/sh", validator=attr.validators.instance_of(str))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._status = 1

    @step(title="write", tag="console", args=["data"])
    def _console_write(self, data):
        del data

    @step(title="read", result=True, tag="console")
    def _console_read(self, payload):
        # ConsoleLoggingReporter writes bytes from console-tagged read/stop steps.
        return payload

    @staticmethod
    def _decode_stream(data, *, codec, decodeerrors):
        if not data:
            return []
        return data.decode(codec, decodeerrors).splitlines()

    def _run(self, cmd, *, timeout=30.0, codec="utf-8", decodeerrors="strict"):
        self._console_write(f"{cmd}\r\n".encode(codec, decodeerrors))
        completed = subprocess.run(
            [self.shell, "-lc", cmd],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )

        stdout = self._decode_stream(completed.stdout, codec=codec, decodeerrors=decodeerrors)
        stderr = self._decode_stream(completed.stderr, codec=codec, decodeerrors=decodeerrors)
        returncode = completed.returncode

        console_lines = [f"local$ {cmd}", *stdout, *(f"stderr: {line}" for line in stderr)]
        if returncode != 0:
            console_lines.append(f"[exit:{returncode}]")
        self._console_read(("\r\n".join(console_lines) + "\r\n").encode(codec, decodeerrors))

        return (stdout, stderr, returncode)

    @Driver.check_active
    @step(args=["cmd"], result=True)
    def run(self, cmd, timeout=30.0, codec="utf-8", decodeerrors="strict"):
        return self._run(cmd, timeout=timeout, codec=codec, decodeerrors=decodeerrors)

    @step()
    def get_status(self):
        return self._status
