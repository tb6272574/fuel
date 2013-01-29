from django.db import models
from django.contrib.auth.models import User
import datetime, pytz

# constants

DAILY_BONUS = 100

TYPES = (
        (0, 'reserved'),
        (1, 'Fuel band'),
        (2, 'Daily bonus'),
        (3, 'Bet'),
        (4, 'Gamble return'),
        )

# Create your models here.

class FuelUser(User):

    BOOST_DAYS = {
            'M': 'Monday',
            'T': 'Tuesday',
            'W': 'Wednesday',
            'H': 'Thursday',
            'F': 'Friday',
            'S': 'Saturday',
            'U': 'Sunday',
            }

    STATUS = {
            'b': 'bronze',
            's': 'silver',
            'g': 'gold',
            }

    def name(self):
        return self.get_full_name()

    def start_date(self):
        return self.profile.start_date.astimezone(pytz.timezone('America/Los_Angeles')).strftime('%m/%d/%y %H:%M:%S')

    def boost_day(self):
        return self.BOOST_DAYS[self.profile.boost_day]

    def status(self):
        return self.STATUS[self.profile.status]

    def credit(self):
        return self.STATUS[self.profile.status]

    class Meta:
        ordering = ['id']
        proxy = True

class Amount(models.Model):
    user = models.ForeignKey(User)
    time = models.DateTimeField('Time', default='', auto_now_add=True)
    #date = models.DateField('Date', default='', auto_now_add=True)
    amount = models.IntegerField('Amount', default=0)
    atype = models.IntegerField('Type', choices=TYPES, default=0)
    action = models.CharField('Action', max_length=100)
    def __unicode__(self):
        return u"%d" % (self.amount)

class Profile(models.Model):
    user = models.OneToOneField(User)
    start_date = models.DateTimeField('Started', default='', auto_now_add=True)

    DAYS_OF_WEEK = (
            ('M', 'Monday'),
            ('T', 'Tuesday'),
            ('W', 'Wednesday'),
            ('H', 'Thursday'),
            ('F', 'Friday'),
            ('S', 'Saturday'),
            ('U', 'Sunday'),
            )
    boost_day = models.CharField(max_length=1, choices=DAYS_OF_WEEK, default=0) 

    STATUS = (
            ('b', 'bronze'),
            ('s', 'silver'),
            ('g', 'gold'),
            )
    status = models.CharField(max_length=1, choices=STATUS, default=0)

    last_input_time = models.DateTimeField('Last input time', default='')

    def add_daily_bonus(self):
        a = Amount()
        a.user = self.user
        a.amount = DAILY_BONUS
        a.atype = 2
        a.action = 'Daily bonus for %s' % datetime.now().astimezone(pytz.timezone('America/Los_Angeles')).strftime('%m/%d/%y')
        a.save()

    def current_amount(self):
        return sum([a.amount for a in user.amount_set])
    
class Record(models.Model):
    user = models.ForeignKey(User)
    date = models.DateField('Date', default='')
    steps = models.PositiveIntegerField('Steps', default=0)
    calories = models.PositiveIntegerField('Calories', default=0)
    fuelscore = models.PositiveIntegerField('FuelScore', default=0)
    amount = models.OneToOneField(Amount)
    last_updated = models.DateTimeField('Last updated', default='', auto_now=True)

    def get_amount(self):
        return self.fuelscore

    def save_amount(self):
        a = Amount()
        a.user = self.user
        a.amount = self.get_amount()
        a.atype = 1
        #a.action = 'FuelScore for %s' % date.strftime('%m/%d/%y')
        a.save()
        self.amount = a
        self.save()



