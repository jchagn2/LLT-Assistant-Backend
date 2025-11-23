import uuid
from unittest.mock import MagicMock

import pytest

from app.analyzers.ast_parser import ParsedTestFile, TestClassInfo, TestFunctionInfo
from app.core.analysis.uncertain_case_detector import UncertainCaseDetector


@pytest.fixture
def detector():
    return UncertainCaseDetector()


def create_mock_func(name, assertions=[], decorators=[], source_code=""):
    func = MagicMock(spec=TestFunctionInfo)
    func.name = name
    func.assertions = assertions
    func.decorators = decorators
    func.source_code = source_code
    func.unique_id = uuid.uuid4()
    return func


def test_identify_uncertain_cases_similar_names(detector):
    func1 = create_mock_func("test_user_creation_success")
    func2 = create_mock_func("test_user_creation_failure")
    func3 = create_mock_func("test_product_update_logic")
    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2, func3]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert func1 in uncertain
    assert func2 in uncertain
    assert func3 not in uncertain


def test_identify_uncertain_cases_complex_assertions(detector):
    assertion1 = MagicMock()
    assertion1.assertion_type = "equality"
    assertion2 = MagicMock()
    assertion2.assertion_type = "other"

    func1 = create_mock_func("check_complex_output_validation")
    func1.assertions = [assertion1, assertion2]
    func2 = create_mock_func("verify_simple_return_value")
    func2.assertions = [assertion1]

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert func1 in uncertain
    assert func2 not in uncertain


def test_identify_uncertain_cases_unusual_patterns(detector):
    func1 = create_mock_func("test_case_with_sleep_call")
    func1.source_code = "import time; time.sleep(1)"
    func2 = create_mock_func("test_case_with_global_keyword")
    func2.source_code = "global x; x = 1"
    func3 = create_mock_func("test_case_with_many_decorators")
    func3.decorators = [1, 2, 3, 4]
    func4 = create_mock_func("a_regular_test_case_for_patterns")

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2, func3, func4]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert func1 in uncertain
    assert func2 in uncertain
    assert func3 in uncertain
    assert func4 not in uncertain


def test_are_similar_functions(detector):
    func1 = create_mock_func("test_get_user_by_id")
    func2 = create_mock_func("test_get_user_by_name")
    func3 = create_mock_func("test_delete_product_completely")

    assert detector._are_similar_functions(func1, func2) is True
    assert detector._are_similar_functions(func1, func3) is False


def test_has_unusual_patterns(detector):
    func_sleep = create_mock_func("test_sleep", source_code="time.sleep(1)")
    func_global = create_mock_func("test_global", source_code="global my_var")
    # More than MIN_DECORATORS_FOR_UNUSUAL (3)
    func_decorators = create_mock_func("test_decorators", decorators=[1, 2, 3, 4, 5, 6])
    func_normal = create_mock_func("test_normal", source_code="x = 1")

    assert detector._has_unusual_patterns(func_sleep) is True
    assert detector._has_unusual_patterns(func_global) is True
    assert detector._has_unusual_patterns(func_decorators) is True
    assert detector._has_unusual_patterns(func_normal) is False


def test_no_uncertain_cases(detector):
    func1 = create_mock_func("validate_user_creation_endpoint")
    func2 = create_mock_func("check_product_deletion_behavior")
    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = [func1, func2]
    parsed_file.test_classes = []

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert len(uncertain) == 0


def test_identify_uncertain_cases_in_classes(detector):
    class_func1 = create_mock_func("test_similar_in_class_a")
    class_func2 = create_mock_func("test_similar_in_class_b")
    test_class = MagicMock(spec=TestClassInfo)
    test_class.methods = [class_func1, class_func2]

    parsed_file = MagicMock(spec=ParsedTestFile)
    parsed_file.test_functions = []
    parsed_file.test_classes = [test_class]

    uncertain = detector.identify_uncertain_cases(parsed_file)
    assert class_func1 in uncertain
    assert class_func2 in uncertain
