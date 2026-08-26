"""Tests for error taxonomy (src/domain/errors.py)."""

from __future__ import annotations

import pytest

from domain.errors import (
    AlfredError,
    ContractViolation,
    ErrorClass,
    ExhaustionError,
    InfrastructureError,
    LengthMismatch,
    PolicyViolation,
    SelfPairing,
    UnitsViolation,
    UnsortedTimestamps,
    error_class_of,
)


class TestErrorClass:
    """Tests for the ErrorClass enum."""

    def test_five_classes_exist(self) -> None:
        """Taxonomy has exactly five classes."""
        assert len(ErrorClass) == 5

    def test_class_values_are_stable_wire_names(self) -> None:
        """Enum values are the stable wire names."""
        assert ErrorClass.INFRASTRUCTURE.value == "infrastructure"
        assert ErrorClass.POLICY_VIOLATION.value == "policy_violation"
        assert ErrorClass.CRITERION_FAILURE.value == "criterion_failure"
        assert ErrorClass.EXHAUSTION.value == "exhaustion"
        assert ErrorClass.CONTRACT_VIOLATION.value == "contract_violation"


class TestAlfredErrorHierarchy:
    """Tests for the AlfredError base class and subclasses."""

    def test_base_class_default_is_contract_violation(self) -> None:
        """AlfredError defaults to CONTRACT_VIOLATION."""
        assert AlfredError.error_class == ErrorClass.CONTRACT_VIOLATION

    def test_infrastructure_error_class(self) -> None:
        """InfrastructureError maps to INFRASTRUCTURE."""
        assert InfrastructureError.error_class == ErrorClass.INFRASTRUCTURE

    def test_policy_violation_error_class(self) -> None:
        """PolicyViolation maps to POLICY_VIOLATION."""
        assert PolicyViolation.error_class == ErrorClass.POLICY_VIOLATION

    def test_exhaustion_error_class(self) -> None:
        """ExhaustionError maps to EXHAUSTION."""
        assert ExhaustionError.error_class == ErrorClass.EXHAUSTION

    def test_contract_violation_error_class(self) -> None:
        """ContractViolation maps to CONTRACT_VIOLATION."""
        assert ContractViolation.error_class == ErrorClass.CONTRACT_VIOLATION

    def test_units_violation_inherits_contract_violation(self) -> None:
        """UnitsViolation is a ContractViolation."""
        assert issubclass(UnitsViolation, ContractViolation)
        assert UnitsViolation.error_class == ErrorClass.CONTRACT_VIOLATION

    def test_unsorted_timestamps_inherits_contract_violation(self) -> None:
        """UnsortedTimestamps is a ContractViolation."""
        assert issubclass(UnsortedTimestamps, ContractViolation)
        assert UnsortedTimestamps.error_class == ErrorClass.CONTRACT_VIOLATION

    def test_length_mismatch_inherits_contract_violation(self) -> None:
        """LengthMismatch is a ContractViolation."""
        assert issubclass(LengthMismatch, ContractViolation)
        assert LengthMismatch.error_class == ErrorClass.CONTRACT_VIOLATION

    def test_self_pairing_inherits_contract_violation(self) -> None:
        """SelfPairing is a ContractViolation."""
        assert issubclass(SelfPairing, ContractViolation)
        assert SelfPairing.error_class == ErrorClass.CONTRACT_VIOLATION


class TestErrorClassOf:
    """Tests for error_class_of function."""

    def test_returns_class_for_alfred_errors(self) -> None:
        """error_class_of returns the declared class for AlfredError subclasses."""
        assert error_class_of(InfrastructureError("down")) == ErrorClass.INFRASTRUCTURE
        assert error_class_of(PolicyViolation("blocked")) == ErrorClass.POLICY_VIOLATION
        assert error_class_of(ExhaustionError("cap")) == ErrorClass.EXHAUSTION
        assert error_class_of(ContractViolation("bug")) == ErrorClass.CONTRACT_VIOLATION
        assert error_class_of(UnitsViolation("bad units")) == ErrorClass.CONTRACT_VIOLATION
        assert error_class_of(UnsortedTimestamps("unsorted")) == ErrorClass.CONTRACT_VIOLATION
        assert error_class_of(LengthMismatch("mismatch")) == ErrorClass.CONTRACT_VIOLATION
        assert error_class_of(SelfPairing("self")) == ErrorClass.CONTRACT_VIOLATION

    def test_raises_for_unknown_error_types(self) -> None:
        """error_class_of raises ContractViolation for errors outside taxonomy."""
        with pytest.raises(ContractViolation) as exc:
            error_class_of(ValueError("unknown"))
        assert "error type is outside the taxonomy" in str(exc.value)
        assert "ValueError" in str(exc.value)

    def test_raises_for_builtin_exceptions(self) -> None:
        """Builtin exceptions raise ContractViolation."""
        with pytest.raises(ContractViolation):
            error_class_of(RuntimeError("fail"))
        with pytest.raises(ContractViolation):
            error_class_of(KeyError("missing"))
        with pytest.raises(ContractViolation):
            error_class_of(TypeError("bad type"))


class TestErrorInstantiation:
    """Tests that error types can be instantiated and raised."""

    def test_all_errors_raisable(self) -> None:
        """Each error type can be raised and caught."""
        with pytest.raises(InfrastructureError):
            raise InfrastructureError("model server down")

        with pytest.raises(PolicyViolation):
            raise PolicyViolation("protected path write")

        with pytest.raises(ExhaustionError):
            raise ExhaustionError("turn cap reached")

        with pytest.raises(ContractViolation):
            raise ContractViolation("caller bug")

        with pytest.raises(UnitsViolation):
            raise UnitsViolation("wrong unit")

        with pytest.raises(UnsortedTimestamps):
            raise UnsortedTimestamps("timestamps not sorted")

        with pytest.raises(LengthMismatch):
            raise LengthMismatch("arrays differ")

        with pytest.raises(SelfPairing):
            raise SelfPairing("ego paired with self")

    def test_all_errors_catchable_as_alfred_error(self) -> None:
        """All errors are catchable as AlfredError."""
        for exc_type in [
            InfrastructureError,
            PolicyViolation,
            ExhaustionError,
            ContractViolation,
            UnitsViolation,
            UnsortedTimestamps,
            LengthMismatch,
            SelfPairing,
        ]:
            with pytest.raises(AlfredError):
                raise exc_type("test")

    def test_contract_violation_catches_subclasses(self) -> None:
        """ContractViolation catches its subclasses."""
        with pytest.raises(ContractViolation):
            raise UnitsViolation("bad")

        with pytest.raises(ContractViolation):
            raise UnsortedTimestamps("bad")

        with pytest.raises(ContractViolation):
            raise LengthMismatch("bad")

        with pytest.raises(ContractViolation):
            raise SelfPairing("bad")
