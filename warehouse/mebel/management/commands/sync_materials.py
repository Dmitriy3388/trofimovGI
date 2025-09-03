from django.core.management.base import BaseCommand
from mebel.models import Material

class Command(BaseCommand):
    help = 'Синхронизирует резервы материалов с актуальными данными заказов'

    def handle(self, *args, **options):
        Material.update_all_reserved_quantities()
        self.stdout.write(
            self.style.SUCCESS('✅ Резервы материалов успешно синхронизированы с заказами')
        )