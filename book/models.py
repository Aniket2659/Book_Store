from django.db import models
from user.models import User

class Book(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    author = models.CharField(max_length=255, db_index=True)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books', db_index=True)
    price = models.PositiveIntegerField(null=False)
    stock = models.PositiveIntegerField(null=False) 

    class Meta:
        db_table="book"

    def __str__(self):
        return self.name