from fuel.models import *

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
