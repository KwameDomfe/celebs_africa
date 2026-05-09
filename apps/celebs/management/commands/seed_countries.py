from django.core.management.base import BaseCommand
from apps.celebs.models import Country

AFRICAN_COUNTRIES = [
    ('Algeria', 'DZ', '🇩🇿'),
    ('Angola', 'AO', '🇦🇴'),
    ('Benin', 'BJ', '🇧🇯'),
    ('Botswana', 'BW', '🇧🇼'),
    ('Burkina Faso', 'BF', '🇧🇫'),
    ('Burundi', 'BI', '🇧🇮'),
    ('Cabo Verde', 'CV', '🇨🇻'),
    ('Cameroon', 'CM', '🇨🇲'),
    ('Central African Republic', 'CF', '🇨🇫'),
    ('Chad', 'TD', '🇹🇩'),
    ('Comoros', 'KM', '🇰🇲'),
    ('DR Congo', 'CD', '🇨🇩'),
    ('Republic of Congo', 'CG', '🇨🇬'),
    ('Djibouti', 'DJ', '🇩🇯'),
    ('Egypt', 'EG', '🇪🇬'),
    ('Equatorial Guinea', 'GQ', '🇬🇶'),
    ('Eritrea', 'ER', '🇪🇷'),
    ('Eswatini', 'SZ', '🇸🇿'),
    ('Ethiopia', 'ET', '🇪🇹'),
    ('Gabon', 'GA', '🇬🇦'),
    ('Gambia', 'GM', '🇬🇲'),
    ('Ghana', 'GH', '🇬🇭'),
    ('Guinea', 'GN', '🇬🇳'),
    ('Guinea-Bissau', 'GW', '🇬🇼'),
    ('Ivory Coast', 'CI', '🇨🇮'),
    ('Kenya', 'KE', '🇰🇪'),
    ('Lesotho', 'LS', '🇱🇸'),
    ('Liberia', 'LR', '🇱🇷'),
    ('Libya', 'LY', '🇱🇾'),
    ('Madagascar', 'MG', '🇲🇬'),
    ('Malawi', 'MW', '🇲🇼'),
    ('Mali', 'ML', '🇲🇱'),
    ('Mauritania', 'MR', '🇲🇷'),
    ('Mauritius', 'MU', '🇲🇺'),
    ('Morocco', 'MA', '🇲🇦'),
    ('Mozambique', 'MZ', '🇲🇿'),
    ('Namibia', 'NA', '🇳🇦'),
    ('Niger', 'NE', '🇳🇪'),
    ('Nigeria', 'NG', '🇳🇬'),
    ('Rwanda', 'RW', '🇷🇼'),
    ('São Tomé and Príncipe', 'ST', '🇸🇹'),
    ('Senegal', 'SN', '🇸🇳'),
    ('Seychelles', 'SC', '🇸🇨'),
    ('Sierra Leone', 'SL', '🇸🇱'),
    ('Somalia', 'SO', '🇸🇴'),
    ('South Africa', 'ZA', '🇿🇦'),
    ('South Sudan', 'SS', '🇸🇸'),
    ('Sudan', 'SD', '🇸🇩'),
    ('Tanzania', 'TZ', '🇹🇿'),
    ('Togo', 'TG', '🇹🇬'),
    ('Tunisia', 'TN', '🇹🇳'),
    ('Uganda', 'UG', '🇺🇬'),
    ('Zambia', 'ZM', '🇿🇲'),
    ('Zimbabwe', 'ZW', '🇿🇼'),
]


class Command(BaseCommand):
    help = 'Seed all 54 African countries with ISO codes and flag emojis'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for name, code, flag in AFRICAN_COUNTRIES:
            obj, was_created = Country.objects.update_or_create(
                code=code,
                defaults={'name': name, 'flag': flag},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} created, {updated} updated. Total: {created + updated} countries.'
        ))
