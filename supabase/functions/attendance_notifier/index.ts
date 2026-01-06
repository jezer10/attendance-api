import { createClient } from "npm:@supabase/supabase-js@2";
import { DateTime } from "npm:luxon@3.4.4";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

const WHATSAPP_TEMPLATE_URL = Deno.env.get("WHATSAPP_TEMPLATE_URL");
const WHATSAPP_TEMPLATE_NAME = Deno.env.get("WHATSAPP_TEMPLATE_NAME") ??
  "ticket_order";
const WHATSAPP_LANGUAGE_CODE = Deno.env.get("WHATSAPP_LANGUAGE_CODE") ?? "en";
const WHATSAPP_AUTH_LOGIN_URL = Deno.env.get("WHATSAPP_AUTH_LOGIN_URL");
const WHATSAPP_AUTH_REFRESH_URL = Deno.env.get("WHATSAPP_AUTH_REFRESH_URL");
const WHATSAPP_AUTH_USERNAME = Deno.env.get("WHATSAPP_AUTH_USERNAME");
const WHATSAPP_AUTH_PASSWORD = Deno.env.get("WHATSAPP_AUTH_PASSWORD");

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  throw new Error("Missing Supabase environment variables.");
}
if (
  !WHATSAPP_TEMPLATE_URL || !WHATSAPP_AUTH_LOGIN_URL ||
  !WHATSAPP_AUTH_REFRESH_URL || !WHATSAPP_AUTH_USERNAME ||
  !WHATSAPP_AUTH_PASSWORD
) {
  throw new Error("Missing WhatsApp provider environment variables.");
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

type AttendanceEvent = {
  id: string;
  user_id: string;
  scheduled_for: string;
  timezone: string;
};

type AttendanceRecord = {
  user_id: string;
  phone_number: string | null;
  location_address: string;
  location_latitude: number;
  location_longitude: number;
};

type TokenPair = {
  access_token: string;
  refresh_token: string;
};

let accessToken: string | null = null;
let refreshToken: string | null = null;

function toWaId(phoneNumber: string): string {
  return phoneNumber.replace(/^\+/, "");
}

function normalizeTimezone(value: string): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return "UTC";

  // 1) Preferir zona IANA si viene incluida (ej: "America/Lima")
  const parts = trimmed.split(/\s+/);
  for (let i = parts.length - 1; i >= 0; i -= 1) {
    const token = parts[i].replace(/[()]/g, "");
    if (token.includes("/")) return token;
  }

  // 2) Fallback: si solo viene offset tipo UTC-05:00 o -05:00
  const m = trimmed.match(/(UTC)?([+-]\d{2}:\d{2})/i);
  if (m?.[2]) return `UTC${m[2]}`;

  // 3) Último recurso
  return "UTC";
}

function safeZone(timezone: string): string {
  const zone = normalizeTimezone(timezone);
  const test = DateTime.utc().setZone(zone);
  return test.isValid ? zone : "UTC";
}

export function formatLocalTime(iso: string, timezone: string) {
  const zone = safeZone(timezone);

  // Nota: su ISO ya trae +00:00, así que Luxon lo interpreta bien.
  // Aun así, forzar a UTC primero es consistente y evita ambigüedades.
  const dtUtc = DateTime.fromISO(iso).toUTC();
  const local = dtUtc.setZone(zone);

  return {
    date: local.toFormat("dd/LL/yyyy"),
    time: local.toFormat("HH:mm"),
    zone, // opcional: útil para depurar/inspección
    isValid: local.isValid, // opcional
  };
}

async function login(): Promise<TokenPair> {
  const auth = btoa(`${WHATSAPP_AUTH_USERNAME}:${WHATSAPP_AUTH_PASSWORD}`);
  const response = await fetch(WHATSAPP_AUTH_LOGIN_URL!, {
    method: "POST",
    headers: { Authorization: `Basic ${auth}` },
  });

  console.log({ WHATSAPP_AUTH_USERNAME, WHATSAPP_AUTH_PASSWORD });

  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }

  const data = await response.json();
  if (!data.access_token || !data.refresh_token) {
    throw new Error("Login response missing tokens");
  }

  return { access_token: data.access_token, refresh_token: data.refresh_token };
}

