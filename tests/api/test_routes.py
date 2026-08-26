"""API route tests using TestClient with build_identity injection."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

from typing import Final

import pytest
from fastapi.testclient import TestClient
from src.api.app import BuildIdentity, Health, app, build_identity

TEST_RELEASE_ID: Final = "test-release-123"
TEST_SOURCE_DIGEST: Final = "a" * 64


@pytest.fixture(autouse=True)
def _set_build_identity_env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setenv("ALFRED_RELEASE_ID", TEST_RELEASE_ID)
    monkeypatch.setenv("ALFRED_RELEASE_DIGEST", TEST_SOURCE_DIGEST)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def expected_identity() -> BuildIdentity:
    return BuildIdentity(release_id=TEST_RELEASE_ID, source_digest=TEST_SOURCE_DIGEST)


class TestHealthEndpoint:
    def test_health_returns_ok_with_release_id(
        self, client: TestClient, expected_identity: BuildIdentity
    ) -> None:
        response = client.get("/health")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert response.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        data = response.json()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert data["status"] == "ok"
        assert data["release_id"] == expected_identity.release_id

    def test_health_response_matches_health_model(self, client: TestClient) -> None:
        response = client.get("/health")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert response.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        health = Health(**response.json())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        assert health.status == "ok"
        assert health.release_id == TEST_RELEASE_ID


class TestVersionEndpoint:
    def test_version_returns_build_identity(
        self, client: TestClient, expected_identity: BuildIdentity
    ) -> None:
        response = client.get("/version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert response.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        data = response.json()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert data["release_id"] == expected_identity.release_id
        assert data["source_digest"] == expected_identity.source_digest

    def test_version_response_matches_build_identity_model(self, client: TestClient) -> None:
        response = client.get("/version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert response.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        identity = BuildIdentity(**response.json())  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        assert identity.release_id == TEST_RELEASE_ID
        assert identity.source_digest == TEST_SOURCE_DIGEST


class TestBuildIdentityInjection:
    def test_build_identity_function_uses_env_vars(self) -> None:
        identity = build_identity()
        assert identity.release_id == TEST_RELEASE_ID
        assert identity.source_digest == TEST_SOURCE_DIGEST

    def test_build_identity_raises_when_env_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ALFRED_RELEASE_ID", raising=False)
        monkeypatch.delenv("ALFRED_RELEASE_DIGEST", raising=False)
        with pytest.raises(RuntimeError) as exc_info:
            build_identity()
        assert "must be baked into the image" in str(exc_info.value)

    def test_build_identity_raises_when_only_one_env_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ALFRED_RELEASE_ID", "only-release")
        monkeypatch.delenv("ALFRED_RELEASE_DIGEST", raising=False)
        with pytest.raises(RuntimeError):
            build_identity()


class TestEndpointsIntegration:
    def test_health_and_version_release_ids_match(self, client: TestClient) -> None:
        health_resp = client.get("/health")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        version_resp = client.get("/version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert health_resp.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        assert version_resp.status_code == 200  # pyright: ignore[reportUnknownMemberType]
        assert health_resp.json()["release_id"] == version_resp.json()["release_id"]  # pyright: ignore[reportUnknownMemberType]

    def test_multiple_requests_return_consistent_identity(self, client: TestClient) -> None:
        for _ in range(5):
            resp = client.get("/version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            assert resp.status_code == 200  # pyright: ignore[reportUnknownMemberType]
            assert resp.json()["release_id"] == TEST_RELEASE_ID  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            assert resp.json()["source_digest"] == TEST_SOURCE_DIGEST  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
