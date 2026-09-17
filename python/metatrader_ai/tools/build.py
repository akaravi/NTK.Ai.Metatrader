import subprocess
import os

from .tool import Tool, Property, Parameters

def build_mql5(mq5_path: str, metaeditor_path: str = r"C:\Program Files\MetaTrader 5\metaeditor64.exe") -> str:
    """
    Compiles an MQL5 file using MetaEditor and returns the log output.
    """
    log_path = mq5_path.replace(".mq5", ".log")

    # Remove old log so we don't read stale results
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except PermissionError:
            pass 

    subprocess.run(
        [metaeditor_path, f'/compile:{mq5_path}', '/log'],
        capture_output=True,
        text=True,
        check=False
    )

    if not os.path.exists(log_path):
        return "No log file generated. Compilation may have failed silently."

    with open(log_path, "r", encoding="utf-16") as f:
        log = f.read()

    return log

TOOL_BUILD_MQL5 = Tool(
    name="build_mql5",
    description="Compile an MQL5 file and return the log output.",
    parameters=Parameters(
        properties=[
            Property(
                name="mq5_path",
                type="string",
                description="Path to the MQL5 file to compile.",
                required=True,
            ),
            Property(
                name="metaeditor_path",
                type="string",
                description="Path to the MetaEditor executable. Defaults to 'C:\\Program Files\\MetaTrader 5\\metaeditor64.exe'.",
                required=False,
            ),
        ]
    ),
)