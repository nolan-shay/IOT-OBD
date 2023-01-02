import obd  
import time
import pyrebase    
from datetime import date
import boto3
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression

def getPrevDay(date):
    return date - timedelta(days = 1)
def getNextDay(date):
    return date + timedelta(days = 1)

def pushNotification(inputMessage):
  # Create an SNS client
  client = boto3.client(
    "sns",
    aws_access_key_id="",
    aws_secret_access_key="",
    region_name=""
  )
  Message = istanceDBvalue = db.child("cars").child("Acura").child("miles_since_clear").get().val()
  owner = db.child("cars").child("Acura").child("owner").get().val()
  number = db.child("accounts").child(owner).child("phoneNumber").get().val()
  # Send your sms message.
  client.publish(
    PhoneNumber="+1"+number,
    Message= inputMessage
  )

  print('Text sent!')

def insertExtraDaysFuel():
  today = date.today()
  todayStr = today.strftime("%Y-%m-%d")
  day = today
  print("today is: ", todayStr)
  last7Fuel = list(db.child("cars").child("Acura").child("last7Fuel").get().val().items())
  lastDBday = len(last7Fuel) - 1
  counter = 1
  while day.strftime("%Y-%m-%d") != last7Fuel[lastDBday][0] and counter <= 7:
      counter = counter + 1
      day = getPrevDay(day)

  if day != today and counter != 7:
      day = getNextDay(day)

  while day.strftime("%Y-%m-%d") != today.strftime("%Y-%m-%d"):
      last7Fuel.append((day.strftime("%Y-%m-%d"), 0))
      day = getNextDay(day)
      print("test1")

  if len(last7Fuel) > 6 and today.strftime("%Y-%m-%d") != lastDBday:
      last7Fuel = last7Fuel[ (len(last7Fuel)-6) : (len(last7Fuel))  ]

  responseDict = {

  }

  for val in last7Fuel :
      responseDict[ val[0] ] = val[1]

  print( last7Fuel )

  db.child("cars").child("Acura").update({"last7Fuel": responseDict})

def insertExtraDaysMiles():
  today = date.today()
  todayStr = today.strftime("%Y-%m-%d")
  day = today
  print("today is: ", todayStr)
  last7Miles = list(db.child("cars").child("Acura").child("last7Miles").get().val().items())
  lastDBday = len(last7Miles) - 1
  counter = 1
  while day.strftime("%Y-%m-%d") != last7Miles[lastDBday][0] and counter <= 7:
      counter = counter + 1
      day = getPrevDay(day)

  if day != today and counter != 7:
      day = getNextDay(day)

  while day.strftime("%Y-%m-%d") != today.strftime("%Y-%m-%d"):
      last7Miles.append((day.strftime("%Y-%m-%d"), 0))
      day = getNextDay(day)
      print("test1")

  if len(last7Miles) > 6 and today.strftime("%Y-%m-%d") != lastDBday:
      last7Miles = last7Miles[ (len(last7Miles)-6) : (len(last7Miles))  ]

  responseDict = {

  }

  for val in last7Miles :
      responseDict[ val[0] ] = val[1]

  print( last7Miles)

  db.child("cars").child("Acura").update({"last7Miles": responseDict})

# uses linear regression and the last 7 days of your driving to estimate the date when you will
def expectedDateOfOilChange():
    last7Miles = list( db.child("cars").child("Acura").child("last7Miles").get().val().items() ) ### list of tuples with dates and miles driven
    X = [ *range(0, len(last7Miles), 1) ]
    milesToOilChange = 2500
    ###print("X = ",X)
    Y = []
    sum = 0
    for val in last7Miles:
        sum = sum + val[1]
        Y.append( sum )
    ####print( "Y = ",Y )
    Y = np.array(Y).reshape(-1,1)
    X = np.array(X).reshape(-1,1)
    linear_regressor = LinearRegression()
    linear_regressor.fit(X, Y)
    X = 0
    Y_pred = 0
    numDays = 30
    if len(last7Miles) > 1:
      while Y_pred < ( milesToOilChange + sum ):
        Y_pred = linear_regressor.predict(np.array(X).reshape(1,-1))
        ####print (X, "  ", Y_pred[0][0])
        X = X + 1
      numDays = X - (len(last7Miles) - 1)
    today = date.today()
    todayStr = today.strftime("%Y-%m-%d")
    expectedDate = today + timedelta(days = numDays)
    expectedDateStr = expectedDate.strftime("%Y-%m-%d")
    print("Oil change expected on",expectedDateStr)
    return expectedDateStr

