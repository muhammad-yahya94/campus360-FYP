from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Payment
from admissions.models import Applicant
import stripe
import logging
from django.db.models import Q


# Configure logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def payment_form(request):
    logger.info("Rendering payment form")
    if request.user.is_authenticated:
        # Get Applicants where Payment is either not created or status is not 'paid'
        applicants = Applicant.objects.filter(
            user=request.user
        ).filter(
            Q(payment__isnull=True) | ~Q(payment__status='paid')
        ).distinct()
    else:
        applicants = []
    return render(request, "payment_form.html", {'applicants': applicants})

@csrf_exempt
def stripe_config(request):
    if request.method == "GET":
        logger.info("Stripe config requested")
        stripe_config = {"publicKey": settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=True)
    logger.warning(f"Invalid method {request.method} for stripe_config")
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def create_checkout_session(request):
    if request.method == "POST":
        try:
            logger.info("Received POST request to create checkout session")
            price_id = request.POST.get("price_id")
            applicant_id = request.POST.get("applicant_id")

            if not price_id:
                logger.error("Price ID is required")
                return JsonResponse({"error": "Price ID is required"}, status=400)
            if not applicant_id:
                logger.error("Applicant ID is required")
                return JsonResponse({"error": "Applicant ID is required"}, status=400)

            logger.info(f"Price ID received: {price_id}, Applicant ID: {applicant_id}")
            # Verify price_id exists
            price = stripe.Price.retrieve(price_id)
            logger.info(f"Price retrieved: {price.unit_amount} {price.currency}")
            amount = price.unit_amount

            logger.info("Creating Stripe checkout session")
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=str(request.user.id) if request.user.is_authenticated else None,
                success_url=settings.PAYMENT_SUCCESS_URL,
                cancel_url=settings.PAYMENT_CANCEL_URL,
                payment_method_types=["card"],
                mode="payment",
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ]
            )
            logger.info(f"Checkout session created: {checkout_session['id']}")

            # Get the specific Applicant for the payment
            if request.user.is_authenticated:
                logger.info(f"Checking Applicant {applicant_id} for user {request.user.id}")
                applicant = Applicant.objects.get(id=applicant_id, user=request.user)
                logger.info(f"Creating Payment record for Applicant {applicant.id}")
                Payment.objects.create(
                    user=applicant,
                    stripe_session_id=checkout_session["id"],
                    amount=amount / 100,  # Convert cents to PKR
                    status="pending"
                )
                logger.info("Payment record created successfully")
            else:
                logger.info("User not authenticated, skipping Payment record creation")

            return JsonResponse({"sessionId": checkout_session["id"]})
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Stripe InvalidRequestError: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=500)
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe AuthenticationError: {str(e)}", exc_info=True)
            return JsonResponse({"error": "Invalid Stripe API key"}, status=500)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}", exc_info=True)
            return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=500)
        except Applicant.DoesNotExist:
            logger.error(f"Applicant with ID {applicant_id} not found for user {request.user.id}")
            return JsonResponse({"error": "Invalid applicant selection"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in create_checkout_session: {str(e)}", exc_info=True)
            return JsonResponse({"error": "An unexpected error occurred"}, status=500)
    else:
        logger.warning(f"Received invalid {request.method} request from {request.META.get('REMOTE_ADDR')}")
        return JsonResponse({"error": "This endpoint only accepts POST requests"}, status=405)

@login_required
def success(request):
    session_id = request.GET.get("session_id", "")
    logger.info(f"Success page accessed with session_id: {session_id}")
    context = {"session_id": session_id}
    return render(request, "success.html", context)

@login_required
def cancel(request):
    session_id = request.GET.get("session_id", "")
    logger.info(f"Cancel page accessed with session_id: {session_id}")
    context = {"session_id": session_id}
    return render(request, "cancel.html", context)

@csrf_exempt
def stripe_webhook(request):
    logger.info("Webhook request received")
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info(f"Webhook event received: {event['type']}")
    except ValueError:
        logger.error("Invalid webhook payload")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session["payment_status"] == "paid":
            try:
                payment = Payment.objects.get(stripe_session_id=session["id"])
                payment.stripe_payment_intent = session["payment_intent"]
                payment.status = "paid"
                payment.save()
                logger.info(f"Payment {session['id']} marked as paid")
            except Payment.DoesNotExist:
                logger.warning(f"Payment record not found for session {session['id']}")
                pass

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        try:
            payment = Payment.objects.get(stripe_session_id=session["id"])
            payment.status = "failed"
            payment.save()
            logger.info(f"Payment {session['id']} marked as failed")
        except Payment.DoesNotExist:
            logger.warning(f"Payment record not found for session {session['id']}")
            pass

    else:
        logger.info(f"Unhandled webhook event: {event['type']}")

    return JsonResponse({"status": "success"}, status=200)