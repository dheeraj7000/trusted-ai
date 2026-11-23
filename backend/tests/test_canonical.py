"""Tests for canonical JSON serialization."""
from app.evidence.canonical import canonical_json_hash, canonical_json_serialize


class TestCanonicalJsonSerialize:
    def test_deterministic_output_different_key_orders(self):
        """Same logical dict with different key insertion orders produces identical bytes."""
        a = {"z": 1, "a": 2, "m": {"b": 3, "a": 4}}
        b = {"a": 2, "m": {"a": 4, "b": 3}, "z": 1}
        assert canonical_json_serialize(a) == canonical_json_serialize(b)

    def test_nested_dict_sorted(self):
        obj = {"b": {"d": 1, "c": 2}, "a": 3}
        result = canonical_json_serialize(obj)
        assert result == b'{"a":3,"b":{"c":2,"d":1}}'

    def test_list_order_preserved(self):
        """Lists are not re-sorted - only dict keys are."""
        obj = {"items": [3, 1, 2]}
        result = canonical_json_serialize(obj)
        assert result == b'{"items":[3,1,2]}'

    def test_pydantic_model(self):
        """Pydantic models are converted to dicts before serialization."""
        from app.models import PolicyConfig

        config = PolicyConfig(
            policy_version="v1",
            refund_autonomous_limit=100,
            human_approval_above=100,
            allowed_data_destinations=["internal://case-system"],
            sensitive_fields=["ssn"],
        )
        result = canonical_json_serialize(config)
        assert b'"policy_version":"v1"' in result


class TestCanonicalJsonHash:
    def test_consistent_hash_same_data(self):
        a = {"z": 1, "a": 2}
        b = {"a": 2, "z": 1}
        assert canonical_json_hash(a) == canonical_json_hash(b)

    def test_different_data_different_hash(self):
        a = {"key": "value1"}
        b = {"key": "value2"}
        assert canonical_json_hash(a) != canonical_json_hash(b)

    def test_hash_is_hex_sha256(self):
        result = canonical_json_hash({"hello": "world"})
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)
