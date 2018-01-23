# Хак для импорта модуля. Добавляем родительскую директорию в `sys.path`.
import os
import sys
sys.path.insert(0, 
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import re
import random

import engines

SAMPLE_INPUT = "Sample Text"
PROPER_RESULT = "result-PHQGHUMEAYLN"

@pytest.fixture
def create_test_file(tmpdir):
    def create_test_file(content):
        file_name = "test%d.txt" % random.randint(1, 1000)
        test_file = tmpdir.mkdir("test").join(file_name)
        test_file.write(content)
        return str(test_file)
    return create_test_file

@pytest.mark.parametrize("engine", engines.ENGINES)
def test_launch_engine(engine, create_test_file):
    """ Тестируем функцию запуска движка для движка A. """

    test_file = create_test_file(SAMPLE_INPUT)
    output = engines.launch_engine(
        engine, test_file, engines_dir="engines-bin")
    result = output[test_file]
    assert result == PROPER_RESULT