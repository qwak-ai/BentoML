from bentoml.exceptions import InferenceException


def test_inference_exception_should_convert_string_to_dictionary():
    exception = InferenceException(400, "test")
    assert exception.status_code == 400
    assert exception.message == {"message": "test"}

def test_inference_exception_should_convert_status_200_to_500():
    exception = InferenceException(200, "test")
    assert exception.status_code == 500
    assert exception.message == {
        "message": "test",
        "qwak_backend_message": f"Invalid status code. Given value: 200. Supported: 4xx, 5xx"
    }

def test_inference_exception_should_convert_status_300_to_500():
    exception = InferenceException(300, "test")
    assert exception.status_code == 500
    assert exception.message == {
        "message": "test",
        "qwak_backend_message": f"Invalid status code. Given value: 300. Supported: 4xx, 5xx"
    }

def test_inference_exception_should_convert_status_with_dictionary():
    exception = InferenceException(300, {"my_error": "this_is_my_error"})
    assert exception.status_code == 500
    assert exception.message == {
        "my_error": "this_is_my_error",
        "qwak_backend_message": f"Invalid status code. Given value: 300. Supported: 4xx, 5xx"
    }
