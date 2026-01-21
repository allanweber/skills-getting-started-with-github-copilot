import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client, reset_activities):
        """Test successfully retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9  # Should have 9 activities
    
    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_participants_is_list(self, client, reset_activities):
        """Test that participants field is always a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_details in data.values():
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistentActivity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signup fails if student is already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_updates_participant_count(self, client, reset_activities):
        """Test that participant count is updated after signup"""
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1
    
    def test_signup_different_activities(self, client, reset_activities):
        """Test signup for different activities"""
        activities_to_test = ["Chess Club", "Programming Class", "Basketball"]
        
        for i, activity in enumerate(activities_to_test):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister for non-existent activity"""
        response = client.delete(
            "/activities/NonExistentActivity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregister fails if student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_updates_participant_count(self, client, reset_activities):
        """Test that participant count is updated after unregister"""
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants from an activity"""
        # Chess Club has 2 participants initially
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        client.delete(
            "/activities/Chess Club/unregister?email=daniel@mergington.edu"
        )
        
        response = client.get("/activities")
        assert len(response.json()["Chess Club"]["participants"]) == 0


class TestIntegration:
    """Integration tests for signup and unregister workflow"""

    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering"""
        email = "integration_test@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Verify participant was added
        response2 = client.get("/activities")
        assert email in response2.json()[activity]["participants"]
        
        # Unregister
        response3 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response3.status_code == 200
        
        # Verify participant was removed
        response4 = client.get("/activities")
        assert email not in response4.json()[activity]["participants"]
    
    def test_signup_multiple_then_unregister_one(self, client, reset_activities):
        """Test signing up multiple students and unregistering one"""
        activity = "Chess Club"
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        # Sign up both students
        client.post(f"/activities/{activity}/signup?email={student1}")
        client.post(f"/activities/{activity}/signup?email={student2}")
        
        # Verify both are registered
        response = client.get("/activities")
        assert student1 in response.json()[activity]["participants"]
        assert student2 in response.json()[activity]["participants"]
        
        # Unregister first student
        client.delete(f"/activities/{activity}/unregister?email={student1}")
        
        # Verify only second student remains
        response = client.get("/activities")
        assert student1 not in response.json()[activity]["participants"]
        assert student2 in response.json()[activity]["participants"]
