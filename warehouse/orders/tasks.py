
from celery import shared_task
from django.core.mail import send_mail
from .models import Order

from io import BytesIO
from celery import shared_task
import weasyprint
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from orders.models import Order


@shared_task
def order_created(order_id):
    """
    Задание по отправке уведомления по электронной почте
    при успешном создании заказа.
    """
    order = Order.objects.get(id=order_id)
    subject = f'Order nr. {order.id}'
    message = f'Заказ на {order.first_name},\n\n' \
              f'Оформлен. Материалы зарезервированы. Исполнитель {order.last_name}' \
              f'Подробная информация http://localhost:8000/admin/orders/order/ \n\n'\
              f'Номер заказа: {order.id}.'
    email = EmailMessage(subject, message, 'admin@warehouse.com',['trofimov3388@gmail.com'])
    html = render_to_string('orders/order/pdf.html', {'order': order})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT / 'css/pdf.css')]
    weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)
    email.attach(f'order_{order.id}.pdf', out.getvalue(),'application/pdf')
    email.send()
    return email.send()
