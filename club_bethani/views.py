from django.db.models import manager
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from datetime import datetime, timedelta

from club_bethani.serializer import ReaderSerializer, BookSerializer, BorrowSerializer, BorrowHistorySerializer
from club_bethani.models import Reader, Book, Borrow, BorrowHistory

# Create your views here.
@csrf_exempt
def readerApi(request,id=0):
    if request.method == 'GET':
        readers = Reader.objects.filter(account_activated=True)
        readers_serializer = ReaderSerializer(readers, many=True)
        return JsonResponse(readers_serializer.data, safe=False)
    
    elif request.method == 'POST':
        reader_data=JSONParser().parse(request)
        readers_serializer = ReaderSerializer(data=reader_data)
        if readers_serializer.is_valid():
            readers_serializer.save()
            return JsonResponse("Reader created Successfully.", safe=False)
        return JsonResponse("Failed to create a reader. Try again", safe= False)
    
    elif request.method == 'PUT':
        reader_data=JSONParser().parse(request)
        reader = Reader.objects.get(id=reader_data['id'])
        readers_serializer = ReaderSerializer(reader,data=reader_data)
        if readers_serializer.is_valid():
            readers_serializer.save()
            return JsonResponse("Reader updated Successfully.", safe=False)
        return JsonResponse("Failed to update a reader. Try again", safe= False)
   
    elif request.method == 'DELETE':
        reader = Reader.objects.get(id=id)
        reader.delete()
        return JsonResponse("Reader deleted successfully.", safe= False)

@csrf_exempt
def bookApi(request,id=0):
    if request.method == 'GET':
        readers = Book.objects.all()
        readers_serializer = BookSerializer(readers, many=True)
        return JsonResponse(readers_serializer.data, safe=False)
    
    elif request.method == 'POST':

        book_data=JSONParser().parse(request)
        print(book_data)
        book_serializer = BookSerializer(data=book_data)

        if book_serializer.is_valid():
            book_serializer.save()
            return JsonResponse("Book created Successfully.", safe=False)

        return JsonResponse("Failed to create a Book. Try again", safe= False)

    
    elif request.method == 'PUT':
        book_data=JSONParser().parse(request)
        if "borrow_count" not in book_data:
            book = Book.objects.get(id=book_data['id'])
            book_serializer = BookSerializer(book,data=book_data)
            if book_serializer.is_valid():
                book_serializer.save()
                return JsonResponse("Book updated Successfully.", safe=False)
        else:
            return JsonResponse("Failed to create a Book. You cannot update borrow count of your own book.", safe= False)            
        return JsonResponse("Failed to update a Book. Try again", safe= False)
   
    elif request.method == 'DELETE':
        reader = Book.objects.get(id=id)
        reader.delete()
        return JsonResponse("Book deleted successfully.", safe= False)


@csrf_exempt
def borrowApi(request,id=0):
    if request.method == 'GET':
        borrows = Borrow.objects.all()
        borrows_serializer = BorrowSerializer(borrows, many=True)
        return JsonResponse(borrows_serializer.data, safe=False)
    
    elif request.method == 'POST':
        borrow_data=JSONParser().parse(request)
        print(borrow_data)
        book = Book.objects.get(id=int(borrow_data['book_borrowed']))
        if(book.available_status):
            borrower = Reader.objects.get(id=int(borrow_data['borrower']))
            
            if(book.reader == borrower):
                return JsonResponse("You cannot borrow your own Book. Thank you.", safe=False)

            already_borrowed_books=borrower.books_borrowed
            if(already_borrowed_books<2):
                borrow_serializer = BorrowSerializer(data=borrow_data)
                if borrow_serializer.is_valid():
                    borrow_serializer.save()
                    return JsonResponse("Book Request Successfull. Wait for confirmation....", safe=False)
            else:
                return JsonResponse("Failed to borrow a Book. Try again (You have already borrowed 2 books)", safe= False)


        return JsonResponse("Failed to borrow a Book. Try again (Book status unavailable)", safe= False)

    
    elif request.method == 'PUT':
        borrow_data=JSONParser().parse(request)         
        borrow = Borrow.objects.get(id=int(borrow_data['id']))
        borrower = Reader.objects.filter(id=int(borrow_data['borrower']))
        book_borrowed = Book.objects.filter(id=int(borrow_data['book_borrowed']))

        if(borrow_data['borrow_accept'] and not borrow_data['book_received_by_borrower']):

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
                    return JsonResponse("Borrow request Accepted.", safe=False)
            else:
                return JsonResponse("Book can't be issued. Borrower already have 2 borrowed books)", safe= False)

        elif(borrow_data['borrow_accept'] and borrow_data['book_received_by_borrower'] and not borrow_data['returned']):
            # Here, Borrower collects requested book from Owner of book. But, Owner should accept the borrow request first.

            borrow_serializer = BorrowSerializer(borrow,data=borrow_data)
            if borrow_serializer.is_valid():
                borrow_serializer.save()
                return JsonResponse("Book is received by the Borrower.", safe=False)


        elif(borrow_data['book_received_by_borrower'] and borrow_data['returned']):            
            # BOOK is returned to Owner. 

            # Create new record in BorrowHistory table
            BorrowHistory.objects.create(borrower=borrow.borrower, book_borrowed=borrow.book_borrowed, borrow_accept_date=borrow.borrow_accept_date,social_score=borrow_data['social_score'], borrower_note=borrow.note,owner_comment=borrow_data['owner_comment'])

            # Delete the borrow book record 
            borrow.delete()

            # Update Book and Reader table 
            borrower.update(books_borrowed= (borrower.first().books_borrowed-1))
            book_borrowed.update(available_status=True,borrow_count= (book_borrowed.first().borrow_count+1))
            return JsonResponse("Borrowed book returned Successfully.", safe=False)

        else:
            borrow_serializer = BorrowSerializer(borrow,data=borrow_data)
            if borrow_serializer.is_valid():
                borrow_serializer.save()
                return JsonResponse("Borrow data updated Successfully.", safe=False)



    # Borrower can cancel his borrow request from here
    # or Owner of Book can cancel the borrow request from here
    elif request.method == 'DELETE':
        borrow_data=JSONParser().parse(request)         
        borrow_request = Borrow.objects.get(id=int(borrow_data['id']))


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
            return JsonResponse("Borrow request cancelled Successfully. (accept: yes, collected: no)", safe=False)

        elif not borrow_request.borrow_accept:
            # accepted: False , collected: False
            
            borrow_request.delete()
            return JsonResponse("Borrow request cancelled Successfully. (accept: no)", safe=False)
        else:
            # accepted: True , collected: True

            return JsonResponse("Cannot cancel request until you return the book.", safe=False)



