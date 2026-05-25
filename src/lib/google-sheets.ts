import { google } from "googleapis";
import fs from "fs";
import path from "path";

const SHEET_ID = process.env.GOOGLE_SHEETS_ID;
const SERVICE_ACCOUNT_FILE = process.env.GOOGLE_SERVICE_ACCOUNT_FILE || "./service-account.json";

let sheetsClient: any = null;

async function getSheetClient() {
  if (sheetsClient) {
    return sheetsClient;
  }

  try {
    const credentialsPath = path.resolve(SERVICE_ACCOUNT_FILE);
    const credentials = JSON.parse(fs.readFileSync(credentialsPath, "utf-8"));

    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });

    sheetsClient = google.sheets({ version: "v4", auth });
    return sheetsClient;
  } catch (err) {
    console.error("Failed to initialize Google Sheets client:", err);
    throw err;
  }
}

export async function appendReview(
  rating: number,
  comment: string,
  source: string
) {
  try {
    const sheets = await getSheetClient();

    if (!SHEET_ID) {
      throw new Error("GOOGLE_SHEETS_ID not set");
    }

    const now = new Date();
    const dateStr = now.toLocaleDateString("th-TH");
    const timeStr = now.toLocaleTimeString("th-TH");

    const values = [
      [rating, comment, source, `${dateStr} ${timeStr}`],
    ];

    await sheets.spreadsheets.values.append({
      spreadsheetId: SHEET_ID,
      range: "รีวิว!A:D",
      valueInputOption: "RAW",
      requestBody: {
        values,
      },
    });

    return { success: true };
  } catch (err) {
    console.error("Error appending review to Sheets:", err);
    throw err;
  }
}

export async function getReviews() {
  try {
    const sheets = await getSheetClient();

    if (!SHEET_ID) {
      throw new Error("GOOGLE_SHEETS_ID not set");
    }

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: "รีวิว!A:D",
    });

    const rows = response.data.values || [];
    const reviews = rows.slice(1).map((row: any[]) => ({
      rating: parseInt(row[0]) || 0,
      comment: row[1] || "",
      source: row[2] || "",
      createdAt: row[3] || "",
    }));

    return reviews;
  } catch (err) {
    console.error("Error reading reviews from Sheets:", err);
    return [];
  }
}
