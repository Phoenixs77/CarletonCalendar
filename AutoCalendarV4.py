import re
import datetime
import uuid
from zoneinfo import ZoneInfo  # Requires Python 3.9+

# ---------------------------
# Course Parsing Section
# ---------------------------

class Course:
    def __init__(self, className, instructor, meetingType, time, days, location, dateRange):
        self.className = className
        self.instructor = instructor if instructor else "TBA"
        self.meetingType = meetingType.lower()
        self.time = time
        self.days = days
        self.location = location if location else "TBA"
        self.dateRange = dateRange

    def __repr__(self):
        return (f"\nCourse Information:\n"
                f"  Class Name  : {self.className}\n"
                f"  Instructor  : {self.instructor}\n"
                f"  Type        : {self.meetingType.capitalize()}\n"
                f"  Time        : {self.time}\n"
                f"  Days        : {self.days}\n"
                f"  Location    : {self.location}\n"
                f"  Date Range  : {self.dateRange}\n")

def parseCourses(text):
    courses = []
    blocks = text.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        className = lines[0].strip()
        instructor = None
        meetingInfoLine = None
        headerLine = None

        for line in lines:
            if "Assigned Instructor:" in line:
                parts = line.split("Assigned Instructor:")
                instructor = parts[1].strip() if len(parts) > 1 else "TBA"

        scheduledIndex = None
        for i, line in enumerate(lines):
            if "Scheduled Meeting Times" in line:
                scheduledIndex = i
                break

        if scheduledIndex is not None:
            if scheduledIndex + 1 < len(lines):
                headerLine = lines[scheduledIndex + 1].strip()
            if scheduledIndex + 2 < len(lines):
                meetingInfoLine = lines[scheduledIndex + 2].strip()

        timeVal = days = location = dateRange = meetingType = "TBA"

        if meetingInfoLine:
            if "\t" in meetingInfoLine:
                headers = headerLine.split("\t")
                data = meetingInfoLine.split("\t")
                try:
                    timeVal = data[headers.index("Time")].strip()
                    days = data[headers.index("Days")].strip()
                    location = data[headers.index("Where")].strip()
                    dateRange = data[headers.index("Date Range")].strip()
                    meetingType = data[headers.index("Schedule Type")].strip().lower()
                except ValueError:
                    parts = re.split(r'\s{2,}', meetingInfoLine)
                    if len(parts) >= 7:
                        timeVal = parts[1].strip()
                        days = parts[2].strip()
                        location = parts[3].strip()
                        dateRange = parts[4].strip()
                        meetingType = parts[5].strip().lower()
            else:
                parts = re.split(r'\s{2,}', meetingInfoLine)
                if len(parts) >= 7:
                    timeVal = parts[1].strip()
                    days = parts[2].strip()
                    location = parts[3].strip()
                    dateRange = parts[4].strip()
                    meetingType = parts[5].strip().lower()

        course = Course(className, instructor, meetingType, timeVal, days, location, dateRange)
        courses.append(course)

    return courses

# ---------------------------
# Helper Functions for ICS Conversion
# ---------------------------

def parseDays(daysStr):
    """
    Converts a days string (each day as a single letter) into a list of ICS BYDAY values.
    Mapping:
      M -> MO, T -> TU, W -> WE, R -> TH, F -> FR, S -> SA, U -> SU
    Example: "MW" becomes ["MO", "WE"]
    """
    mapping = {
        'M': 'MO',
        'T': 'TU',
        'W': 'WE',
        'R': 'TH',  # R for Thursday
        'F': 'FR',
        'S': 'SA',  # S for Saturday (assumed)
        'U': 'SU'
    }
    result = []
    for ch in daysStr.strip().upper():
        if ch in mapping:
            result.append(mapping[ch])
    return result

def parseDateRange(dateRangeStr):
    """
    Expects a date range in one of the following formats:
      "MM/DD/YYYY - MM/DD/YYYY"
      "Mon DD, YYYY - Mon DD, YYYY" (e.g., "Jan 06, 2025 - Apr 08, 2025")
    Returns a tuple (startDate, endDate) as datetime.date objects.
    """
    try:
        startStr, endStr = [s.strip() for s in dateRangeStr.split("-")]
        for fmt in ("%m/%d/%Y", "%b %d, %Y"):
            try:
                startDate = datetime.datetime.strptime(startStr, fmt).date()
                endDate = datetime.datetime.strptime(endStr, fmt).date()
                return startDate, endDate
            except ValueError:
                continue
        return None, None
    except Exception:
        return None, None

