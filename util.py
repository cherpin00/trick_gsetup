import subprocess

def run(program):
    process = subprocess.run(program.split(" "), capture_output=True)
    return process