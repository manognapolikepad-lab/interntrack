from django.contrib import admin
from .models import Application, Opportunity, SavedOpportunity, StudentProfile


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
	list_display = ("title", "organization", "opportunity_type", "deadline", "is_active")
	list_filter = ("opportunity_type", "is_active", "is_remote")
	search_fields = ("title", "organization", "required_skills")
	date_hierarchy = "created_at"
	list_editable = ("is_active",)
	readonly_fields = ("created_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
	list_display = ("student", "opportunity", "status", "date_applied", "updated_at")
	list_filter = ("status",)
	search_fields = ("student__username", "opportunity__title", "opportunity__organization")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "college", "graduation_year")
	search_fields = ("user__username", "user__email", "college")


@admin.register(SavedOpportunity)
class SavedOpportunityAdmin(admin.ModelAdmin):
	list_display = ("student", "opportunity", "saved_at")
	search_fields = ("student__username", "opportunity__title")
