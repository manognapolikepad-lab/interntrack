from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Application, Opportunity, SavedOpportunity, StudentProfile


class InternTrackWorkflowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="maya", password="LongPass!234")
		self.other_user = User.objects.create_user(username="sam", password="LongPass!234")
		self.opportunity = Opportunity.objects.create(
			title="Product Engineering Intern",
			organization="Northstar Labs",
			opportunity_type=Opportunity.Type.INTERNSHIP,
			description="Build useful tools with a thoughtful engineering team.",
			required_skills="Python, Django",
			location="Boston",
			deadline=date.today() + timedelta(days=20),
		)

	def test_registration_creates_profile_and_logs_student_in(self):
		response = self.client.post(reverse("register"), {
			"username": "newstudent",
			"email": "student@example.com",
			"password1": "LongPass!234",
			"password2": "LongPass!234",
		})
		self.assertRedirects(response, reverse("dashboard"))
		self.assertTrue(StudentProfile.objects.filter(user__username="newstudent").exists())
		self.assertTrue(response.wsgi_request.user.is_authenticated)

	def test_dashboard_requires_login(self):
		response = self.client.get(reverse("dashboard"))
		self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

	def test_search_matches_required_skills(self):
		response = self.client.get(reverse("opportunity_list"), {"q": "Django"})
		self.assertContains(response, "Product Engineering Intern")

	def test_login_and_opportunity_details(self):
		login_response = self.client.post(reverse("login"), {
			"username": "maya",
			"password": "LongPass!234",
		})
		self.assertRedirects(login_response, reverse("dashboard"))
		detail_response = self.client.get(reverse("opportunity_detail", args=[self.opportunity.pk]))
		self.assertContains(detail_response, "Build useful tools")

	def test_invalid_login_shows_form_error(self):
		response = self.client.post(reverse("login"), {
			"username": "maya",
			"password": "incorrect",
		})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Please enter a correct username and password")

	def test_logout_returns_to_opportunity_board(self):
		self.client.force_login(self.user)
		response = self.client.post(reverse("logout"))
		self.assertRedirects(response, reverse("opportunity_list"))
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_type_location_and_place_filters(self):
		remote_hackathon = Opportunity.objects.create(
			title="Climate Code Sprint",
			organization="Open Earth",
			opportunity_type=Opportunity.Type.HACKATHON,
			description="A remote weekend build sprint.",
			location="Worldwide",
			is_remote=True,
		)
		response = self.client.get(reverse("opportunity_list"), {
			"type": "hackathon", "location": "remote", "place": "World",
		})
		self.assertEqual(list(response.context["opportunities"]), [remote_hackathon])

	def test_deadline_sort_puts_undated_opportunities_last(self):
		undated = Opportunity.objects.create(
			title="Open workshop",
			organization="Community Lab",
			opportunity_type=Opportunity.Type.WORKSHOP,
			description="A workshop without a fixed deadline.",
		)
		response = self.client.get(reverse("opportunity_list"), {"sort": "deadline"})
		self.assertEqual(list(response.context["opportunities"]), [self.opportunity, undated])

	def test_student_can_add_opportunity_once(self):
		self.client.force_login(self.user)
		url = reverse("add_application", args=[self.opportunity.pk])
		self.client.post(url)
		self.client.post(url)
		self.assertEqual(Application.objects.filter(student=self.user, opportunity=self.opportunity).count(), 1)

	def test_student_can_update_application_status_date_and_notes(self):
		application = Application.objects.create(student=self.user, opportunity=self.opportunity)
		self.client.force_login(self.user)
		response = self.client.post(reverse("update_application", args=[application.pk]), {
			"status": Application.Status.INTERVIEW,
			"date_applied": "2026-10-01",
			"notes": "Prepare system design examples.",
			"next": "tracker",
		})
		self.assertRedirects(response, reverse("tracker"))
		application.refresh_from_db()
		self.assertEqual(application.status, Application.Status.INTERVIEW)
		self.assertEqual(application.date_applied.isoformat(), "2026-10-01")
		self.assertEqual(application.notes, "Prepare system design examples.")

	def test_invalid_status_update_keeps_data_and_shows_error(self):
		application = Application.objects.create(student=self.user, opportunity=self.opportunity)
		self.client.force_login(self.user)
		response = self.client.post(reverse("update_application", args=[application.pk]), {
			"status": "not-a-status", "date_applied": "", "notes": "", "next": "tracker",
		}, follow=True)
		application.refresh_from_db()
		self.assertEqual(application.status, Application.Status.INTERESTED)
		self.assertContains(response, "Update not saved")

	def test_student_cannot_update_another_students_application(self):
		application = Application.objects.create(student=self.other_user, opportunity=self.opportunity)
		self.client.force_login(self.user)
		response = self.client.post(reverse("update_application", args=[application.pk]), {
			"status": Application.Status.SELECTED,
			"date_applied": "",
			"notes": "Changed by another account",
		})
		self.assertEqual(response.status_code, 404)
		application.refresh_from_db()
		self.assertEqual(application.status, Application.Status.INTERESTED)

	def test_save_action_toggles_saved_opportunity(self):
		self.client.force_login(self.user)
		url = reverse("toggle_saved", args=[self.opportunity.pk])
		self.client.post(url, {"next": "opportunity_detail"})
		self.assertTrue(SavedOpportunity.objects.filter(student=self.user, opportunity=self.opportunity).exists())
		self.client.post(url, {"next": "opportunity_detail"})
		self.assertFalse(SavedOpportunity.objects.filter(student=self.user, opportunity=self.opportunity).exists())

	def test_dashboard_and_tracker_render_application(self):
		Application.objects.create(student=self.user, opportunity=self.opportunity)
		self.client.force_login(self.user)
		self.assertContains(self.client.get(reverse("dashboard")), "Product Engineering Intern")
		self.assertContains(self.client.get(reverse("tracker")), "Personal notes")

	def test_dashboard_and_private_lists_only_include_current_students_records(self):
		Application.objects.create(student=self.user, opportunity=self.opportunity)
		private_opportunity = Opportunity.objects.create(
			title="Private student listing",
			organization="Other Org",
			opportunity_type=Opportunity.Type.EVENT,
			description="Only associated with another student's records.",
		)
		Application.objects.create(student=self.other_user, opportunity=private_opportunity)
		SavedOpportunity.objects.create(student=self.other_user, opportunity=private_opportunity)
		self.client.force_login(self.user)
		for url_name in ("dashboard", "tracker", "saved_opportunities"):
			response = self.client.get(reverse(url_name))
			self.assertNotContains(response, "Private student listing")
		self.assertContains(self.client.get(reverse("dashboard")), "Product Engineering Intern")

	def test_saved_opportunities_appear_on_own_dashboard_only(self):
		self.opportunity.deadline = date.today() + timedelta(days=8)
		self.opportunity.save(update_fields=["deadline"])
		SavedOpportunity.objects.create(student=self.user, opportunity=self.opportunity)
		self.client.force_login(self.user)
		response = self.client.get(reverse("dashboard"))
		self.assertContains(response, "Worth another look.")
		self.assertContains(response, "Product Engineering Intern")
		self.assertEqual(response.context["saved_count"], 1)
		self.assertIn(self.opportunity, response.context["upcoming"])

	def test_dashboard_counts_and_deadlines_are_personalized(self):
		self.opportunity.deadline = date.today() + timedelta(days=10)
		self.opportunity.save(update_fields=["deadline"])
		Application.objects.create(student=self.user, opportunity=self.opportunity, status=Application.Status.APPLIED)
		other_opportunity = Opportunity.objects.create(
			title="Another student's deadline",
			organization="Other Org",
			opportunity_type=Opportunity.Type.INTERNSHIP,
			description="Private opportunity.",
			deadline=date.today() + timedelta(days=5),
		)
		Application.objects.create(student=self.other_user, opportunity=other_opportunity)
		self.client.force_login(self.user)
		response = self.client.get(reverse("dashboard"))
		self.assertEqual(response.context["counts"][Application.Status.APPLIED], 1)
		self.assertEqual(list(response.context["upcoming"]), [self.opportunity])
		self.assertContains(response, "Product Engineering Intern")
		self.assertNotContains(response, "Another student's deadline")
