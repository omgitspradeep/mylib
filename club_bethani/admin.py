from django.contrib import admin
from club_bethani.models import Reader, Book, Borrow, BorrowHistory
from django.contrib.auth.models import Group

# Register your models here.


admin.site.header = "Bethani Book Club"
admin.site.site_title = "BBC"
admin.site.index_title ="INDEX TITLE"

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    #fields = (('firstname','lastname'), 'gender', 'address', 'phone_number','email','house_no','profession')
    list_display = ('id','full_name','username','password', 'gender', 'address','house_no','phone_number','email','profession','books_shared','books_borrowed','account_activated' )
    search_fields =('firstname','lastname')
    list_filter = ('profession','gender')



@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'reader', 'author','image','description','available_status','borrow_count','upload_date','language' )
    search_fields = ('name','author')
    list_filter = ('available_status','author','language')

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'book_borrowed', 'request_date','borrow_accept','accepted_time','book_received_by_borrower','note','remaining_days')
    list_filter=('request_date',)

@admin.register(BorrowHistory)
class BorrowHistoryAdmin(admin.ModelAdmin):
    list_display = ('borrower', 'book_borrowed', 'book_owner', 'borrow_accept_date','returned_date','social_score','borrower_note','owner_comment')
    list_filter=('returned_date',)

#Removes Group from the admin panel
# admin.site.unregister(Group)