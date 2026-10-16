from django.conf import settings
from django.db import models
from django.utils import timezone


class StudentProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
	college = models.CharField(max_length=180, blank=True)
	graduation_year = models.PositiveSmallIntegerField(null=True, blank=True)
	skills = models.TextField(blank=True, help_text="Separate skills with commas")
	bio = models.TextField(blank=True)

	def __str__(self):
		return f"Profile: {self.user.username}"


class Opportunity(models.Model):
	class Type(models.TextChoices):
		INTERNSHIP = "internship", "Internship"
		HACKATHON = "hackathon", "Hackathon"
		WORKSHOP = "workshop", "Workshop"
		EVENT = "event", "Technical event"

	title = models.CharField(max_length=200)
	organization = models.CharField(max_length=180)
	opportunity_type = models.CharField(max_length=20, choices=Type.choices)
	description = models.TextField()
	required_skills = models.CharField(max_length=300, blank=True, help_text="Comma-separated skills")
	location = models.CharField(max_length=140, blank=True)
	is_remote = models.BooleanField(default=False)
	deadline = models.DateField(null=True, blank=True)
	application_url = models.URLField(blank=True)
	logo_url = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self):
		return self.title

	@property
	def is_expired(self):
		return bool(self.deadline and self.deadline < timezone.localdate())


class SavedOpportunity(models.Model):
	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_opportunities")
	opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="saved_by")
	saved_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["student", "opportunity"], name="unique_saved_opportunity")]
		ordering = ["-saved_at"]

	def __str__(self):
		return f"{self.student} saved {self.opportunity}"


class Application(models.Model):
	class Status(models.TextChoices):
		INTERESTED = "interested", "Interested"
		APPLIED = "applied", "Applied"
		INTERVIEW = "interview", "Interview"
		SELECTED = "selected", "Selected"
		REJECTED = "rejected", "Rejected"

	student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
	opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="applications")
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.INTERESTED)
	date_applied = models.DateField(null=True, blank=True)
	notes = models.TextField(blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=["student", "opportunity"], name="unique_student_application")]
		ordering = ["-updated_at"]

	def __str__(self):
		return f"{self.student} · {self.opportunity}"