def expectedDateOfRefuel():
    last7Fuel = list( db.child("cars").child("Acura").child("last7Fuel").get().val().items() ) ### list of tuples with dates and miles driven
    X = [ *range(0, len(last7Fuel), 1) ]
    fuelPercent = 73
    #####print("X = ",X)
    Y = []
    sum = 0
    for val in last7Fuel:
        sum = sum + val[1]
        Y.append( sum )
    #####print( "Y = ",Y )
    Y = np.array(Y).reshape(-1,1)
    X = np.array(X).reshape(-1,1)
    linear_regressor = LinearRegression()
    linear_regressor.fit(X, Y)
    X = 0
    Y_pred = 0
    numDays = 7 ## default value
    if len(last7Fuel) > 1:
      while Y_pred < ( fuelPercent + sum ):
        Y_pred = linear_regressor.predict(np.array(X).reshape(1,-1))
        ###print (X, "  ", Y_pred[0][0])
        X = X + 1
      numDays = X - (len(last7Fuel) - 1)
    today = date.today()
    todayStr = today.strftime("%Y-%m-%d")
    expectedDate = today + timedelta(days = numDays)
    expectedDateStr = expectedDate.strftime("%Y-%m-%d")
    print("Refuel expected on ",expectedDateStr)
    return expectedDateStr


