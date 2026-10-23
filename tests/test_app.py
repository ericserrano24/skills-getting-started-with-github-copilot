from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_returns_activity_details_and_participants(client):
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == expected_participants
    assert response.json()["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        (
            "Unknown Activity",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
        (
            "Chess Club",
            "michael@mergington.edu",
            400,
            "Student is already signed up for this activity",
        ),
    ],
)
def test_signup_rejects_unknown_activity_or_duplicate_participant(
    client, activity_name, email, expected_status, expected_detail
):
    # Arrange
    original_participants = (
        app_module.activities.get(activity_name, {}).get("participants", []).copy()
    )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail
    if activity_name in app_module.activities:
        assert app_module.activities[activity_name]["participants"] == original_participants


def test_unregister_removes_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown Activity", "student@mergington.edu", "Activity not found"),
        (
            "Chess Club",
            "not-signed-up@mergington.edu",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_rejects_unknown_activity_or_participant(
    client, activity_name, email, expected_detail
):
    # Arrange
    original_participants = (
        app_module.activities.get(activity_name, {}).get("participants", []).copy()
    )

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == expected_detail
    if activity_name in app_module.activities:
        assert app_module.activities[activity_name]["participants"] == original_participants
