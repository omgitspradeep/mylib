from django.db.models import manager
from django.db import IntegrityError

from django.http import response
from django.shortcuts import render
from django.urls import base, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q

from datetime import datetime
from requests import api

from rest_framework import status
from rest_framework import pagination
from rest_framework.views import APIView

from club_bethani.serializer import ReaderSerializer, BookSerializer, BorrowSerializer, BorrowHistorySerializer, UserSerializer
from club_bethani.models import Reader, Book, Borrow, BorrowHistory
from club_bethani import serializer
from mylib.mypaginations import MyPageNumberPagination


from rest_framework.generics import ListAPIView
from rest_framework.pagination import BasePagination, PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from django.core.mail import send_mail
from django.conf import settings
import requests


# Create your views here.



#This gives paginated output only when user provides token
# Offers only GET and POST operations on Book (1. UPload new book 2. Get Paginated books)
class BookModelViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser]
    queryset = Book.objects.filter(reader__account_activated='True').order_by('-id')
    serializer_class = BookSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    
    
@api_view(['POST'])
@csrf_exempt
def login(request):

    # 1. Validate 
    uname = request.POST['username']
    passwrd = request.POST['password']
    if uname is None or passwrd is None:
        return JsonResponse({'detail': 'Please enter Credentials!'},status=HTTP_400_BAD_REQUEST)
    #print(uname+" "+passwrd)
    try:    
        if '@' in uname:
            kwargs = {'email': uname}
            usr = get_user_model().objects.get(**kwargs)
            if not usr.check_password(passwrd):
                return JsonResponse({'detail': 'Wrong Credentials!'},status=HTTP_400_BAD_REQUEST)
        else:
            # You cannot use password to get user object directly. Therefore, use authenticate.
            usr = authenticate(username= uname, password=passwrd)
            if usr is None:
                return JsonResponse({'detail': 'Wrong Credentials!'},status=HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return JsonResponse({'detail': 'User does not exists!'},status=HTTP_400_BAD_REQUEST)
    

    # 2. Get userProfile
    person = Reader.objects.get(user = usr.id)
    #3. Check if Reader's account is activated 
    if person.account_activated: 
        reader_seri = ReaderSerializer(person)
        #print(reader_seri.data.items)
    
        # 4. Get allBooks (with pagination)
        try:
            books = requests.get("http://"+request.get_host()+reverse('allbookspag'))
            all_books = "not avl"
            if books.status_code == 200:
                all_books = books.json() 
        except:
            all_books ="Fail"
        # 5. Get JWT Tokens
        refresh  = RefreshToken.for_user(usr)
        token_data = {
            "refresh" : str(refresh),
            "token": str(refresh.access_token)
        }

        #6. Get MyBooks 
        '''
        try:
            mybooks= requests.get("http://"+request.get_host()+reverse('mybooks',args=(person.id,)))
            my_all_books="not_avl"
            if mybooks.status_code == 200:
                my_all_books = mybooks.json()

        except:
            return JsonResponse({"detail": "Something went wrong while fetching your books!"},status=HTTP_404_NOT_FOUND)
        '''
        #7. Get MyEvents
        events =getBorrows(person.id)


        return JsonResponse({
            "jwtToken":token_data,
            "profile":reader_seri.data,
            "books":all_books,
            "myevents":events
        }, status=HTTP_200_OK)

    else:
        return JsonResponse({"detail": "Account not activated.!"},status=HTTP_404_NOT_FOUND)


# It is called from login
# It get books of only users whose account is activated
# Offer only GET operation on book for view functions
class AllbooksPagination(ListAPIView):
    queryset = Book.objects.filter(reader__account_activated='True').order_by('-id')
    serializer_class = BookSerializer


@api_view(['POST'])
@csrf_exempt
def signUpNewUser(request):
    # Validate all fields before creating new user.
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    gender = request.data.get('gender')
    address = request.data.get('address')
    phone_number = request.data.get('phone_number')
    email = request.data.get('email')
    house_no = request.data.get('house_no')
    profession = request.data.get('profession')

    usrname= request.data.get('username')                   

    user = UserSerializer(data=request.data)

    if user.is_valid():
        user.save()
        # Getting just created User object
        myuser= User.objects.get(username=usrname)
        # Making recently created User as new Reader 
        Reader.objects.create(user=myuser,firstname=first_name,lastname=last_name,gender=gender,address=address,phone_number=phone_number,email=email,house_no=house_no,profession=profession)
        #rs = ReaderSerializer(student)
        return JsonResponse({"detail":"User successfully created. Wait for Admin approval."},status=HTTP_200_OK)
    else:
        return JsonResponse({"detail":"Username / Email already taken. Try another"},safe=False)


# no POST method: We cannot only create reader during signup.

@csrf_exempt
@api_view(["GET","PUT","DELETE"])
#@permission_classes((IsAuthenticated, ))
#@authentication_classes((JWTAuthentication,))
def readerApi(request,id=0):
    if request.method == 'GET':
        # API: http://127.0.0.1:8000/bbc/api/getReader/4
        reader= Reader.objects.filter(pk=id,account_activated=True).first()
        if reader:
            readers_serializer = ReaderSerializer(reader)
            return Response(readers_serializer.data, status=HTTP_200_OK)
        else:
            return Response({"detail":"Account is deactivate or does not exits"}, status=HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        # API: http://127.0.0.1:8000/bbc/api/getReader/   Body: json data without image because image is sent as string for now
        readerId= request.data.get('id')
        userId  = request.data.get('user')

        try:
            # First Update user email if it is duplicate then it throws IntegrityError else User will be updated.
            user = User.objects.get(id=userId)
            user.email=request.data.get('email')

            reader = Reader.objects.get(pk=readerId)
            readers_serializer = ReaderSerializer(reader,data=request.data, partial=True)
            if readers_serializer.is_valid():
                user.save()
                readers_serializer.save()
                return JsonResponse({"detail" : "Reader updated Successfully."}, status=HTTP_200_OK)
            else:
                # This error mostly occurs when user mistakes in profession, address and gender
                return JsonResponse({"detail" : "Failed to update a reader. Try again"}, status= 600)


        except ObjectDoesNotExist as e:
            return JsonResponse({"detail": "Requested User doesn't exists. Please try again"}, status=600)
        except IntegrityError as e:
            return JsonResponse({"detail": "Provided Email already exists. Please try another"}, status=HTTP_404_NOT_FOUND)
               


        """   try:
            reader = Reader.objects.get(pk=readerId)
            readers_serializer = ReaderSerializer(reader,data=request.data, partial=True)
            if readers_serializer.is_valid():
                readers_serializer.save()

                # If reader and user has different email addresses change user's email with reader's
                usr = reader.user
                reader = Reader.objects.get(user=usr)
                if(usr.email != reader.email):
                    usr.email=reader.email
                    usr.save()

                return JsonResponse({"detail" : "Reader updated Successfully."}, status=HTTP_200_OK)
            return JsonResponse({"detail" : "Failed to update a reader. Try again"}, status= HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return JsonResponse({"detail": "Requested User doesn't exists. Please try again"}, status=HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return JsonResponse({"detail": "Provided Email already exists. Please try another"}, status=HTTP_404_NOT_FOUND)
            
         """

    elif request.method == 'DELETE':
        # API: http://127.0.0.1:8000/bbc/api/getReader/4
        
        try:
            reader = Reader.objects.get(id=id)
            #reader.delete()
            return Response("Dear "+reader.full_name()+", Please contact admin to delete your account.", status=HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"detail" : "Such user does not exits."}, status=HTTP_404_NOT_FOUND)


#This performs only BOOK UPDATE and BOOK DELETE
# 
@csrf_exempt
@api_view(["PUT","DELETE"])
#@permission_classes((IsAuthenticated, ))
#@authentication_classes((JWTAuthentication,))
def bookApi(request,ownerId=0):
    try:
        bookId = request.data.get('id')
    except:
        Response({"detail" : "Provide bookId in Request"}, status=HTTP_400_BAD_REQUEST)
    
    if request.method == 'PUT':
        # API: http://127.0.0.1:8000/bbc/api/getBooks/1   BODY: { "id": 1,"desc":"ddfd" }
        if "borrow_count" not in request.data:
            book = Book.objects.get(pk=bookId)
            if ownerId == book.reader.id:
                print("--------------OwnerID------------"+ str(book.reader.id))

                book_serializer = BookSerializer(book,data=request.data, partial=True)
                if book_serializer.is_valid():
                    book_serializer.save()
                    return Response(book_serializer.data, status=HTTP_200_OK)
            else:
                return Response({"detail" : "You can make changes on your books only."}, status=HTTP_400_BAD_REQUEST)
        else:
            return Response({"detail" : "Failed to create a Book. You cannot update borrow count of your own book."}, status=HTTP_400_BAD_REQUEST)            
        return Response({"detail" : "Failed to update a Book. Try again"}, status=HTTP_400_BAD_REQUEST)
   
    elif request.method == 'DELETE':
        # API: http://127.0.0.1:8000/bbc/api/getBooks/1   BODY: { "id": 1 }
        book = Book.objects.get(pk=bookId)

        if ownerId == book.reader.id:
            read = Book.objects.get(pk=bookId)
            read.delete() #http://127.0.0.1:8000/bbc/api/getBooks/1   BODY: { "id": 1 }
            try:
                allbooks = requests.get("http://"+request.get_host()+reverse('allbookspag'))
                mybooks= requests.get("http://"+request.get_host()+reverse('mybooks',args=(ownerId,)))

                if allbooks.status_code == 200 and mybooks.status_code==200:                    
                    return JsonResponse({
                        "detail":"success",
                        "books":allbooks.json(),
                        "mybook":mybooks.json()
                        }, status=HTTP_200_OK)
                else:
                    return JsonResponse({"detail": "Book successfully deleted. But data cannot be fetched."},status=HTTP_400_BAD_REQUEST)

            except:
                #Book already deleted
                return JsonResponse({"detail": "Something went wrong while fetching your books!"},status=HTTP_404_NOT_FOUND)
        
        else:
            #Book not deleted
            return Response({"detail" : "You can delete your books only."},status=HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["GET",])
#@permission_classes((IsAuthenticated, ))
#@authentication_classes((JWTAuthentication,))
def getMyBooks(request,ownerId):
    # API : http://127.0.0.1:8000/bbc/api/getMyBooks/1
    paginator = PageNumberPagination()
    paginator.page_size = 4
    mybooks = Book.objects.filter(reader=ownerId).order_by("-id")
    result_page = paginator.paginate_queryset(mybooks, request)
    mybooks_seri = BookSerializer(result_page, many= True)
    return paginator.get_paginated_response(mybooks_seri.data)



@csrf_exempt
@api_view(["POST",])
#@permission_classes((IsAuthenticated, ))
#@authentication_classes((JWTAuthentication,))
def changePassword(request):
    uname = request.POST['username']
    upass = request.POST['password']
    new_pass = request.POST['newpass']

    if uname is None or upass is None:
        return Response({'detail':'Please enter username & password!'},status=HTTP_400_BAD_REQUEST)
    
    # You cannot use password to get user object directly. Therefore, use authenticate.
    usr = authenticate(username= uname, password=upass)
    if usr is not None:
        usr.set_password(new_pass)
        usr.save()

        return Response({"detail":"Password is changed successfully"}, status=HTTP_200_OK)
    else:
        return Response({"detail":"Wrong credentials"}, status=HTTP_400_BAD_REQUEST)


def getBorrows(id):
    borrows = Borrow.objects.filter(Q(borrower=id) | Q(book_borrowed__reader=id)) # Borrower is one with id and owner is book_borrowed__reader
    borrows_serializer = BorrowSerializer(borrows, many=True)
    return borrows_serializer.data


@api_view(["GET","POST","PUT","DELETE"])
#@permission_classes((IsAuthenticated, ))
#@authentication_classes((JWTAuthentication,))
@csrf_exempt
def borrowApi(request,id=0):
    if request.method == 'GET':
        # Get all Borrow Events
        data = getBorrows(id)
        return Response({"my_events":data}, status=HTTP_200_OK)

    elif request.method == 'POST':
        # Borrow book 
        # 1. Cannot borrow own book.
        # 2. Cannot send borrow request twice for same book.
        # 3. Cannot borrow if already borrowed 2 books
        borrow_data=JSONParser().parse(request)
        try:
            borrowerId = int(borrow_data['borrower'])
            bookId = int(borrow_data['book_borrowed'])
            book = Book.objects.get(id=bookId)

            # Check if user has alreadry requested for this book. 
            borrowReq = Borrow.objects.filter(Q(borrower=borrowerId) & Q(book_borrowed=bookId)) # Borrower is one with id and owner is book_borrowed__reader

            if borrowReq.count()>0:
                print("Request Already Sent.")
                return Response({"detail" : "You have already sent borrow Request for this book."}, status=HTTP_400_BAD_REQUEST)
            

            if(book.available_status):
                borrower = Reader.objects.get(id=borrowerId)
                if(book.reader == borrower):
                    return Response({"detail" : "You cannot borrow your own Book. Thank you."}, status=HTTP_400_BAD_REQUEST)

                
                already_borrowed_books=borrower.books_borrowed
                if(already_borrowed_books<2):
                    borrow_serializer = BorrowSerializer(data=borrow_data)
                    if borrow_serializer.is_valid():
                        borrow_serializer.save()
                        # Get all Borrow Events
                        data = getBorrows(borrowerId)
                        return Response({
                            "detail":"Book Request Successfull. Wait for confirmation....",
                            "my_events":data
                        }, status=HTTP_200_OK)
                else:
                    return JsonResponse({"detail" : "Failed to borrow a Book. Try again (You have already borrowed 2 books"}, status=HTTP_400_BAD_REQUEST)
            else:
                return JsonResponse({"detail":"Failed to borrow a Book. Try again (Book status unavailable)"}, status=HTTP_400_BAD_REQUEST)
        except :
            return JsonResponse({"detail":"Failed to borrow a Book. Missing request data."}, status=HTTP_400_BAD_REQUEST)

    
    elif request.method == 'PUT':
        borrow_data=JSONParser().parse(request)  
        borrowerID = int(borrow_data['borrower'])
        borrow = Borrow.objects.get(id=int(borrow_data['id']))
        borrower = Reader.objects.filter(id=borrowerID)
        book_borrowed = Book.objects.filter(id=int(borrow_data['book_borrowed']))

        if(borrow_data['borrow_accept'] and not borrow_data['book_received_by_borrower']):
            # To stop user to hit same accept request api multiple times.
            if not borrow.borrow_accept:
                
                # Here, Owner accepts the borrow request. But, he should have borrowed less than 2 books only.
                already_borrowed_books=borrower.first().books_borrowed
                if(already_borrowed_books<2):

                    #Creating borrow accept time
                    borrow_accept_time_now = datetime.now()
                    borrow_data['borrow_accept_date'] = borrow_accept_time_now
                    print(borrow_data)

                    borrow_serializer = BorrowSerializer(borrow,data=borrow_data)
                    if borrow_serializer.is_valid():
                        borrow_serializer.save()
                        # Once borrow request is accepted by owner then borrower's currently borrowed book count is incremented by 1.
                        borrower.update(books_borrowed= already_borrowed_books+ 1)
                        # Once borrow request is accepted by owner then book's available status is changed to unavailable.
                        book_borrowed.update(available_status=False)
                        data = getBorrows(borrowerID)
                        return Response({
                            "detail":"Borrow request Accepted.",
                            "my_events": data
                            }, status=HTTP_200_OK)
                else:
                    return Response({"detail" : "Book can't be issued. Borrower already have 2 borrowed books"}, status=HTTP_400_BAD_REQUEST)

            else:
                return Response({"detail" : "Book request is already accepted for you."}, status=HTTP_400_BAD_REQUEST)

        elif(borrow_data['borrow_accept'] and borrow_data['book_received_by_borrower'] and not borrow_data['returned']):
            # Here, Borrower collects requested book from Owner of book. But, Owner should accept the borrow request first.

            borrow_serializer = BorrowSerializer(borrow,data=borrow_data)
            if borrow_serializer.is_valid():
                borrow_serializer.save()
                data = getBorrows(borrowerID)

                return Response({
                    "detail":"Book is received by the Borrower.",
                    "my_events": data
                    }, status=HTTP_200_OK)


        elif(borrow_data['book_received_by_borrower'] and borrow_data['returned']):            
            # BOOK is returned to Owner. 

            # Create new record in BorrowHistory table
            BorrowHistory.objects.create(borrower=borrow.borrower, book_borrowed=borrow.book_borrowed, borrow_accept_date=borrow.borrow_accept_date,social_score=borrow_data['social_score'], borrower_note=borrow.note,owner_comment=borrow_data['owner_comment'])

            # Delete the borrow book record 
            borrow.delete()

            # Update Book and Reader table 
            borrower.update(books_borrowed= (borrower.first().books_borrowed-1))
            book_borrowed.update(available_status=True,borrow_count= (book_borrowed.first().borrow_count+1))
            data = getBorrows(borrowerID)

            return Response({
                "detail":"Borrowed book returned Successfully.",
                "my_events":data
                }, status=HTTP_200_OK)

        else:
            # Only for note updation
            borrow_serializer = BorrowSerializer(borrow,data=borrow_data)
            if borrow_serializer.is_valid():
                borrow_serializer.save()
                data = getBorrows(borrowerID)

                return Response({
                    "detail":"Borrow Note is updated Successfully.",
                    "my_events":data
                    }, status=HTTP_200_OK)



    # Borrower can cancel his borrow request from here
    # or Owner of Book can cancel the borrow request from here
    elif request.method == 'DELETE':
        borrow_data=JSONParser().parse(request)         
        borrow_request = Borrow.objects.get(id=int(borrow_data['id']))
        borrowerID = borrow_request.borrower.id
        if borrow_request.borrow_accept and not borrow_request.book_received_by_borrower:
            # If borrow request is accepted by owner then "available_status" was set to FALSE
            # accepted: True , collected: False
            book = borrow_request.book_borrowed
            borrower = borrow_request.borrower
            book.available_status=True
            book.save()
            borrower.books_borrowed -= 1
            borrower.save()
            borrow_request.delete()

            data = getBorrows(borrowerID)
            return  Response({
                "detail":"Borrow request cancelled Successfully. (accept: yes, collected: no)",
                "my_events":data
                }, status= HTTP_200_OK)
        elif not borrow_request.borrow_accept:
            # accepted: False , collected: False
            borrow_request.delete()
            data = getBorrows(borrowerID)
            return  Response({
                "detail":"Borrow request cancelled Successfully. (accept: no)",
                "my_events":data
                }, status= HTTP_200_OK)
        else:
            # accepted: True , collected: True
            return  Response({
                "detail":"Cannot cancel request until you return the book.",
                  }, status= HTTP_400_BAD_REQUEST)



@api_view(["GET",])
@csrf_exempt
def borrowHistoryApi(request):
    if request.method == 'GET':
        borrows = BorrowHistory.objects.all()
        borrows_serializer = BorrowHistorySerializer(borrows, many=True)
        return JsonResponse(borrows_serializer.data, safe=False)



