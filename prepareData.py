from fuel.models import *
import time
import datetime
from sets import Set

print 'Outputing all project members...'
f = open('projectmember.txt','w')
for p in Project.objects.all():
    a = p.members.all()
    f.write(str(len(a)))
    for m in a:
        f.write(' ' + str(m.id))
    f.write('\n')
f.close()

f = open('projecthighscore.txt','w')
for p in Project.objects.all():
    a = p.members.all()
    for m in a:
        s = Score.objects.filter(user=m)
        if len(s) > 0:
            scores = json.loads(s[0].score)
            f.write(str(m.id))
            for pid in range(1,14):
                if str(pid) in scores:
                    if scores[str(pid)] == 5:
                        f.write(' ' + str(pid))
            f.write('\n')
                       # print str(m) + ' gives 5 for project ' + str(pid)
f.close()


print 'Outputing all scales...'
f = open('scale.txt', 'w')
for s in Scale.objects.all().reverse():
    if not s.active:
        #rank of the winner w.r.t points earned up to the winning time
        rank = 1
        winner_point = sum([a.amount for a in Amount.objects.filter(user=s.winner).filter(time__lt=s.get_end_time()).filter(amount__gt=0)])
        for u in User.objects.all():
            u_point = sum([a.amount for a in Amount.objects.filter(user=u).filter(time__lt=s.get_end_time()).filter(amount__gt=0)])
            if u_point > winner_point:
                rank = rank + 1

        f.write(str(time.mktime(s.start_time.timetuple()))+ ' ' + str(time.mktime(s.get_end_time().timetuple())) + ' ' + str(s.winner.id) + ' ' +str(rank) + ' ' + str(s.money) + ' ' + str(len(s.amount_set.all())) + ' ')
        participate = Set([])
        for a in s.amount_set.all():
            participate.add(a.user.id)
        f.write(str(len(participate)) + '\n')
f.close()


print 'Outputing all amounts...'
f = open('amount.txt','w')
for a in Amount.objects.all().reverse():
    f.write(str(time.mktime(a.time.timetuple()))+' '+str(a.user.id)+' '+str(a.amount)+' '+str(a.atype)+'\n')
f.close()


print 'Outputing summary data for each user every day...'
f = open('data.txt','w')

now = 0
for u in FuelUser.objects.all():
    fr = u.friends()
    if fr == None:
        continue;
    now = now + 1
    print(now)
    print(u.get_full_name())
    f.write(str(u.id)+'\n')
    f.write(str(u.get_full_name())+'\n')
    f.write(str(len(fr)))
    for x in fr:
        f.write(' '+str(x.id))
    f.write('\n')
    for dayid in range(14,41):
        if dayid > 28:
            month = 3
            day = dayid - 28
        else:
            month = 2
            day = dayid
        f.write(str(month)+'-'+str(day)+'\n')
        r=Record.objects.filter(user=u,date=datetime.date(2013,month,day))
        if len(r) == 0:
            fuelScore = 0
        else:
            fuelScore = r[0].fuelscore
        pointEarned = 0
        for x in Amount.objects.filter(user=u):
            if x.time.date() == datetime.date(2013,month,day):
                if x.amount > 0: # not game-playing
                    pointEarned = pointEarned + x.amount
        pointSpent = 0
        winning = 0
        for x in Amount.objects.filter(user=u).filter(atype=3):
            if x.time.date() == datetime.date(2013,month,day):
                pointSpent = pointSpent - x.amount
        for s in Scale.objects.filter(active=False, winner=u):
            if s.get_end_time().date() == datetime.date(2013,month,day):
                winning = winning + s.money
        f.write(str(fuelScore)+' '+str(pointEarned)+' '+str(pointSpent)+' '+str(winning)+'\n')


f.close()
