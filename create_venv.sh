deactivate

rm -rf venv

python3 -m venv venv
source venv/bin/activate

# vscode
python -m pip install --upgrade pip
python -m pip install --upgrade pylint
python -m pip install --upgrade black
python -m pip install --upgrade flake8
python -m pip install --upgrade isort

# requirements.txt
python -m pip install --upgrade pipreqs
python -m pip install --upgrade build
python -m pip install --upgrade twine

# libraries
python -m pip install zmq
python -m pip install PyYAML

pipreqs --force .