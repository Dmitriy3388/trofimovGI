from decimal import Decimal
from django.conf import settings
from mebel.models import Material


class OrderCart:
    def __init__(self, request):
        #Инициализируем пустую корзину заказа
        self.session = request.session
        ordercart = self.session.get(settings.ORDERCART_SESSION_ID)
        if not ordercart:
            ordercart = self.session[settings.ORDERCART_SESSION_ID] = {}
        self.ordercart = ordercart


    def __iter__(self):
        """
        Прокрутить материальные позиции в заказе и получить материалы из базы данных
        """
        material_ids = self.ordercart.keys()
        # get the  objects and add them to the
        materials = Material.objects.filter(id__in=material_ids)
        ordercart = self.ordercart.copy()
        for material in materials:
            ordercart[str(material.id)]['material'] = material
        for item in ordercart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Добавить материал к заказу либо обновить его количество.
        """
        return sum(item['quantity'] for item in self.ordercart.values())

    def add(self, material, quantity=1, override_quantity=False):
        """
        Добавить товар к заказу или обновить количество
        """
        material_id = str(material.id)
        if material_id not in self.ordercart:
            self.ordercart[material_id] = {'quantity': 0, 'price': str(material.price)}
        if override_quantity:
            self.ordercart[material_id]['quantity'] = quantity
        else:
            self.ordercart[material_id]['quantity'] += quantity
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, material):
        """
        Удалить материал из заказа
        """
        material_id = str(material.id)
        if material_id in self.ordercart:
            del self.ordercart[material_id]
            self.save()

    def clear(self):
        # remov from session
        del self.session[settings.ORDERCART_SESSION_ID]
        self.save()

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.ordercart.values())