from django.contrib import admin

from .models import FarmExpense, FarmSale


@admin.register(FarmExpense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'date', 'payment_status', 'crop')
    list_filter = ('category', 'payment_status')


@admin.register(FarmSale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('crop', 'buyer_name', 'quantity_quintals', 'total_amount', 'amount_received', 'payment_status')
    list_filter = ('payment_status',)
