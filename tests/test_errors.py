"""Tests for neonloops.errors."""

from neonloops.errors import NeonloopsApiError, NeonloopsTimeoutError


class TestNeonloopsApiError:
    def test_constructor_with_dict_body(self):
        err = NeonloopsApiError("Bad request", 400, {"error": "Bad request"})
        assert err.status == 400
        assert err.body == {"error": "Bad request"}
        assert str(err) == "Bad request"

    def test_constructor_with_string_body(self):
        err = NeonloopsApiError("Server error", 500, "Internal error text")
        assert err.status == 500
        assert err.body == "Internal error text"
        assert str(err) == "Server error"

    def test_constructor_with_no_body(self):
        err = NeonloopsApiError("Not found", 404)
        assert err.status == 404
        assert err.body is None

    def test_repr(self):
        err = NeonloopsApiError("Unauthorized", 401, None)
        r = repr(err)
        assert "NeonloopsApiError" in r
        assert "status=401" in r
        assert "Unauthorized" in r

    def test_is_exception(self):
        err = NeonloopsApiError("err", 500)
        assert isinstance(err, Exception)


class TestNeonloopsTimeoutError:
    def test_message_includes_timeout(self):
        err = NeonloopsTimeoutError(30.0)
        assert "30.0" in str(err)
        assert "timed out" in str(err).lower()

    def test_timeout_s_field(self):
        err = NeonloopsTimeoutError(120.0)
        assert err.timeout_s == 120.0

    def test_is_exception(self):
        err = NeonloopsTimeoutError(5.0)
        assert isinstance(err, Exception)

    def test_different_timeout_values(self):
        for val in [0.5, 1.0, 60.0, 300.0]:
            err = NeonloopsTimeoutError(val)
            assert err.timeout_s == val
            assert str(val) in str(err)