def parseTimeRange(timeStr, eventDate, tz):
    """
    Expects a time range in the format "HH:MM am - HH:MM pm" (case-insensitive).
    Returns a tuple of timezone-aware datetime objects (startDateTime, endDateTime)
    using eventDate and the provided tz.
    """
    try:
        # Ensure AM/PM parts are uppercase
        startTimeStr, endTimeStr = [s.strip().upper() for s in timeStr.split("-")]
        startDT = datetime.datetime.strptime(f"{eventDate.strftime('%m/%d/%Y')} {startTimeStr}", "%m/%d/%Y %I:%M %p")
        endDT = datetime.datetime.strptime(f"{eventDate.strftime('%m/%d/%Y')} {endTimeStr}", "%m/%d/%Y %I:%M %p")
        startDT = startDT.replace(tzinfo=tz)
        endDT = endDT.replace(tzinfo=tz)
        return startDT, endDT
    except Exception:
        return None, None

def getFirstOccurrence(startDate, bydayList):
    """
    Given a starting date and a list of ICS BYDAY values,
    returns the first date on or after startDate that matches one of the weekdays.
    """
    weekdayMapping = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
    targetWeekdays = [weekdayMapping[day] for day in bydayList if day in weekdayMapping]
    current = startDate
    for _ in range(7):
        if current.weekday() in targetWeekdays:
            return current
        current += datetime.timedelta(days=1)
    return startDate

def formatDateTime(dt):
    """
    Formats a datetime object in the ICS date-time format: YYYYMMDDTHHMMSS
    """
    return dt.strftime("%Y%m%dT%H%M%S")

def generateVTimezone(tzid):
    """
    Returns a VTIMEZONE block for the given tzid.
    This example uses America/New_York definitions.
    """
    return "\n".join([
        "BEGIN:VTIMEZONE",
        f"TZID:{tzid}",
        "X-LIC-LOCATION:America/New_York",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:-0500",
        "TZOFFSETTO:-0400",
        "TZNAME:EDT",
        "DTSTART:19700308T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:-0400",
        "TZOFFSETTO:-0500",
        "TZNAME:EST",
        "DTSTART:19701101T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
        "END:STANDARD",
        "END:VTIMEZONE"
    ])

# ---------------------------
# ICS Generation Section
# ---------------------------

def generateICS(courses, calendarName="Courses Calendar"):
    """
    Converts a list of Course objects into an ICS file content.
    Each course becomes a repeating event.
    """
    tzid = "America/New_York"
    nytz = ZoneInfo(tzid)
    
    lines = []
    lines.append("BEGIN:VCALENDAR")
    lines.append("VERSION:2.0")
    lines.append("PRODID:-//Course ICS Converter//EN")
    lines.append(f"X-WR-CALNAME:{calendarName}")
    # Insert VTIMEZONE block for the timezone
    lines.append(generateVTimezone(tzid))
    
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    dtStamp = formatDateTime(now.astimezone(nytz))

    for course in courses:
        # Skip courses missing required scheduling info.
        if course.dateRange == "TBA" or course.time == "TBA" or course.days == "TBA":
            continue

        startDate, endDate = parseDateRange(course.dateRange)
        if not startDate or not endDate:
            continue

        # Parse meeting days (each letter represents a day).
        bydayList = parseDays(course.days)
        if not bydayList:
            continue

        # Determine the first occurrence on or after the start date.
        firstOccurrenceDate = getFirstOccurrence(startDate, bydayList)
        startDT, endDT = parseTimeRange(course.time, firstOccurrenceDate, nytz)
        if not startDT or not endDT:
            continue

        # Build the RRULE string.
        # Use the course end date with the event's start time for the UNTIL value.
        untilDT = datetime.datetime.combine(endDate, startDT.timetz())
        untilDT = untilDT.replace(tzinfo=nytz)
        rrule = f"FREQ=WEEKLY;UNTIL={formatDateTime(untilDT)};BYDAY={','.join(bydayList)}"

        uid = f"{uuid.uuid4()}@coursecalendar"
        description = f"Type: {course.meetingType.capitalize()}\\nInstructor: {course.instructor}"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{dtStamp}")
        lines.append(f"DTSTART;TZID={tzid}:{formatDateTime(startDT)}")
        lines.append(f"DTEND;TZID={tzid}:{formatDateTime(endDT)}")
        lines.append(f"RRULE:{rrule}")
        lines.append(f"SUMMARY:{course.className}")
        lines.append(f"DESCRIPTION:{description}")
        lines.append(f"LOCATION:{course.location}")
        lines.append("END:VEVENT")
    
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

# ---------------------------
# Main Execution Section
# ---------------------------
if __name__ == "__main__":
    # Read the content from the provided file
    filePath = "test.txt"
    with open(filePath, "r", encoding="utf-8") as file:
        fileContent = file.read()

    # Parse the courses from the text file
    parsedCourses = parseCourses(fileContent)

    # Uncomment below for debugging:
    # for course in parsedCourses:
    #     print(course)

    # Generate the ICS file content
    icsContent = generateICS(parsedCourses)

    # Write the ICS content to a file
    icsFilePath = "courses.ics"
    with open(icsFilePath, "w", encoding="utf-8") as icsFile:
        icsFile.write(icsContent)

    print(f"ICS file has been generated and saved to {icsFilePath}.")
