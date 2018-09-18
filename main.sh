#!/usr/bin/env bash
export PYENV_ROOT="$HOME/.pyenv"
if [ ! -d $PYENV_ROOT ]; then
    git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT
fi

export PATH="$PYENV_ROOT/bin:$PATH"
pyenv install -s $(cat .python-version)

eval "$(pyenv init -)"

pip install pipenv
python -m pipenv check || python -m pipenv --rm
python -m pipenv sync || python -m pipenv install

python -m pipenv run python main.py
