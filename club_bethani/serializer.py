from django.db import models
from django.db.models import fields
from rest_framework import serializers
from club_bethani.models import Reader, Book, Borrow, BorrowHistory

# Reader cannot activate his own account
class ReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reader
        fields =("id","firstname","lastname","username","password","gender","address","phone_number","email","house_no","profession","profile_pic")

# Owner of books should not be able to update borrow_count for his book.
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields ='__all__'     
        #fields =("reader","author","name","image","description","available_status","upload_date","language")

class BorrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrow
        fields ='__all__'


class BorrowHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowHistory
        fields ='__all__'
