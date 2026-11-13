import fs from "fs";
import path from "path";
import { z } from "zod";

const DATA_DIR = path.join(__dirname, "..", "public", "data");
const CSV_PATH = path.join(__dirname, "..", "outputs", "final_rankings.csv");

console.log("===============================================================");
console.log("  PHASE 1: RUNNING STRICT ZOD DATA VALIDATION");
console.log("===============================================================");

// 1. Meta Schema
const MetaSchema = z.object({
  dataset: z.object({
    total_matches: z.number().int().positive(),
    excluded_dls_matches: z.number().int().nonnegative(),
    excluded_dls_balls: z.number().int().nonnegative(),
    excluded_super_over_balls: z.number().int().nonnegative(),
    total_legal_deliveries: z.number().int().positive(),
    high_pressure_deliveries: z.number().int().positive(),
    high_pressure_pct: z.number().min(0).max(100),
    eligible_batters: z.literal(118),
    eligible_bowlers: z.literal(125),
    min_balls_threshold: z.literal(150),
    min_matches_threshold: z.literal(15),
  }),
  build: z.object({
    version: z.string(),
    git_commit: z.string(),
    build_timestamp: z.string(),
    data_span: z.string(),
    caveat: z.string(),
  }),
});

// 2. Rankings Item Schema
const RankingItemSchema = z
  .object({
    player_id: z.string().min(1),
    rank: z.number().int().positive(),
    role: z.enum(["batter", "bowler"]),
    player_name: z.string().min(1),
    balls: z.number().int().min(150),
    matches: z.number().int().min(15),
    raw_rate: z.number(),
    shrunk_rate: z.number(),
    lambda: z.number().min(0).max(1),
    ci80_lower: z.number(),
    ci80_upper: z.number(),
    prob_top10: z.number().min(0).max(1),
    dismissal_rate_vs_exp: z.number(),
    ipl_share_pct: z.number().min(0).max(100),
    t20i_share_pct: z.number().min(0).max(100),
    tier: z.string().min(1),
    pace_or_spin: z.enum(["Pace", "Spin"]).nullable().optional(),
    batting_type: z.string().nullable().optional(),
    bowling_type: z.string().nullable().optional(),
  })
  .refine((data) => data.ci80_lower <= data.ci80_upper, {
    message: "ci80_lower cannot exceed ci80_upper",
    path: ["ci80_lower"],
  });

// 3. Leverage by Over Schema
const LeverageByOverItemSchema = z.object({
  over: z.number().int().min(1).max(20),
  innings_1_mean: z.number(),
  innings_1_stderr: z.number(),
  innings_2_mean: z.number(),
  innings_2_stderr: z.number(),
  overall_mean: z.number(),
});

// 4. Player Profile Schema
const PlayerProfileSchema = z.object({
  player_id: z.string().min(1),
  player_name: z.string().min(1),
  role: z.enum(["batter", "bowler"]),
  rank: z.number().int().positive(),
  tier: z.string().min(1),
  plain_language_reading: z.string().min(1),
  stats: z.object({
    balls: z.number().int().min(150),
    matches: z.number().int().min(15),
    raw_rate: z.number(),
    shrunk_rate: z.number(),
    lambda: z.number().min(0).max(1),
    ci80_lower: z.number(),
    ci80_upper: z.number(),
    prob_top10: z.number().min(0).max(1),
    dismissal_rate_vs_exp: z.number(),
    ipl_share_pct: z.number().min(0).max(100),
    t20i_share_pct: z.number().min(0).max(100),
  }),
  phase_split: z.object({
    powerplay_balls: z.number().int().nonnegative(),
    powerplay_pct: z.number().min(0).max(100),
    middle_balls: z.number().int().nonnegative(),
    middle_pct: z.number().min(0).max(100),
    death_balls: z.number().int().nonnegative(),
    death_pct: z.number().min(0).max(100),
  }),
  innings_split: z.object({
    innings_1_balls: z.number().int().nonnegative(),
    innings_1_pct: z.number().min(0).max(100),
    innings_2_balls: z.number().int().nonnegative(),
    innings_2_pct: z.number().min(0).max(100),
  }),
  stability_check: z.object({
    leave_2_matches_raw_rate: z.number(),
    leave_2_matches_shrunk_rate: z.number(),
    leave_2_matches_rank: z.number().int().positive(),
    rank_delta: z.number().int(),
    is_sensitive: z.boolean(),
    audit_note: z.string(),
  }),
  match_strip: z.array(
    z.object({
      match_id: z.number().int().positive(),
      season: z.number().int(),
      match_date: z.string(),
      balls: z.number().int().positive(),
      runs: z.number().int().nonnegative(),
      wickets: z.number().int().nonnegative(),
      contribution_rate: z.number(),
    })
  ),
});

