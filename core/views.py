from django.shortcuts import render , redirect



def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def gallery(request):
    return render(request, 'gallery.html')

def events(request):
    return render(request, 'all-news-events.html')

def team(request):
    return render(request, 'team.html')

def testimonial(request):
    return render(request, 'testimonial.html')

def contact(request):
    return render(request, 'contact.html')

def admission(request):
    return render(request, 'admission.html')
