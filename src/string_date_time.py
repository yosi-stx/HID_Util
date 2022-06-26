# file: string_date_time.py
# usage: 
# >>>>  from string_date_time import get_date_time
# >>>>  s1= get_date_time()


from datetime import datetime

# def string_date_time():
def get_date_time():
    dt = datetime.now()
    # 'The date is %s_%s_%s' % (dt.year,dt.month, dt.day )
    # >> result:
    # 'The date is 2021_3_9'

    s1=str(dt)
    # >>> s1
    # '2021-03-09 21:52:26.091822'

    date=str(dt.date())
    # print(date)
    date = date.replace("-", "_")


    time=str(dt.time())
    # print(time)
    y = time.replace(":", "_")
    # print(y)

    time1=s1[11:13]+'_'+s1[14:16]
    #time1=str(dt.hour)+'_'+str(dt.minute)

    # print(time1)

    date_time=date+'__'+time1
    # print("string date_time:",date_time)
    return date_time

# usage: 
# >>>>  from string_date_time import get_date
# >>>>  s1= get_date()
def get_date():
    dt = datetime.now()
    # 'The date is %s_%s_%s' % (dt.year,dt.month, dt.day )
    # >> result:
    # 'The date is 2021_3_9'

    s1=str(dt)
    # >>> s1
    # '2021-03-09 21:52:26.091822'

    date=str(dt.date())
    # print(date)
    date = date.replace("-", "_")


    time=str(dt.time())
    # print(time)
    y = time.replace(":", "_")
    # print(y)

    return date
    
# In [7]: print(datetime.now())
# 2021-12-20 17:28:28.520957

def get_date_time_sec():
    dt = datetime.now()
    # 'The date is %s_%s_%s' % (dt.year,dt.month, dt.day )
    # >> result:
    # 'The date is 2021_3_9'

    s1=str(dt)
    # >>> s1
    # '2021-03-09 21:52:26.091822'

    date=str(dt.date())
    # print(date)
    date = date.replace("-", "_")


    time=str(dt.time())
    # print(time)
    y = time.replace(":", "_")
    # print(y)

    time1=s1[11:13]+'_'+s1[14:16]+'_'+s1[17:19]
    #time1=str(dt.hour)+'_'+str(dt.minute)+'_'+str(dt.second)

    # print(time1)

    date_time=date+'__'+time1
    # print("string date_time:",date_time)
    return date_time
    
def get_date_time_milisec():
    dt = datetime.now()
    # 'The date is %s_%s_%s' % (dt.year,dt.month, dt.day )
    # >> result:
    # 'The date is 2021_3_9'

    s1=str(dt)
    # >>> s1
    # '2021-03-09 21:52:26.091822'

    date=str(dt.date())
    # print(date)
    date = date.replace("-", "_")


    time=str(dt.time())
    # print(time)
    y = time.replace(":", "_")
    # print(y)

    time1=s1[11:13]+'_'+s1[14:16]+'_'+s1[17:19]+'.'+s1[20:23]
    #time1=str(dt.hour)+'_'+str(dt.minute)+'_'+str(dt.second)

    # print(time1)

    date_time=date+'__'+time1
    # print("string date_time:",date_time)
    return date_time
    

def get_time():
    dt = datetime.now()
    # 'The date is %s_%s_%s' % (dt.year,dt.month, dt.day )
    # >> result:
    # 'The date is 2021_3_9'

    # time1=str(dt.hour)+'_'+str(dt.minute)+':'+str(dt.second)
    h = "%02d" %dt.hour
    m = "%02d" %dt.minute
    s = "%02d" %dt.second
    time1 = h +':'+ m +':'+ s
    # print(time1)

    date_time = time1
    # print("string date_time:",date_time)
    return date_time


'''    
# comment:
# this file is at location : C:\Python37\YG_try\string_date_time.py
# to add C:\Python37\YG_try\
# into the python path, I need to run the following lines each time I open Idle:
// to add to python path:
import sys
sys.path.append("C:\Python37\YG_try")

'''

def main():
    print("this is a library file with functions:\n \
    get_time() get_date_time() get_date() get_date_time_sec() get_date_time_milisec() get_time()")
    date_time = get_time()
    print("\n\n example:   string date_time:",date_time)

if __name__ == "__main__":
    main()