from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ApplicationForm, RegistrationForm, StudentProfileForm
from .models import Application, Opportunity, SavedOpportunity, StudentProfile


def opportunity_list(request):
    opportunities = Opportunity.objects.filter(is_active=True)
    search = request.GET.get("q", "").strip()
    opportunity_type = request.GET.get("type", "")
    location = request.GET.get("location", "")
    location_query = request.GET.get("place", "").strip()
    sort = request.GET.get("sort", "newest")
    if search:
        opportunities = opportunities.filter(
            Q(title__icontains=search)
            | Q(organization__icontains=search)
            | Q(required_skills__icontains=search)
        )
    if opportunity_type:
        opportunities = opportunities.filter(opportunity_type=opportunity_type)
    if location == "remote":
        opportunities = opportunities.filter(is_remote=True)
    elif location == "onsite":
        opportunities = opportunities.filter(is_remote=False)
    if location_query:
        opportunities = opportunities.filter(location__icontains=location_query)
    if sort == "deadline":
        opportunities = opportunities.order_by(F("deadline").asc(nulls_last=True), "-created_at")

    page = Paginator(opportunities, 9).get_page(request.GET.get("page"))
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(
            SavedOpportunity.objects.filter(student=request.user, opportunity__in=page.object_list)
            .values_list("opportunity_id", flat=True)
        )
    return render(request, "opportunities/opportunity_list.html", {
        "page": page,
        "opportunities": page.object_list,
        "saved_ids": saved_ids,
        "search": search,
        "selected_type": opportunity_type,
        "selected_location": location,
        "location_query": location_query,
        "sort": sort,
        "types": Opportunity.Type.choices,
    })


def opportunity_detail(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_active=True)
    application = None
    is_saved = False
    if request.user.is_authenticated:
        application = Application.objects.filter(student=request.user, opportunity=opportunity).first()
        is_saved = SavedOpportunity.objects.filter(student=request.user, opportunity=opportunity).exists()
    return render(request, "opportunities/opportunity_detail.html", {
        "opportunity": opportunity,
        "application": application,
        "is_saved": is_saved,
        "application_form": ApplicationForm(instance=application),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        StudentProfile.objects.create(user=user)
        login(request, user)
        messages.success(request, "Your account is ready. Let’s find your next opportunity.")
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    applications = Application.objects.filter(student=request.user).select_related("opportunity")
    status_counts = applications.values("status").annotate(total=Count("id"))
    counts = {status: 0 for status, _label in Application.Status.choices}
    counts.update({row["status"]: row["total"] for row in status_counts})
    deadline_limit = timezone.localdate() + timedelta(days=21)
    related_opportunities = Opportunity.objects.filter(
        Q(saved_by__student=request.user) | Q(applications__student=request.user),
        is_active=True,
        deadline__gte=timezone.localdate(),
        deadline__lte=deadline_limit,
    ).distinct().order_by("deadline")[:5]
    recent = applications.order_by("-updated_at")[:5]
    saved_opportunities = Opportunity.objects.filter(
        saved_by__student=request.user, is_active=True
    ).order_by("-saved_by__saved_at")[:4]
    return render(request, "opportunities/dashboard.html", {
        "applications": applications,
        "recent_applications": recent,
        "upcoming": related_opportunities,
        "saved_opportunities": saved_opportunities,
        "counts": counts,
        "total_applications": applications.count(),
        "saved_count": SavedOpportunity.objects.filter(student=request.user).count(),
        "chart_labels": [label for _value, label in Application.Status.choices],
        "chart_values": [counts[value] for value, _label in Application.Status.choices],
    })


@login_required
def tracker(request):
    applications = Application.objects.filter(student=request.user).select_related("opportunity")
    return render(request, "opportunities/tracker.html", {
        "applications": applications,
        "status_choices": Application.Status.choices,
    })


@login_required
def update_application(request, pk):
    application = get_object_or_404(Application, pk=pk, student=request.user)
    if request.method == "POST":
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, "Application progress updated.")
        else:
            errors = " ".join(
                f"{field}: {', '.join(messages_for_field)}"
                for field, messages_for_field in form.errors.items()
            )
            messages.error(request, f"Update not saved. {errors}")
    destination = request.POST.get("next")
    return redirect("dashboard" if destination == "dashboard" else "tracker")


@login_required
def add_application(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_active=True)
    if request.method == "POST":
        application, created = Application.objects.get_or_create(
            student=request.user,
            opportunity=opportunity,
            defaults={"status": Application.Status.INTERESTED},
        )
        if created:
            messages.success(request, "Added to your application tracker.")
        else:
            messages.info(request, "This opportunity is already in your tracker.")
    return redirect("opportunity_detail", pk=opportunity.pk)


@login_required
def toggle_saved(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, is_active=True)
    if request.method == "POST":
        saved, created = SavedOpportunity.objects.get_or_create(student=request.user, opportunity=opportunity)
        if not created:
            saved.delete()
            messages.info(request, "Removed from your saved opportunities.")
        else:
            messages.success(request, "Saved for later.")
    destination = request.POST.get("next")
    if destination == "opportunity_detail":
        return redirect("opportunity_detail", pk=pk)
    if destination == "saved_opportunities":
        return redirect("saved_opportunities")
    return redirect("opportunity_list")


@login_required
def saved_opportunities(request):
    saved = SavedOpportunity.objects.filter(student=request.user).select_related("opportunity")
    return render(request, "opportunities/saved.html", {"saved_opportunities": saved})


@login_required
def profile(request):
    student_profile, _created = StudentProfile.objects.get_or_create(user=request.user)
    form = StudentProfileForm(request.POST or None, instance=student_profile, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")
    return render(request, "opportunities/profile.html", {"form": form})
