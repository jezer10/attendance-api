import { createClient } from "npm:@supabase/supabase-js@2";
import { DateTime } from "npm:luxon@3.4.4";
type AttendanceRecord = {
  user_id: string;
  is_active: boolean;
  timezone: string;
  random_window_minutes: number | null;
  entry_enabled: boolean;
  entry_local_time: string | null;
  entry_days: string[] | null;
  exit_enabled: boolean;
  exit_local_time: string | null;
  exit_days: string[] | null;
};

type AttendanceEventInsert = {
  user_id: string;
  event_type: "entry" | "exit";
  event_date: string;
  scheduled_for: string;
  timezone: string;
  base_local_time: string;
  random_window_minutes: number;
  offset_minutes: number;
};

const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
const ATTENDANCE_API_URL = Deno.env.get("ATTENDANCE_API_URL");
const ATTENDANCE_API_KEY = Deno.env.get("ATTENDANCE_API_KEY");

if (
  !SUPABASE_URL ||
  !SUPABASE_SERVICE_ROLE_KEY ||
  !ATTENDANCE_API_URL ||
  !ATTENDANCE_API_KEY
) {
  throw new Error("Missing Supabase environment variables.");
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    persistSession: false,
  },
});

const DAY_NAMES = new Set([
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
]);

function normalizeTimezone(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return "UTC";
  }

  const parts = trimmed.split(" ");
  for (let i = parts.length - 1; i >= 0; i -= 1) {
    if (parts[i].includes("/")) {
      return parts[i];
    }
  }

  return trimmed;
}

function safeZone(timezone: string): string {
  const zone = normalizeTimezone(timezone);
  const test = DateTime.utc().setZone(zone);
  return test.isValid ? zone : "UTC";
}

function parseTime(
  value: string,
): { hour: number; minute: number; second: number } {
  const [hour, minute, second] = value.split(":").map((part) => Number(part));
  return {
    hour: Number.isFinite(hour) ? hour : 0,
    minute: Number.isFinite(minute) ? minute : 0,
    second: Number.isFinite(second) ? second : 0,
  };
}

function hashString(value: string): number {
  let hash = 0;
  for (const char of value) {
    hash = (hash * 31 + char.charCodeAt(0)) | 0;
  }
  return Math.abs(hash);
}

function computeOffsetMinutes(
  userId: string,
  date: string,
  eventType: "entry" | "exit",
  windowMinutes: number,
): number {
  if (windowMinutes <= 0) {
    return 0;
  }
  const hash = hashString(`${userId}:${date}:${eventType}`);
  const range = windowMinutes * 2 + 1;
  return (hash % range) - windowMinutes;
}

function matchesDay(windowDays: string[] | null, today: string): boolean {
  if (!windowDays || windowDays.length === 0) {
    return true;
  }
  return windowDays.some((day) => day && day.toLowerCase() === today);
}

function scheduleEvent(
  record: AttendanceRecord,
  eventType: "entry" | "exit",
  localNow: DateTime,
): AttendanceEventInsert | null {
  const days = eventType === "entry" ? record.entry_days : record.exit_days;
  const baseTime = eventType === "entry"
    ? record.entry_local_time
    : record.exit_local_time;

  if (!baseTime) {
    return null;
  }

  const localDayName = localNow.toFormat("cccc").toLowerCase();
  console.log({ days, baseTime, localDayName });
  if (!DAY_NAMES.has(localDayName)) {
    return null;
  }

  if (!matchesDay(days, localDayName)) {
    return null;
  }

  const windowMinutes = Math.max(record.random_window_minutes ?? 0, 0);
  const localDate = localNow.toISODate();
  if (!localDate) {
    return null;
  }

  const { hour, minute, second } = parseTime(baseTime);
  const zone = localNow.zoneName;
  const baseLocal = DateTime.fromObject(
    {
      year: localNow.year,
      month: localNow.month,
      day: localNow.day,
      hour,
      minute,
      second,
    },
    { zone },
  );

  if (!baseLocal.isValid) {
    return null;
  }

  const offsetMinutes = computeOffsetMinutes(
    record.user_id,
    localDate,
    eventType,
    windowMinutes,
  );
  let scheduledLocal = baseLocal.plus({ minutes: offsetMinutes });

  const startOfDay = baseLocal.startOf("day");
  const endOfDay = baseLocal.endOf("day");
  if (scheduledLocal < startOfDay) {
    scheduledLocal = startOfDay;
  }
  if (scheduledLocal > endOfDay) {
    scheduledLocal = endOfDay;
  }

  if (localNow < scheduledLocal) {
    return null;
  }

  return {
    user_id: record.user_id,
    event_type: eventType,
    event_date: localDate,
    scheduled_for: scheduledLocal.toUTC().toISO(),
    timezone: record.timezone,
    base_local_time: baseTime,
    random_window_minutes: windowMinutes,
    offset_minutes: offsetMinutes,
  };
}

Deno.serve(async () => {
  const { data: records, error } = await supabase
    .from("attendance_records")
    .select(
      [
        "user_id",
        "is_active",
        "timezone",
        "random_window_minutes",
        "entry_enabled",
        "entry_local_time",
        "entry_days",
        "exit_enabled",
        "exit_local_time",
        "exit_days",
      ].join(","),
    );

  if (error) {
    return new Response(
      JSON.stringify({
        detail: "Failed to load attendance records",
        error: error.message,
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  const inserts: AttendanceEventInsert[] = [];

  for (const record of records as AttendanceRecord[]) {
    if (!record.is_active) {
      continue;
    }

    const zone = safeZone(record.timezone);
    const localNow = DateTime.utc().setZone(zone);

    if (record.entry_enabled) {
      console.log("entry_enabled");
      const entryEvent = scheduleEvent(record, "entry", localNow);
      if (entryEvent) {
        inserts.push(entryEvent);
      }
    }

    if (record.exit_enabled) {
      const exitEvent = scheduleEvent(record, "exit", localNow);
      if (exitEvent) {
        inserts.push(exitEvent);
      }
    }
  }

  let inserted = 0;
  if (inserts.length > 0) {
    const { error: insertError, data } = await supabase
      .from("attendance_events")
      .upsert(inserts, {
        onConflict: "user_id,event_date,event_type",
        ignoreDuplicates: true,
      })
      .select("id,user_id,event_type");

    if (insertError) {
      return new Response(
        JSON.stringify({
          detail: "Failed to persist attendance events",
          error: insertError.message,
        }),
        {
          status: 500,
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    const insertedRows = (data ?? []) as {
      user_id: string;
      event_type: "entry" | "exit";
    }[];
    inserted = insertedRows.length;

    if (insertedRows.length > 0) {
      await Promise.all(
        insertedRows.map(async (row) => {
          const response = await fetch(
            `${ATTENDANCE_API_URL}/api/v1/attendance/mark/internal`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                "X-Internal-Key": ATTENDANCE_API_KEY,
              },
              body: JSON.stringify({
                eventType: row.event_type,
                userId: row.user_id,
              }),
            },
          );

          if (!response.ok) {
            const body = await response.text();
            console.error(
              "Failed to mark attendance",
              row.user_id,
              row.event_type,
              response.status,
              body,
            );
          }
        }),
      );
    }
  }

  return new Response(
    JSON.stringify({
      detail: "Attendance schedule processed",
      considered: records.length,
      candidates: inserts.length,
      inserted,
    }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    },
  );
});
