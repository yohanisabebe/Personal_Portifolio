from django.views.generic.base import TemplateView
from .models import Personal, About, Experience, Description, Education, Technology, Portfolio
from .forms import ContactForm
import cloudinary.uploader
from django.core.mail import send_mail
from django.conf import settings # Import settings to access email configuration
from django.shortcuts import render # Keep render if you need to render error pages/messages
from django.http import JsonResponse
# from django.shortcuts import render # Already imported above, remove duplicate
from operator import attrgetter
from django.db.models import Q
# from django.http import JsonResponse # Already imported above, remove duplicate

class HomePageView(TemplateView):
    template_name = 'portfolio/portfolio_main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['personal'] = Personal.objects.all()
        context['about'] = About.objects.all()
        context['technologies'] = Technology.objects.all()
        context['portfolio'] = Portfolio.objects.all()
        context['contact_form'] = ContactForm()
        # Pass the reCAPTCHA public key to the template for JS
        context['RECAPTCHA_PUBLIC_KEY'] = settings.RECAPTCHA_PUBLIC_KEY 
        
        # message_sent is now handled client-side via JsonResponse, 
        # so this specific context variable might not be needed for initial render.
        # context['message_sent'] = False 
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            your_name = form.cleaned_data['your_name']
            your_email = form.cleaned_data['your_email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Build the email body
            email_body = f"Name: {your_name}\nEmail: {your_email}\nSubject: {subject}\n\n{message}"
            
            # Define recipient and sender for the email
            # This is the email address that will receive the form submission
            recipient_email = 'yohaniabebe@gmail.com' 
            
            # The 'from_email' should be your configured sending email (e.g., from settings.py)
            # This is important for SMTP server validation and deliverability.
            # The 'reply_to' allows you to reply directly to the user's email.
            from_email_address = settings.DEFAULT_FROM_EMAIL # Or settings.EMAIL_HOST_USER
            reply_to_address = [your_email] # List for 'reply-to' header

            try:
                send_mail(
                    subject=f"New Contact Form Submission: {subject}", # Subject line you'll see
                    message=email_body, # The content of the email
                    from_email=from_email_address, # The sender (your configured email)
                    recipient_list=[recipient_email], # The actual recipient (yohaniabebe@gmail.com)
                    fail_silently=False, # Crucial for debugging - raises exceptions on failure
                    reply_to=reply_to_address, # Sets the reply-to header to the user's email
                )
                # If email sends successfully, return success JSON response
                return JsonResponse({'status': 'success', 'message': 'Your message has been sent. Thank you!'})
            except Exception as e:
                # If sending email fails, return error JSON response and log the error
                print(f"Error sending email: {e}") # Log the error to your console/logs
                return JsonResponse({'status': 'error', 'message': 'There was an error sending your message. Please try again later.'}, status=500) # 500 for server error
        else:
            # Form is not valid (e.g., validation errors, reCAPTCHA failed)
            # You can extract specific error messages
            errors = {field: form.errors[field][0] for field in form.errors}
            # For reCAPTCHA specific errors, you might want to check form.errors.get('captcha')
            
            print(f"Form errors: {form.errors}") # Log form errors for debugging
            return JsonResponse({'status': 'error', 'errors': errors, 'message': 'Please correct the errors in the form.'}, status=400) # 400 for bad request

class DigitalCVPageView(TemplateView):
    template_name = 'portfolio/digital_cv.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiences = Experience.objects.all()

        for experience in experiences:
            # Using set() on a related manager (like descriptions) usually needs to be careful
            # if 'descriptions' is a ManyToManyField or a reverse ForeignKey relationship.
            # If Description has a ForeignKey to Experience:
            experience.descriptions.set(Description.objects.filter(experience=experience).order_by('order_number'))            # If descriptions is a ManyToMany, it would be different.
            # Assuming it's a related_name/reverse foreign key, accessing it directly works.
            # No .set() needed unless you're trying to re-assign relations.

        context['experiences'] = experiences
        context['personal'] = Personal.objects.all()
        context['education'] = Education.objects.all()
        context['technologies'] = Technology.objects.all()
        context['portfolio'] = Portfolio.objects.filter(
            Q(filter='filter-certification')
        )
        
        grouped_portfolio = {}
        # Ensure 'portfolio' is a list before sorting if it's a QuerySet that might be consumed
        # If it's a QuerySet, sorting directly like this is fine:
        portfolios = context['portfolio'].order_by('-year') # Sort QuerySet directly
        
        for item in portfolios:
            issuer_name = item.issuer.name if item.issuer else "Unknown Issuer"
            if issuer_name not in grouped_portfolio:
                grouped_portfolio[issuer_name] = []
            grouped_portfolio[issuer_name].append(item)

        context['grouped_portfolio'] = grouped_portfolio

        return context
    
def handle_not_found(request, exception):
    return render(request, "layouts/page-404.html", status=404) # Set status code for 404
def upload_from_path(request):
    if request.method == 'POST':
        file_path = '/path/to/your/image.jpg' # Or get it from request.FILES
        result = cloudinary.uploader.upload(file_path, folder="my_django_uploads")
        # result will contain information about the uploaded file,
        # including its secure_url, public_id, etc.
        print(result['secure_url'])
        # You can then save this URL or public_id to your model
    # ...

def upload_from_django_file(request):
    if request.method == 'POST' and request.FILES.get('my_image_field'):
        uploaded_file = request.FILES['my_image_field']
        result = cloudinary.uploader.upload(uploaded_file, folder="user_uploads")
        print(result['secure_url'])