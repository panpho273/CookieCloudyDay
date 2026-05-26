import fs from "fs";
import path from "path";
import { google } from "googleapis";

const SHEET_ID =
  process.env.GOOGLE_SHEET_ID ||
  process.env.GOOGLE_SHEETS_ID ||
  process.env.SHEET_ID ||
  "";

function getAuthClient() {
  const serviceAccountPath = path.join(process.cwd(), "service-account.json");

  let clientEmail = process.env.GOOGLE_CLIENT_EMAIL || "";
  let privateKey = process.env.GOOGLE_PRIVATE_KEY || "";

  if ((!clientEmail || !privateKey) && fs.existsSync(serviceAccountPath)) {
    const raw = fs.readFileSync(serviceAccountPath, "utf-8");
    const json = JSON.parse(raw);

    clientEmail = json.client_email || clientEmail;
    privateKey = json.private_key || privateKey;
  }

  if (!SHEET_ID) {
    throw new Error("Missing GOOGLE_SHEET_ID / GOOGLE_SHEETS_ID");
  }

  if (!clientEmail || !privateKey) {
    throw new Error("Missing Google service account credentials");
  }

  privateKey = privateKey.replace(/\\n/g, "\n");

  return new google.auth.JWT({
    email: clientEmail,
    key: privateKey,
    scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
  });
}

export async function getSheetValues(range: string) {
  const auth = getAuthClient();
  const sheets = google.sheets({ version: "v4", auth });

  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range,
  });

  return response.data.values || [];
}

export async function getOrdersSheet() {
  return getSheetValues("'ชีต1'!A:Z");
}

export async function getReviewsSheet() {
  return getSheetValues("reviews!A:Z");
}

export async function getMembersSheet() {
  return getSheetValues("members!A:Z");
}