async function refresh(): Promise<TokenPair | null> {
  if (!refreshToken) {
    return null;
  }

  const response = await fetch(WHATSAPP_AUTH_REFRESH_URL!, {
    method: "POST",
    headers: { Authorization: `Bearer ${refreshToken}` },
  });

  if (!response.ok) {
    return null;
  }

  const data = await response.json();
  if (!data.access_token) {
    return null;
  }

  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token ?? refreshToken,
  };
}

async function ensureToken(): Promise<void> {
  if (accessToken) {
    return;
  }

  const tokens = await login();
  accessToken = tokens.access_token;
  refreshToken = tokens.refresh_token;
}

async function sendTemplate(
  payload: Record<string, unknown>,
): Promise<Response> {
  await ensureToken();

  let response = await fetch(WHATSAPP_TEMPLATE_URL!, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });

  if (response.status !== 401) {
    return response;
  }

  const refreshed = await refresh();
  if (refreshed) {
    accessToken = refreshed.access_token;
    refreshToken = refreshed.refresh_token;
    response = await fetch(WHATSAPP_TEMPLATE_URL!, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    });
    if (response.status !== 401) {
      return response;
    }
  }

  const tokens = await login();
  accessToken = tokens.access_token;
  refreshToken = tokens.refresh_token;
  return await fetch(WHATSAPP_TEMPLATE_URL!, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
}

async function markNotified(eventIds: string[]) {
  if (eventIds.length === 0) {
    return;
  }
  const { error } = await supabase
    .from("attendance_events")
    .update({ notified_at: new Date().toISOString() })
    .in("id", eventIds);

  if (error) {
    throw new Error(`Failed to update notified_at: ${error.message}`);
  }
}

Deno.serve(async () => {
  const { data: events, error } = await supabase
    .from("attendance_events")
    .select("id,user_id,scheduled_for,timezone")
    .is("notified_at", null);

  if (error) {
    return new Response(
      JSON.stringify({
        detail: "Failed to load pending events",
        error: error.message,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }

  if (!events || events.length === 0) {
    return new Response(
      JSON.stringify({ detail: "No pending events" }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  }

  const userIds = [
    ...new Set(events.map((event: AttendanceEvent) => event.user_id)),
  ];
  const { data: records, error: recordsError } = await supabase
    .from("attendance_records")
    .select(
      "user_id,phone_number,location_address,location_latitude,location_longitude",
    )
    .in("user_id", userIds);

  if (recordsError) {
    return new Response(
      JSON.stringify({
        detail: "Failed to load attendance records",
        error: recordsError.message,
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }

  const recordMap = new Map(
    (records as AttendanceRecord[]).map((record) => [record.user_id, record]),
  );

  const notifiedIds: string[] = [];
  const failures: { id: string; error: string }[] = [];

  for (const event of events as AttendanceEvent[]) {
    const record = recordMap.get(event.user_id);
    if (!record?.phone_number) {
      continue;
    }

    const timezone = event.timezone || "UTC";
    const scheduled_for = event.scheduled_for;
    const { date, time } = formatLocalTime(scheduled_for, timezone);

    const payload = {
      templateName: WHATSAPP_TEMPLATE_NAME,
      languageCode: WHATSAPP_LANGUAGE_CODE,
      body: {
        map: {
          employee_name: { type: "text", text: event.user_id },
          checkin_date: { type: "text", text: date },
          checkin_time: { type: "text", text: time },
          checkin_location: { type: "text", text: record.location_address },
        },
      },
      header: {
        type: "location",
        location: {
          latitude: record.location_latitude,
          longitude: record.location_longitude,
          name: record.location_address,
          address: record.location_address,
        },
      },
      waId: toWaId(record.phone_number),
    };

    console.log({ payload });

    try {
      const response = await sendTemplate(payload);
      console.log({ response });
      if (!response.ok) {
        failures.push({ id: event.id, error: `Status ${response.status}` });
        continue;
      }
      notifiedIds.push(event.id);
    } catch (err) {
      failures.push({ id: event.id, error: String(err) });
    }
  }

  try {
    await markNotified(notifiedIds);
  } catch (err) {
    return new Response(
      JSON.stringify({
        detail: "Failed to update notifications",
        error: String(err),
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }

  return new Response(
    JSON.stringify({
      detail: "Notifications processed",
      pending: events.length,
      notified: notifiedIds.length,
      failures,
    }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
});
