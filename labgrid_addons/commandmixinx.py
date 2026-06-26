from labgrid.driver.commandmixin import CommandMixin
from labgrid.driver.common import Driver
from labgrid.driver.exception import ExecutionError
from labgrid.step import step


class CommandMixinX(CommandMixin):
    @Driver.check_active
    @step(args=["cmd", "pattern"], result=True)
    def run_expect(self, cmd, pattern, timeout=30.0, codec="utf-8", decodeerrors="strict"):
        stdout, stderr, returncode = self.run(
            cmd, timeout=timeout, codec=codec, decodeerrors=decodeerrors
        )
        if returncode != 0:
            raise ExecutionError(cmd, stdout, stderr)

        if not any(pattern in line for line in [*stdout, *stderr]):
            raise ExecutionError(f"Pattern not found in output: {pattern}", stdout, stderr)

        return stdout
