import datetime
import zoneinfo

# pip install astral
from astral.sun import sun
from astral import LocationInfo

# ------------------------------------------------------------------------
# Config start
# Set your location here
# Only latitude, longitude and timezone is important
# ------------------------------------------------------------------------
#city = LocationInfo("Berlin", "Germany", "Europe/Berlin", 52.50, 13.37)
#city = LocationInfo("Verl",   "Germany", "Europe/Berlin", 51.81, 8.42)
city = LocationInfo("Kassel",  "Germany", "Europe/Berlin", 51.31, 9.48)
timezone = zoneinfo.ZoneInfo("Europe/Berlin")
OUTPUT_AS_UTC = True
# ------------------------------------------------------------------------
# Config end
# ------------------------------------------------------------------------

month_name    = ["unused", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",]
days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# --------------------------------------------------------------------
# Some outputs to fiddle around
# --------------------------------------------------------------------
print((
    f"Information for {city.name}/{city.region}\n"
    f"Timezone: {city.timezone}\n"
    f"Latitude: {city.latitude:.02f}; Longitude: {city.longitude:.02f}\n"
))

today_day  = datetime.datetime.today().day
today_month = datetime.datetime.today().month

if OUTPUT_AS_UTC:
    print("All outputs as UTC for", today_day, "of", month_name[today_month])
    s = sun(city.observer, date=datetime.date(2024, today_month, today_day))
else:
    print("All outputs in local time incl. daylight saving time")
    s = sun(city.observer, date=datetime.date(2022, today_month, today_day), tzinfo=timezone)

print((
    f'Dawn:    {s["dawn"]}\n'
    f'Sunrise: {s["sunrise"]}\n'
    f'Noon:    {s["noon"]}\n'
    f'Sunset:  {s["sunset"]}\n'
    f'Dusk:    {s["dusk"]}\n'
))

# --------------------------------------------------------------------
# Start of creation of PLC functions
# --------------------------------------------------------------------


def date_to_plc_time(date):
    return "TOD#" +   '{:02d}'.format(date.hour)   + ":"  + '{:02d}'.format(date.minute) + ":"  + '{:02d}'.format(date.second)

def create_plc_array(varname, timeofday):
    
    out = "// All times in UTC for " + city.name + " (Latitude: " + str(city.latitude) + "; Longitude: " + str(city.longitude) +  ")\r"
    out = out + "// Each month has 31 days in this array. Days > number of days in this month contain the value of the last day of month\r"
    out = out + "// Function created with: https://github.com/otti/SunRiseSunSet\r"
    out = out + varname + " : ARRAY[1..12] OF ARRAY[1..31] OF TOD := \r   [\r      //         "

    for day in range(1, 32):
        out = out + '{:02d}'.format(day) + "            "
    out = out + "\r"

    for month in range(1,13):
        out = out + "      ["
        for day in range(1, 32):
            if day <= days_in_month[month]:
                s = sun(city.observer, date=datetime.date(2023, month, day)) # <-- 2023 not a leap year
            else:
                s = sun(city.observer, date=datetime.date(2023, month, days_in_month[month])) # <-- create always 31 entreis for each month

            out = out + date_to_plc_time(s[timeofday])

            if day != 31:
                out = out + ", "

        if month != 12:
            out = out + "],"
        else:
            out = out + "] "

        out = out + " //" + month_name[month] + "\r"

    out = out + "   ];"

    return out

def CreatePlcFunction(time_of_day, function_name):
    f = open("_Template.TcPOU", "r")
    sFunctionBody = f.read()
    f.close()

    sArray = create_plc_array(time_of_day, time_of_day)

    sFunctionBody = sFunctionBody.replace("(*FUNCTION_NAME*)", function_name)
    sFunctionBody = sFunctionBody.replace("(*VAR*)", sArray)
    sFunctionBody = sFunctionBody.replace("(*VARNAME*)", time_of_day)
    
    f = open(function_name + ".TcPOU", "w")
    f.write(sFunctionBody)
    f.close()


CreatePlcFunction("dawn",    "fGetTimeOfDawn")
CreatePlcFunction("sunrise", "fGetTimeOfSunrise")
CreatePlcFunction("noon",    "fGetTimeOfNoon")
CreatePlcFunction("sunset",  "fGetTimeOfSunset")
CreatePlcFunction("dusk",    "fGetTimeOfDusk")



