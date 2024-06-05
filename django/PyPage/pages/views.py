from django.shortcuts import render
from django.db.models import Q
from .functions import make_str
from pages.models import Project


def home(request):
    projects = Project.objects.filter(
        Q(id__range=(1, 5)) |
        Q(id__range=(1, 1)) |
        Q(id__range=(6, 6)) |
        Q(id__range=(27, 28)) |
        Q(id__range=(7, 7)) |
        Q(id__range=(49, 50)) |
        Q(id__range=(8, 8)) |
        Q(id__range=(38, 39)) |
        Q(id__range=(9, 9)) |
        Q(id__range=(16, 17)) |
        Q(id__range=(10, 13))
    )

    return render(request, "PyPage/home.html", {'posts': projects})


def ach(request):
    projects = Project.objects.filter(
        Q(id__range=(1, 1)) |
        Q(id__range=(6, 6)) |
        Q(id__range=(27, 28)) |
        Q(id__range=(7, 7)) |
        Q(id__range=(49, 50)) |
        Q(id__range=(8, 8)) |
        Q(id__range=(38, 39)) |
        Q(id__range=(9, 9)) |
        Q(id__range=(16, 17))
    )

    return render(request, "PyPage/ach.html", {'posts': projects})


def ach1(request):
    projects = Project.objects.filter(
        Q(id__range=(15, 15)) |
        Q(id__range=(9, 9)) |
        Q(id__range=(16, 25))
    )

    return render(request, "PyPage/ach1.html", {'posts': projects})


def ach2(request):
    projects = Project.objects.filter(
        Q(id__range=(26, 26)) |
        Q(id__range=(6, 6)) |
        Q(id__range=(27, 36))
    )

    return render(request, "PyPage/ach2.html", {'posts': projects})


def ach3(request):
    projects = Project.objects.filter(
        Q(id__range=(37, 37)) |
        Q(id__range=(8, 8)) |
        Q(id__range=(38, 47))
    )

    return render(request, "PyPage/ach3.html", {'posts': projects})


def ach4(request):
    projects = Project.objects.filter(
        Q(id__range=(48, 48)) |
        Q(id__range=(7, 7)) |
        Q(id__range=(49, 58))
    )

    return render(request, "PyPage/ach4.html", {'posts': projects})
