from django.db import models
from django.db.models import fields
from rest_framework import serializers
from club_bethani.models import Reader, Book, Borrow, BorrowHistory
from django.contrib.auth.models import User


# Reader cannot activate his own account
class ReaderSerializer(serializers.ModelSerializer):
    # read_only eans that the field will be included in the APIs output but won't be included during Create or Update operations on the endpoint
    # . To populate this field, we'll create a method to automatically fill the field with the request user.
    
    class Meta:
        model = Reader
        fields ="__all__"
    
    

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


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


'''

     def update(self, instance, validated_data):
        instance.firstname = validated_data.get('firstname', instance.firstname)
        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.gender = validated_data.get('gender', instance.gender)
        return instance
'''
