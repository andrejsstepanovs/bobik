import requests
import os
import zipfile
import tempfile
import icalendar
import datetime
import pytz
import numpy
import pickle
import recurring_ical_events
from ..state import ApplicationState as AppStatus
from ..my_print import print_text
from typing import Any


class Calendar:
    def __init__(self, state: AppStatus, options: dict):
        self.state = state
        self.calendars: dict[str, Any] = options
        self.cache_enabled: bool = options['cache']['enabled'] == "Yes"
        self.cache_file_path: str = options['cache']['file']
        if self.cache_enabled and self.cache_file_path == "":
            raise ValueError("Cache file not specified")

        self.events: list[dict] = []
        self.min_time: datetime.time = datetime.datetime.min.time()
        self.max_time: datetime.time = datetime.datetime.max.time()

    @staticmethod
    def get_files_by_prefix(directory_path: str, prefix: str) -> list[str]:
        files: list[str] = []
        for root, dirs, filenames in os.walk(directory_path):
            for filename in filenames:
                if filename.startswith(prefix):
                    files.append(os.path.join(root, filename))
        return files

    @staticmethod
    def sort_files_by_creation_time(files: list[str]) -> list[str]:
        return sorted(files, key=lambda x: os.path.getctime(x), reverse=True)

    def load_ics_files(self):
        for calendar in self.calendars["ics"]:
            if calendar["type"] == "url":
                try:
                    response = requests.get(calendar["url"])
                    response.raise_for_status()
                    calendar["ics"] = response.text
                except requests.exceptions.RequestException as e:
                    print(f"Error loading ICS file from URL: {e}")
            elif calendar["type"] == "zip_dir":
                files = self.get_files_by_prefix(calendar["directory"], calendar["file"])
                sorted_files = self.sort_files_by_creation_time(files)
                if len(sorted_files) == 0:
                    print_text(state=self.state, text=f"No files found for calendar {calendar['name']}")
                    continue
                ics_file_found = False
                for file in sorted_files:
                    print(f"Loading file: {file}")
                    file_name, file_extension = os.path.splitext(file)
                    if file_extension == ".zip":
                        try:
                            with zipfile.ZipFile(file_name+file_extension, 'r') as zip_file:
                                file_list: list[str] = zip_file.namelist()
                                if len(file_list) == 0:
                                    raise ValueError(f"No files found inside zip: {zip_file}")

                                with tempfile.TemporaryDirectory() as temp_dir:
                                    for inside_zip_file in file_list:
                                        if ics_file_found:
                                            break
                                        if not inside_zip_file.startswith(calendar["calendar_name"]):
                                            continue
                                        zip_file.extract(inside_zip_file, temp_dir)
                                        target = os.path.join(temp_dir, inside_zip_file)
                                        print(f"Extracting file: {inside_zip_file} into {target}")
                                        with open(target, encoding='utf-8', mode='r') as extracted_file:
                                            print("Reading")
                                            calendar["ics"] = extracted_file.read()
                                            print("Extracted")
                                            ics_file_found = True
                                            break
                        except zipfile.BadZipfile as e:
                            print(f"Error extracting ICS file from ZIP archive: {e}")
                    elif file_extension == ".ics":
                        if ics_file_found:
                            break
                        try:
                            with open(file_name+file_extension, encoding='utf-8', mode='r') as file:
                                calendar["ics"] = file.read()
                                ics_file_found = True
                        except UnicodeDecodeError as e:
                            print(f"Error reading ICS file: {e}")
                    else:
                        raise ValueError(f"Unknown file extension: {file_extension}")
                    if ics_file_found:
                        break
            else:
                raise ValueError("Unknown calendar type")

    def load_calendar_events(self) -> list[dict]:
        calendar_events: list[dict] = []
        for calendar in self.calendars["ics"]:
            print_text(state=self.state, text=f"Calendar: {calendar['name']} - {calendar['calendar_name']}")
            calendar_data = icalendar.Calendar.from_ical(calendar["ics"])

            earliest: datetime.datetime = None
            last: datetime.datetime = None
            for event in calendar_data.walk('VEVENT'):
                start = self.convert_to_datetime(event.get("DTSTART"), self.min_time)
                end = self.convert_to_datetime(event.get("DTEND"), self.max_time)
                if earliest is None or (start is not None and start < earliest):
                    earliest = start
                if last is None or (end is not None and end > last):
                    last = end

            events = recurring_ical_events.of(calendar_data).between(earliest, last)
            for event in events:
                if event.is_broken or len(event.errors) > 0:
                    raise ValueError(f"Event is broken: {event.errors}")

                attendee = event.get("ATTENDEE")
                attendees = []
                mail_prefix = "mailto:"
                if attendee is not None:
                    if isinstance(attendee, icalendar.vCalAddress):
                        attendees.append(str(attendee).replace(mail_prefix, ""))
                    else:
                        for x in attendee:
                            attendees.append(str(x).replace(mail_prefix, ""))

                start = self.convert_to_datetime(event.get("DTSTART"), self.min_time)
                end = self.convert_to_datetime(event.get("DTEND"), self.max_time)
                if end is None:
                    end: datetime.datetime = start
                    end: datetime.datetime = datetime.datetime.combine(end, datetime.datetime.max.time())
                    end: datetime.datetime = end.replace(tzinfo=datetime.timezone.utc)
                if start is None:
                    raise ValueError("Event start or end is None")

                full_day = False
                if start is not None and end is not None:
                    diff = end - start
                    full_day = diff.days > 1 or diff.seconds >= 86399

                organizer = str(event.get("ORGANIZER")).replace("mailto:", "")
                if organizer == "None":
                    organizer = ""

                event_dict = {
                    "private": calendar["private"],
                    "calendar": calendar["calendar_name"],
                    "name": calendar["name"],
                    "origin": calendar["origin"],
                    "summary": str(event.get("SUMMARY")),
                    "start": start,
                    "end": end,
                    "full_day": full_day,
                    "organizer": organizer,
                    "attendees": attendees,
                    "description": str(event.get("DESCRIPTION")),
                    "status": str(event.get("STATUS")),
                }
                calendar_events.append(event_dict)
        return calendar_events

    def convert_to_datetime(self, date_value: icalendar.vDDDTypes, suffix_time_if_date: datetime.time) -> datetime.datetime:
        datetime_value: datetime.datetime = date_value.dt if date_value is not None else None
        if datetime_value and type(datetime_value) is datetime.date:
            datetime_value: datetime.datetime = datetime.datetime.combine(datetime_value, suffix_time_if_date)
            datetime_value: datetime.datetime = datetime_value.replace(tzinfo=datetime.timezone.utc)
        return datetime_value

    def remove_duplicates(self, dict_list: list[dict]) -> list[dict]:
        seen: set = set()
        unique_list: list[dict] = []
        for d in dict_list:
            key_values = (d['summary'], d['start'], d['end'], d['description'])
            if key_values not in seen:
                seen.add(key_values)
                unique_list.append(d)
        return unique_list

    def filter_and_sort_events(self) -> list[dict]:
        sort_by: str = "start"
        days: int = int(self.calendars["days"])

        filter_status: list[str] = self.calendars['filter_status']
        ignore_names: list[str] = self.calendars['ignore_event_names']
        filter_emails: list[str] = self.calendars["emails"]

        filter_from_time: datetime.datetime = datetime.datetime.now()
        filter_from_time: datetime.datetime = datetime.datetime.combine(filter_from_time.date(), self.min_time)

        filter_till_time: datetime.datetime = filter_from_time + datetime.timedelta(days=days)
        filter_till_time: datetime.datetime = datetime.datetime.combine(filter_till_time.date(), self.max_time)

        filter_till_time: datetime.datetime = filter_till_time.replace(tzinfo=pytz.UTC)
        filter_from_time: datetime.datetime = filter_from_time.replace(tzinfo=pytz.UTC)

        filtered_events: list[dict] = []
        for event in self.events:
            email_found = len(filter_emails) == 0
            if not email_found:
                if event["organizer"] == '' and len(event["attendees"]) == 0:
                    email_found = True
                else:
                    if event['organizer'] in filter_emails:
                        email_found = True
                    elif len(event['attendees']) > 0:
                        intersection = numpy.intersect1d(filter_emails, event["attendees"])
                        email_found = len(intersection) > 0
            if not email_found:
                continue

            if len(filter_status) > 0 and event['status'] not in filter_status:
                continue

            if len(ignore_names) > 0 and event['summary'] in ignore_names:
                continue

            s = event["start"]
            e = event["end"]
            a = filter_from_time
            b = filter_till_time
            if s <= a <= e or s <= b <= e or a <= s <= b or a <= e <= b:
                filtered_events.append(event)

        unique: list[dict] = self.remove_duplicates(filtered_events)
        sorted_events: list[dict] = sorted(unique, key=lambda x: x[sort_by])
        return sorted_events

    def get_events(self) -> list[dict]:
        if self.cache_enabled and os.path.exists(self.cache_file_path):
            with open(self.cache_file_path, mode='rb') as f:
                self.events = pickle.load(f)
                return self.events

        self.load_ics_files()
        self.events = self.load_calendar_events()

        if self.cache_enabled:
            try:
                with open(self.cache_file_path, mode='wb') as f:
                    pickle.dump(self.events, f)
            except Exception as e:
                if os.path.exists(self.cache_file_path):
                    os.remove(self.cache_file_path)
                raise e

        return self.events
