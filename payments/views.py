from django.http import HttpResponse

def checkout(request):
    return HttpResponse("Hier kommt später das Stripe-Bezahlformular.")
