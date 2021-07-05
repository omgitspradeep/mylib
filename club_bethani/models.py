from os import name
from django.db import models
from django.core.validators import RegexValidator
from datetime import datetime, timedelta
from django.contrib.auth.models import Group
from django.db.models.lookups import LessThan
from django.core.validators import MaxValueValidator, MinValueValidator 
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.conf import  settings
from django.contrib.auth.models import User

# Create your models here.

User._meta.get_field('email')._unique = True

class Reader(models.Model):
    
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    PROFESSION=(
        ('A','Agriculture'),
        ('T','Teacher'),
        ('S','Student'),
        ('B','Business'),
        ('E','Employee'),
    )

    # we won't user firstname, lastname, email of "User" because it makes difficult for updating.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=15)
    lastname = models.CharField(max_length=15)
    gender = models.CharField(max_length=7, choices = GENDER)
    address = models.CharField(max_length=45)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True) # validators should be a list
    email = models.EmailField(max_length=100, blank= True)
    house_no = models.PositiveIntegerField()
    profession = models.CharField(max_length=15, choices=PROFESSION)
    profile_pic = models.ImageField(upload_to='images/bethani/profiles/', null=True, blank= True)
    account_activated = models.BooleanField(default=False)
    books_borrowed = models.PositiveIntegerField(default=0)

    def full_name(self):
        return self.firstname+" "+self.lastname

    def full_address(self):
        return self.address+", House No. "+str(self.house_no)

    def __str__(self):
        return self.full_name()

    def books_shared(self):
        try:
            return Book.objects.filter(reader=self).count()
        except:
            return 0
    



class Book(models.Model):

    BOOK_STATUS = (
        ('A', 'Available'),
        ('U', 'Unavailable'),
    )
    LANGUAGE_CHOICES=(
        ('N', 'Nepali'),
        ('E', 'English'),
        ('S', 'Sanskrit'),
        ('T', 'Tharu'),
        ('H', 'Hindi'),
        ('Ne','Newari'),
        ('O', 'Others')
    )

    reader = models.ForeignKey(Reader, on_delete=models.SET_NULL, related_name='Reader', null=True)
    author = models.CharField(max_length=45, null=True)
    name = models.CharField(max_length=50,null=True)
    image = models.ImageField(upload_to='images/bethani/', null=True, blank= True)
    description= models.TextField(max_length=250, null=True)
    available_status = models.BooleanField(default=True)  # Book could be unavailable beacause: 1) Borrowed 2) Reader doesn't want to share for now.
    borrow_count = models.PositiveIntegerField(default=0)  
    upload_date = models.DateTimeField(auto_now=False,auto_now_add=True)
    language = models.CharField(max_length=10,choices=LANGUAGE_CHOICES,default='N')

    def __str__(self):
        return self.name
    
    def is_owner_active(self):
        return self.reader.account_activated


    
class Borrow(models.Model):
    borrower = models.ForeignKey(Reader, on_delete=models.SET_NULL, related_name='book_borrower', null=True)
    book_borrowed = models.OneToOneField(Book, on_delete=models.SET_NULL, related_name='book_borroweed', null=True)
    request_date = models.DateTimeField(auto_now=False,auto_now_add=True)
    borrow_accept= models.BooleanField(default=False)
    book_received_by_borrower= models.BooleanField(default=False)
    borrow_accept_date = models.DateTimeField(auto_now=False,auto_now_add=True)
    note= models.TextField(max_length=250, null=True)
    returned = models.BooleanField(default=False)  # False means 1) Book's available_status is False
    

    # To display the latest list of borrows at top
    class Meta:
        ordering=['-request_date']

    def __str__(self):
        return self.borrower.full_name()+" borrows " +self.book_borrowed.name
    
    def remaining_days(self):
        
        if self.borrow_accept:
            time_of_borrow = self.borrow_accept_date.date()  # gives us datetime format
            time_of_return = time_of_borrow + timedelta(days=5,hours=0,minutes=0)
            remaining_days = time_of_return - time_of_borrow
            return remaining_days
        else:
            return "-"
    
    def accepted_time(self):
        if self.borrow_accept:
            return self.borrow_accept_date
        else:
            return "-"


# This helps owner of book to know whether the borrower is trustworthy before giving his book.
# This data is created when the owner of book receives the book back from borrower.

class BorrowHistory(models.Model):
    borrower = models.ForeignKey(Reader, on_delete=models.SET_NULL, related_name='book_borrower_hist', null=True)
    book_borrowed = models.ForeignKey(Book, on_delete=models.SET_NULL, related_name='book_borrowed_hist', null=True)
    borrow_accept_date = models.CharField(max_length=60, default="-")
    social_score= models.IntegerField(default=0, validators=[MinValueValidator(-5), MaxValueValidator(5)]) # Number ranging from -5 to +5
    returned_date = models.DateField(auto_now=False,auto_now_add=True)
    borrower_note= models.TextField(max_length=250, null=True)
    owner_comment = models.TextField(max_length=250, null=True) # About borrower by owner of book

    #book,borrower, borrow_date, returned_date,note, 
    def __str__(self):
        return self.borrower.full_name()+"  read  a book : " +self.book_borrowed.name
    
    def book_owner(self):
        return self.book_borrowed.reader




'''
Note:

    Club admin doesn't have right to add/change/delete Borrow but can view.
    Reader only have right to borrow and provide books.
    All borrow records will remain undeleted to keep track of borrow history.
    Only two books can be borrowed by a Reader/Borrower at a time.


'''



'''
PROBLEMS:

1. To make book status as "Available" when book is returned
    Status: Pending
    Issue: Front + back
    Solution: 

2. To make book status as "Unavailable" when book is borrowed
    Status: Pending
    Issue: Front + back
    Solution: When book is borrowed first mak

3. When return date (which is atmost 7days) arrives but book is not returned then highlight that item.
    Status: Pending
    Solution: 

4. Delete the old picture when new is uploaded.  
   Status: Done
   Solution: install app 'django_cleanup.apps.CleanupConfig' in settings.py after all the apps.
   
'''
