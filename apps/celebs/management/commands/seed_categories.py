from django.core.management.base import BaseCommand
from apps.celebs.models import Category, Family, Type

CATEGORIES = [
    ('Music', [
        ('Afrobeats', ['Solo Artist', 'Group/Band', 'Producer', 'DJ']),
        ('Afropop', ['Solo Artist', 'Group/Band']),
        ('Amapiano', ['Solo Artist', 'Group/Band', 'DJ/Producer']),
        ('Highlife', ['Solo Artist', 'Group/Band']),
        ('Hip-Hop & Rap', ['Solo Artist', 'Group/Band', 'Producer']),
        ('R&B & Soul', ['Solo Artist', 'Group/Band']),
        ('Gospel', ['Solo Artist', 'Choir', 'Group/Band']),
        ('Reggae & Dancehall', ['Solo Artist', 'Group/Band']),
        ('Jazz', ['Solo Artist', 'Instrumentalist', 'Group/Band']),
        ('Traditional & Folk', ['Solo Artist', 'Group/Band']),
    ]),
    ('Film & TV', [
        ('Film', ['Actor', 'Director', 'Producer', 'Screenwriter']),
        ('Television', ['Actor', 'Presenter/Host', 'Producer']),
        ('Streaming', ['Actor', 'Creator/Showrunner']),
        ('Animation', ['Voice Actor', 'Animator']),
    ]),
    ('Sports', [
        ('Football', ['Player', 'Coach/Manager', 'Pundit']),
        ('Basketball', ['Player', 'Coach']),
        ('Athletics', ['Sprinter', 'Long Distance', 'Field Events']),
        ('Boxing', ['Boxer', 'Trainer']),
        ('Tennis', ['Player', 'Coach']),
        ('Rugby', ['Player', 'Coach']),
        ('Cricket', ['Player', 'Coach']),
        ('Martial Arts', ['Fighter', 'Trainer']),
    ]),
    ('Comedy', [
        ('Stand-up', ['Comedian', 'MC']),
        ('Sketch & Skit', ['Creator', 'Actor']),
        ('Satire', ['Commentator', 'Writer']),
    ]),
    ('Media & Journalism', [
        ('Broadcasting', ['TV Presenter', 'Radio Host', 'News Anchor']),
        ('Print & Digital', ['Journalist', 'Columnist']),
        ('Podcasting', ['Host', 'Creator']),
    ]),
    ('Fashion & Beauty', [
        ('Modelling', ['Runway Model', 'Print Model', 'Plus-size Model']),
        ('Design', ['Fashion Designer', 'Stylist']),
        ('Beauty', ['Makeup Artist', 'Hair Stylist']),
    ]),
    ('Business & Entrepreneurship', [
        ('Tech', ['Founder/CEO', 'Investor']),
        ('Finance', ['Banker', 'Investor', 'Economist']),
        ('Entertainment Business', ['Executive', 'Agent/Manager']),
        ('Retail & Consumer', ['Entrepreneur', 'Brand Owner']),
    ]),
    ('Politics & Activism', [
        ('Politics', ['Head of State', 'Minister', 'Legislator']),
        ('Activism', ['Human Rights', 'Environmental', 'Gender Equality']),
        ('Diplomacy', ['Ambassador', 'UN Official']),
    ]),
    ('Literature & Arts', [
        ('Literature', ['Author', 'Poet', 'Playwright']),
        ('Visual Arts', ['Painter', 'Sculptor', 'Photographer']),
        ('Performing Arts', ['Dancer', 'Choreographer', 'Theatre Actor']),
    ]),
    ('Social Media & Digital', [
        ('Content Creation', ['YouTuber', 'TikToker', 'Instagram Influencer']),
        ('Gaming', ['Streamer', 'Pro Gamer']),
        ('Blogging', ['Blogger', 'Vlogger']),
    ]),
    ('Religion & Spirituality', [
        ('Christianity', ['Pastor/Preacher', 'Evangelist']),
        ('Islam', ['Sheikh/Imam', 'Scholar']),
        ('Traditional', ['Spiritual Leader']),
    ]),
    ('Academia & Science', [
        ('Education', ['Professor', 'Lecturer', 'Researcher']),
        ('Science & Tech', ['Scientist', 'Inventor', 'Engineer']),
        ('Medicine', ['Doctor', 'Surgeon', 'Public Health Expert']),
    ]),
]


class Command(BaseCommand):
    help = 'Seed Category, Family, and Type data (safe to re-run; uses get_or_create)'

    def handle(self, *args, **options):
        cat_created = fam_created = type_created = 0

        for cat_name, families in CATEGORIES:
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                cat_created += 1

            for fam_name, types in families:
                family, created = Family.objects.get_or_create(
                    category=category, name=fam_name
                )
                if created:
                    fam_created += 1

                for type_name in types:
                    _, created = Type.objects.get_or_create(
                        family=family, name=type_name
                    )
                    if created:
                        type_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {cat_created} categories, '
            f'{fam_created} families, {type_created} types.'
        ))
