from django.db import models

# Create your models here.

class Product(models.Model): 
    audio = models.FileField(upload_to='audios/',null=True),
    uploaded_at=models.DateTimeField(auto_now_add=True)
     