function runValidation() {
  let errorCount = 0;

  // Validate meta.json
  try {
    const metaRaw = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, "meta.json"), "utf-8")
    );
    MetaSchema.parse(metaRaw);
    console.log("[PASS] meta.json validated successfully.");
  } catch (err: any) {
    console.error("[FAIL] meta.json schema error:", err);
    errorCount++;
  }

  // Validate leverage_by_over.json
  try {
    const lboRaw = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, "leverage_by_over.json"), "utf-8")
    );
    z.array(LeverageByOverItemSchema).length(20).parse(lboRaw);
    console.log("[PASS] leverage_by_over.json (20 overs) validated successfully.");
  } catch (err: any) {
    console.error("[FAIL] leverage_by_over.json schema error:", err);
    errorCount++;
  }

  // Validate rankings.json
  const playerIds = new Set<string>();
  let rankings: any[] = [];
  try {
    const rankingsRaw = JSON.parse(
      fs.readFileSync(path.join(DATA_DIR, "rankings.json"), "utf-8")
    );
    rankings = z.array(RankingItemSchema).length(243).parse(rankingsRaw);

    const batters = rankings.filter((r) => r.role === "batter");
    const bowlers = rankings.filter((r) => r.role === "bowler");

    if (batters.length !== 118) {
      throw new Error(`Expected 118 eligible batters, found ${batters.length}`);
    }
    if (bowlers.length !== 125) {
      throw new Error(`Expected 125 eligible bowlers, found ${bowlers.length}`);
    }

    // Check duplicate IDs
    for (const p of rankings) {
      if (playerIds.has(p.player_id)) {
        throw new Error(`Duplicate player_id found: ${p.player_id}`);
      }
      playerIds.add(p.player_id);
    }

    console.log(
      `[PASS] rankings.json (243 players: 118 batters, 125 bowlers) validated with 0 duplicates.`
    );
  } catch (err: any) {
    console.error("[FAIL] rankings.json schema error:", err);
    errorCount++;
  }

  // Reconcile Top-10 against frozen final_rankings.csv
  try {
    const csvContent = fs.readFileSync(CSV_PATH, "utf-8").trim().split("\n");
    const header = csvContent[0].split(",");
    const roleIdx = header.indexOf("role");
    const rankIdx = header.indexOf("rank");
    const nameIdx = header.indexOf("player_name");

    const csvBattersTop10: string[] = [];
    const csvBowlersTop10: string[] = [];

    for (let i = 1; i < csvContent.length; i++) {
      const parts = csvContent[i].split(",");
      const role = parts[roleIdx].trim();
      const rank = parseInt(parts[rankIdx].trim(), 10);
      const name = parts[nameIdx].trim();
      if (rank <= 10) {
        if (role === "batter") csvBattersTop10[rank - 1] = name;
        if (role === "bowler") csvBowlersTop10[rank - 1] = name;
      }
    }

    const jsonBattersTop10 = rankings
      .filter((r) => r.role === "batter" && r.rank <= 10)
      .sort((a, b) => a.rank - b.rank)
      .map((r) => r.player_name);

    const jsonBowlersTop10 = rankings
      .filter((r) => r.role === "bowler" && r.rank <= 10)
      .sort((a, b) => a.rank - b.rank)
      .map((r) => r.player_name);

    for (let r = 0; r < 10; r++) {
      if (jsonBattersTop10[r] !== csvBattersTop10[r]) {
        throw new Error(
          `Batter Top-10 mismatch at Rank ${r + 1}: JSON '${jsonBattersTop10[r]}' vs CSV '${csvBattersTop10[r]}'`
        );
      }
      if (jsonBowlersTop10[r] !== csvBowlersTop10[r]) {
        throw new Error(
          `Bowler Top-10 mismatch at Rank ${r + 1}: JSON '${jsonBowlersTop10[r]}' vs CSV '${csvBowlersTop10[r]}'`
        );
      }
    }
    console.log(
      "[PASS] Top-10 Batters & Bowlers strictly reconciled against final_rankings.csv in exact order."
    );
  } catch (err: any) {
    console.error("[FAIL] Top-10 Reconciliation Error:", err);
    errorCount++;
  }

  // Validate all individual player profile files
  const playersDir = path.join(DATA_DIR, "players");
  const playerFiles = fs.readdirSync(playersDir);
  console.log(`Validating ${playerFiles.length} player profile files...`);

  let profileErrors = 0;
  for (const pf of playerFiles) {
    if (!pf.endsWith(".json")) continue;
    try {
      const pData = JSON.parse(
        fs.readFileSync(path.join(playersDir, pf), "utf-8")
      );
      PlayerProfileSchema.parse(pData);
    } catch (err: any) {
      console.error(`[FAIL] Error in profile ${pf}:`, err.message);
      profileErrors++;
    }
  }

  if (profileErrors > 0) {
    console.error(`[FAIL] Found ${profileErrors} invalid player profile files.`);
    errorCount += profileErrors;
  } else {
    console.log(
      `[PASS] All ${playerFiles.length} individual player profile JSON files validated successfully.`
    );
  }

  if (errorCount > 0) {
    console.error(`\nValidation failed with ${errorCount} errors!`);
    process.exit(1);
  } else {
    console.log(
      "\n==============================================================="
    );
    console.log("  ALL DATA FILES PASSED STRICT ZOD VALIDATION!");
    console.log(
      "==============================================================="
    );
  }
}

runValidation();
