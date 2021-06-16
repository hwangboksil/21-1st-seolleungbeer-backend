import json,uuid
from json.decoder    import JSONDecodeError
from copy            import deepcopy

from django.http     import JsonResponse
from django.views    import View
from django.db       import transaction,IntegrityError

from .models         import Order,OrderItem,OrderStatus
from products.models import Product, ProductImage
from users.utils     import user_decorator


class OrderView(View):
    @user_decorator
    def get(self,request):
        result = {
            'name': request.user.name,
            'email': request.user.email,
            'mobile': request.user.mobile
        }
        return JsonResponse(result,status=200)

    @user_decorator
    def post(self,request):
        try:
            with transaction.atomic():
                data      = json.loads(request.body)
                new_order = Order.objects.create(
                    order_number        = uuid.uuid4(),
                    delivery_memo       = data['delivery_memo'],
                    payment_information = data['payment_information'],
                    payment_charge      = data['payment_charge'],
                    user                = request.user,
                    order_status_id     = 1
                )

                for key,value in data['order_item'].items():
                    item = OrderItem.objects.get(id=key)

                    if item.amount != value:
                        item_in_cart        = deepcopy(item)
                        item_in_cart.id     = None
                        item_in_cart.amount = item.amount-value
                        item_in_cart.save()

                    item.order  = new_order
                    item.amount = value
                    item.save()

                return JsonResponse({'message':'SUCCESS'}, status=200)

        except OrderItem.DoesNotExist:
            return JsonResponse({'message':'DOES NOT EXIST'}, status=400)
        except IntegrityError:
            return JsonResponse({'message':'INTEGRITY ERROR'}, status=400)
        except JSONDecodeError:
            return JsonResponse({'message':'JSON DECODE ERROR'}, status=400)

class CartView(View):
    @user_decorator
    def post(self, request):
        try:
            data           = json.loads(request.body)
            user           = request.user
            product        = data['product_id']
            current_amount = 0

            if not Product.objects.filter(id=product).exists():
                return JsonResponse({'message':'PRODUCT_DOES_NOT_EXIST'}, status=400)

            order, is_created = Order.objects.get_or_create(
                        user            = user,
                        order_status_id = OrderStatus.PENDING,
                        defaults        = {'order_number':uuid.uuid4()}
                    )

            if OrderItem.objects.filter(order=order, product_id=product).exists():
                current_amount = OrderItem.objects.get(order=order, product_id=product).amount

            order_item, is_created = OrderItem.objects.update_or_create(
                        order      = order,
                        product_id = product,
                        defaults   = {'amount':data['amount'] + current_amount},
                        )

            return JsonResponse({'message':"SUCCESS", "order_item_id":order_item.id},status=200)

        except KeyError:
            return JsonResponse({'message':'KEY_ERROR'},status=400)

    @user_decorator
    def get(self, request):
        try:
            user       = request.user
            order_item = OrderItem.objects.filter(
                order__user            = user,
                order__order_status_id = OrderStatus.PENDING
            )

            result     = [{
                    'order_id'        : carts.order.id,
                    'cart_id'         : carts.id,
                    'amount'          : carts.amount,
                    'korean_name'     : carts.product.korean_name,
                    'english_name'    : carts.product.english_name,
                    'delivery_charge' : carts.order.delivery_charge,
                    'payment_charge'  : carts.product.price,
                    'product_image'   : carts.product.main_image,
                    'delivery_method' : carts.order.delivery_method
                } for carts in order_item]

            return JsonResponse({'message':'SUCCESS', 'result':result}, status=200)
            
        except OrderItem.DoesNotExist:
            return JsonResponse({'message': 'NOTHING_IN_CART'}, status=400)
