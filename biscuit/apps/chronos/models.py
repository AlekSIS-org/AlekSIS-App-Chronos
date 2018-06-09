from django.db import models


# Create your models here.

# class Teacher(models.Model):
#     shortcode = models.CharField(max_length=10)
#     first_name = models.CharField(max_length=100)
#     name = models.CharField(max_length=100)
#
#
# class Room(models.Model):
#     shortcode = models.CharField(max_length=10)
#     name = models.CharField(max_length=100)
#
#
# class Class(models.Model):
#     name = models.CharField(max_length=10)
#     text1 = models.CharField(max_length=200)
#     text2 = models.CharField(max_length=200)
#     room = models.ForeignKey(Room, on_delete=models.CASCADE)
