from datetime import datetime, time, timedelta

from django.utils import timezone

from app.models import Appointment, DayOfWeek


DEFAULT_SLOT_MINUTES = 30
DEFAULT_WEEKDAY_START = time(9, 0)
DEFAULT_WEEKDAY_END = time(17, 0)


def get_effective_appointment_datetime(appointment):
    return appointment.confirmed_date or appointment.requested_date


def get_working_window(doctor, date_value):
    weekday = date_value.weekday()
    working_hours = doctor.working_hours.filter(day=weekday, is_available=True).first() if doctor else None

    if working_hours:
        return working_hours.start_time, working_hours.end_time

    if weekday in DayOfWeek.values and weekday < 5:
        return DEFAULT_WEEKDAY_START, DEFAULT_WEEKDAY_END

    return None


def iter_slot_datetimes(date_value, start_time, end_time, slot_minutes=DEFAULT_SLOT_MINUTES):
    start_dt = timezone.make_aware(datetime.combine(date_value, start_time))
    end_dt = timezone.make_aware(datetime.combine(date_value, end_time))
    current = start_dt

    while current + timedelta(minutes=slot_minutes) <= end_dt:
        yield current
        current += timedelta(minutes=slot_minutes)


def get_booked_slot_datetimes(doctor, exclude_appointment_id=None):
    appointments = Appointment.objects.filter(
        doctor=doctor,
        status__in=[Appointment.Status.REQUESTED, Appointment.Status.CONFIRMED],
    )

    if exclude_appointment_id:
        appointments = appointments.exclude(pk=exclude_appointment_id)

    booked_slots = set()
    for appointment in appointments:
        scheduled_dt = get_effective_appointment_datetime(appointment)
        if scheduled_dt:
            booked_slots.add(timezone.localtime(scheduled_dt))
    return booked_slots


def is_slot_available(doctor, slot_datetime, exclude_appointment_id=None):
    if slot_datetime < timezone.now():
        return False

    working_window = get_working_window(doctor, slot_datetime.date())
    if not working_window:
        return False

    start_time, end_time = working_window
    date_start = timezone.make_aware(datetime.combine(slot_datetime.date(), start_time))
    date_end = timezone.make_aware(datetime.combine(slot_datetime.date(), end_time))
    if slot_datetime < date_start or slot_datetime + timedelta(minutes=DEFAULT_SLOT_MINUTES) > date_end:
        return False

    booked_slots = get_booked_slot_datetimes(doctor, exclude_appointment_id=exclude_appointment_id)
    return timezone.localtime(slot_datetime) not in booked_slots


def build_schedule_map(doctor, start_date, days_ahead=14, slot_minutes=DEFAULT_SLOT_MINUTES, exclude_appointment_id=None):
    booked_slots = get_booked_slot_datetimes(doctor, exclude_appointment_id=exclude_appointment_id)
    schedule = {}

    for day_offset in range(days_ahead):
        current_date = start_date + timedelta(days=day_offset)
        working_window = get_working_window(doctor, current_date)
        if not working_window:
            continue

        slots = []
        start_time, end_time = working_window
        for slot_datetime in iter_slot_datetimes(current_date, start_time, end_time, slot_minutes=slot_minutes):
            slot_local = timezone.localtime(slot_datetime)
            slots.append(
                {
                    'value': slot_local.strftime('%H:%M'),
                    'label': slot_local.strftime('%I:%M %p'),
                    'iso': slot_local.isoformat(),
                    'available': slot_local >= timezone.localtime(timezone.now()) and slot_local not in booked_slots,
                }
            )

        if slots:
            schedule[current_date.isoformat()] = slots

    return schedule
