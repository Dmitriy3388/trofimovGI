from .ordercart import OrderCart


def ordercart(request):
    return {'ordercart': OrderCart(request)}