config = {
  "apiKey": "",
  "authDomain": "",
  "databaseURL": "",
  "projectId": "",
  "storageBucket": "",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

ports = obd.scan_serial()      # return list of valid USB or RF ports 
connection = obd.OBD(ports[0]) # connect to the first port in the list
print (connection.status())
#connection.query(obd.commands.CLEAR_DTC)

def checkErrorCodes():
  r = connection.query(obd.commands.GET_DTC).value
  print(r)

  if not r:
    print("you have no error codes") # no push notifications here
    responseDict = {
    }
    db.child("cars").child("Acura").child("DTC").update({"isEngineLightOn": False})
    db.child("cars").child("Acura").child("DTC").update({"codes": responseDict})
  else :
    print("you have error codes!!!") # push notifications here
    db.child("cars").child("Acura").child("DTC").update({"isEngineLightOn": True})
    ## check if there are more error codes
    DBcodes = db.child("cars").child("Acura").child("DTC").child("codes").get().val()

    messageString = "You have a new Error Code! \n\nCurrent Error Codes are:\n"

    for val in r :
      messageString += ( str(val[0]) + ": " + str(val[1]) + "\n" )

    if DBcodes == None:
      pushNotification(messageString)
      #print("You have a new Error Code!!")
    elif len(list(DBcodes.items())) < len(r):
      pushNotification(messageString)
      #print("You have a new Error Code!!")

    responseDict = {
    }
    for val in r :
      responseDict[ val[0] ] = val[1]
    
    db.child("cars").child("Acura").child("DTC").update({"codes": responseDict})

def updateFuel(fuelPercent):
  today = date.today()
  todayStr = today.strftime("%Y-%m-%d")
  last7Fuel = db.child("cars").child("Acura").child("last7Fuel").get()
  list1 = last7Fuel.val()

  # last7Fuel does not exist
  if list1 == None:
      db.child("cars").child("Acura").update({"last7Fuel": { todayStr : fuelPercent} })


  # non empty list
  else:

      #convert orderedDict to list to check whats happening
      workingList = list(list1.items())  # list

      if workingList[len(workingList)-1][0] == todayStr:  
          print("it is the same day")
          dbPercent = db.child("cars").child("Acura").child("last7Fuel").child(todayStr).get().val()
          db.child("cars").child("Acura").child("last7Fuel").update({todayStr: (dbPercent + fuelPercent) })
      else:
          # need to check if multiple days have passed
          insertExtraDaysFuel()
          if len(workingList) < 7:
              db.child("cars").child("Acura").child("last7Fuel").update({todayStr: fuelPercent})
          else:
              for x in range(len(workingList)):
                  if x != ( len(workingList) - 1 ):
                      workingList[x] = workingList[x+1]  # shift entries down one
                  else:
                      workingList[x] = (todayStr, fuelPercent)
              for val in workingList :
                  myDict[ val[0] ] = val[1]
              db.child("cars").child("Acura").update({"last7Fuel": myDict})

def updateMiles(milesTraveled):
  today = date.today()
  todayStr = today.strftime("%Y-%m-%d")
  last7Miles = db.child("cars").child("Acura").child("last7Miles").get()
  list1 = last7Miles.val()

  # last7Fuel does not exist
  if list1 == None:
      db.child("cars").child("Acura").update({"last7Miles": { todayStr : milesTraveled} })


  # non empty list
  else:
      #convert orderedDict to list to check whats happening
      workingList = list(list1.items())  # list

      if workingList[len(workingList)-1][0] == todayStr:  
          print("it is the same day")
          dbMiles = db.child("cars").child("Acura").child("last7Miles").child(todayStr).get().val()
          db.child("cars").child("Acura").child("last7Miles").update({todayStr: (dbMiles + milesTraveled) })
      else:
          # need to check if multiple days have passed
          insertExtraDaysMiles()
          if len(workingList) < 7:
              db.child("cars").child("Acura").child("last7Miles").update({todayStr: milesTraveled})
          else:
              for x in range(len(workingList)):
                  if x != ( len(workingList) - 1 ):
                      workingList[x] = workingList[x+1]  # shift entries down one
                  else:
                      workingList[x] = (todayStr, milesTraveled)
              myDict = {
              }
              for val in workingList :
                  myDict[ val[0] ] = val[1]
              db.child("cars").child("Acura").update({"last7Miles": myDict})

def stream_handler1(message):
    driving = db.child("cars").child("Acura").child("isDriving").get()
    if driving.val() == True:
      print("Started driving")

      #####  Here we are looking at Miles since the last time the codes were cleared in the car, this is also stored
      #####  in firebase so that we can add the miles to the odometer reading that the user gives us at the beginning
      beginningGasLevel = connection.query(obd.commands.FUEL_LEVEL).value.magnitude  ##gas level at beginning of trip
      distanceResult = connection.query(obd.commands.DISTANCE_SINCE_DTC_CLEAR)
      miles = distanceResult.value.magnitude * 0.621371   ## miles since dtc clear at beginning of trip
      distanceDBvalue = db.child("cars").child("Acura").child("miles_since_clear").get().val()
      odoVal = db.child("cars").child("Acura").child("odometer").get().val()
      if miles > distanceDBvalue:
        db.child("cars").child("Acura").update({"odometer": odoVal + (miles - distanceDBvalue) })
        oilMiles = db.child("cars").child("Acura").child("milesToOil").get().val()
        db.child("cars").child("Acura").update({"milesToOil": oilMiles - (miles - distanceDBvalue) })
        db.child("cars").child("Acura").update({"miles_since_clear": miles })
      elif miles < distanceDBvalue:
        db.child("cars").child("Acura").update({"miles_since_clear": miles })#maybe do something here?
      else:
        db.child("cars").child("Acura").update({"miles_since_clear": miles })  #maybe do something here?
      ### done making sure odometer and miles since driven are all fine and dandy

      ### maybe need to do somthing with a miles til oil change as well??

      ## does stuff while trip is still happening
      while driving.val() == True:
        time.sleep(3)
        driving = db.child("cars").child("Acura").child("isDriving").get()
        result = connection.query(obd.commands.SPEED)
        db.child("cars").child("Acura").update({"speed": (result.value.magnitude * 0.621371)})
        checkErrorCodes()
        print("Still driving")

      ##### this code happens once trip has ended
      gasLevel = connection.query(obd.commands.FUEL_LEVEL).value.magnitude
      print(gasLevel)
      if gasLevel < 20:
        pushNotification("You have below 20% Fuel!")
      print("Percent Fuel Used = ", (beginningGasLevel - gasLevel) )
      updateFuel(beginningGasLevel - gasLevel) 
      distanceDB = db.child("cars").child("Acura").child("miles_since_clear").get()
      distanceDBvalue = distanceDB.val()  # get previous miles since last clear
      db.child("cars").child("Acura").update({"fuel_level": gasLevel}) #get fuel level
      distanceResult = connection.query(obd.commands.DISTANCE_SINCE_DTC_CLEAR)
      miles = distanceResult.value.magnitude * 0.621371 # get miles since last clear
      odo = db.child("cars").child("Acura").child("odometer").get()
      print("miles traveled = ", (miles - distanceDBvalue) )
      updateMiles(miles - distanceDBvalue)
      odoVal = odo.val() # get odo value 
      #update the odometer in the database by taking the odo value and adding the miles_since_dtc_clear from
      # the end of the trip minus the miles_since_dtc_clear at the end of the trip
      db.child("cars").child("Acura").update({"odometer": odoVal + (miles - distanceDBvalue) })
      db.child("cars").child("Acura").update({"miles_since_clear": miles })
      oilMiles = db.child("cars").child("Acura").child("milesToOil").get().val()
      if oilMiles < 150:
        pushNotification("You are Due for an oil change")
      db.child("cars").child("Acura").update({"milesToOil": oilMiles - (miles - distanceDBvalue) })
      date1 = expectedDateOfOilChange()
      date2 = expectedDateOfRefuel()
      ##db.child("cars").child("Acura").update({"expectedOilDate": expectedDateOfOilChange() })
      ##db.child("cars").child("Acura").update({"expectedRefuelDate": expectedDateOfRefuel() })
      print("Stopped Driving")

checkErrorCodes()

## listen for isDriving value to change
my_stream1 = db.child("cars").child("Acura").child("isDriving").stream(stream_handler1)
