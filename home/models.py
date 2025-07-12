from django.db import models

# Create your models here.

class Product(models.Model): 
    audio = models.FileField(upload_to='audio/',null=True),
    uploaded_at=models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name 
    