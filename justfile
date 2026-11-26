set dotenv-load
set positional-arguments

export VIRTUAL_ENV := justfile_directory() / ".venv"

default:
    @echo 'Run the labels CLI: just run pole, just run cable --preview < cables.txt'

run *args:
    @uv run labels "$@"

# Render sample labels for every preset into demo/
demo:
    @uv run python demo.py