@csrf_exempt
def borrowHistoryApi(request):
    if request.method == 'GET':
        borrows = BorrowHistory.objects.all()
        borrows_serializer = BorrowHistorySerializer(borrows, many=True)
        return JsonResponse(borrows_serializer.data, safe=False)
    


"""
 MIN JSON DATA FOR BORROWING API

 1) CREATE BORROW                                HIT BY: BORROWER
        {
            "note": "I was searching for this book for so long. Please provide me this book.",
            "borrower": 2,
            "book_borrowed": 1
        }

2) UPDATE BORROW: SIMPLE       HIT BY: BORROWER


3) UPDATE BORROW: BORROW ACCEPTANCE BY OWNER OF A BOOK.  HIT BY: OWNER OF BOOK
    {
        "id": 7,
        "borrower": 2,
        "book_borrowed": 1,
        "borrow_accept": true,
        "book_received_by_borrower":false,
        "returned": false
    }

4) UPDATE BORROW : BOOK COLLECTED BY A BORROWER ( BOOK IS RECEIVED BY READER/BORROWER).   HIT BY: BORROWER
{
    "id": 7,
    "borrower": 2,
    "book_borrowed": 1,
    "borrow_accept": true,
    "book_received_by_borrower":true,
    "returned": false
}


5) UPDATE BORROW: BOOK RETURNED BY A READER AND OWNER UPDATES THE RETURNED STATUS.  HIT BY: OWNER OF BOOK

{
    "id": 7,
    "borrower": 2,
    "book_borrowed": 1,
    "borrow_accept": true,
    "book_received_by_borrower":true,
    "returned": true,
    "owner_comment":" He returns too late. Don't give him books."
    "social_score": -5
}







6) GET BORROW: http://127.0.0.1:8000/bbc/borrowBooks/

    {
        "id": 2,
        "request_date": "2021-05-31T08:36:40.693349+05:45",
        "borrow_accept": false,
        "borrow_accept_date": "2021-05-31T08:36:40.693387+05:45",
        "note": "I was searching for this book for so long. Please provide me this book.",
        "returned": false,
        "borrower": 2,
        "book_borrowed": 1
    }

"""

"""

readerApi post datasample
{
    "firstname": "Harsha",
    "lastname": "Verma",
    "username": "harh",
    "password": "1abc@def",
    "gender": "F",
    "address": "Butwal-18, Rupandehi",
    "phone_number": "",
    "email": "awan@gmail.com",
    "house_no": 45,
    "profession": "B",
    "profile_pic": null,
    "account_activated": false
}



bookapi post datasample

{
    "author": "Pradeepa",
    "name": "Sadguru",
    "image": null,
    "description": "It imparts genuine love for God.",
    "available_status": true,
    "borrow_count": 0,
    "language": "E",
    "reader": 1
}

"""