import fs from "fs";
import path from "path";
import {
  RankingItem,
  MetaData,
  LeverageByOverItem,
  LeverageHeatmapData,
  ValidationData,
  PlayerProfile,
  FilterOptions,
  PlayerRole,
} from "./types";

const IS_SERVER = typeof window === "undefined";

function readServerJson<T>(relativePath: string): T {
  const fullPath = path.join(process.cwd(), "public", "data", relativePath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Data file not found on server: ${relativePath}`);
  }
  const raw = fs.readFileSync(fullPath, "utf-8");
  return JSON.parse(raw) as T;
}

async function fetchClientJson<T>(relativePath: string): Promise<T> {
  const res = await fetch(`/data/${relativePath}`);
  if (!res.ok) {
    throw new Error(`Failed to load data: ${relativePath} (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function getMeta(): Promise<MetaData> {
  if (IS_SERVER) {
    return readServerJson<MetaData>("meta.json");
  }
  return fetchClientJson<MetaData>("meta.json");
}

export function getMetaSync(): MetaData {
  return readServerJson<MetaData>("meta.json");
}

export async function getRankings(options?: FilterOptions): Promise<RankingItem[]> {
  let all: RankingItem[];
  if (IS_SERVER) {
    all = readServerJson<RankingItem[]>("rankings.json");
  } else {
    all = await fetchClientJson<RankingItem[]>("rankings.json");
  }

  if (!options) return all;

  let result = [...all];

  // Role filter
  if (options.role) {
    result = result.filter((p) => p.role === options.role);
  }

  // Min balls filter
  if (options.minBalls && options.minBalls > 150) {
    result = result.filter((p) => p.balls >= options.minBalls!);
  }

  // Competition filter
  if (options.competition && options.competition !== "all") {
    if (options.competition === "ipl") {
      result = result.filter((p) => p.ipl_share_pct >= 50);
    } else if (options.competition === "t20i") {
      result = result.filter((p) => p.t20i_share_pct >= 50);
    }
  }

  // Pace/Spin filter (bowlers only)
  if (options.paceOrSpin && options.paceOrSpin !== "all") {
    result = result.filter((p) => p.pace_or_spin === options.paceOrSpin);
  }

  // Search query filter
  if (options.searchQuery && options.searchQuery.trim().length > 0) {
    const q = options.searchQuery.toLowerCase().trim();
    result = result.filter(
      (p) =>
        p.player_name.toLowerCase().includes(q) ||
        p.tier.toLowerCase().includes(q)
    );
  }

  // Sorting
  const sortBy = options.sortBy || "rank";
  const order = options.sortOrder || "asc";
  const mult = order === "asc" ? 1 : -1;

  result.sort((a, b) => {
    if (sortBy === "rank") return (a.rank - b.rank) * mult;
    if (sortBy === "shrunk_rate") return (a.shrunk_rate - b.shrunk_rate) * mult;
    if (sortBy === "prob_top10") return (a.prob_top10 - b.prob_top10) * mult;
    if (sortBy === "balls") return (a.balls - b.balls) * mult;
    if (sortBy === "matches") return (a.matches - b.matches) * mult;
    return 0;
  });

  return result;
}

export function getRankingsSync(role?: PlayerRole): RankingItem[] {
  const all = readServerJson<RankingItem[]>("rankings.json");
  if (role) {
    return all.filter((p) => p.role === role);
  }
  return all;
}

export async function getPlayer(playerId: string): Promise<PlayerProfile | null> {
  const filename = `players/${playerId}.json`;
  if (IS_SERVER) {
    const fullPath = path.join(process.cwd(), "public", "data", filename);
    if (!fs.existsSync(fullPath)) return null;
    return readServerJson<PlayerProfile>(filename);
  } else {
    try {
      return await fetchClientJson<PlayerProfile>(filename);
    } catch {
      return null;
    }
  }
}

export function getPlayerSync(playerId: string): PlayerProfile | null {
  const filename = `players/${playerId}.json`;
  const fullPath = path.join(process.cwd(), "public", "data", filename);
  if (!fs.existsSync(fullPath)) return null;
  return readServerJson<PlayerProfile>(filename);
}

export function getAllPlayerIdsSync(): string[] {
  const all = readServerJson<RankingItem[]>("rankings.json");
  return all.map((p) => p.player_id);
}

export async function getLeverageByOver(): Promise<LeverageByOverItem[]> {
  if (IS_SERVER) {
    return readServerJson<LeverageByOverItem[]>("leverage_by_over.json");
  }
  return fetchClientJson<LeverageByOverItem[]>("leverage_by_over.json");
}

export function getLeverageByOverSync(): LeverageByOverItem[] {
  return readServerJson<LeverageByOverItem[]>("leverage_by_over.json");
}

export async function getHeatmap(innings?: 1 | 2): Promise<LeverageHeatmapData> {
  let data: LeverageHeatmapData;
  if (IS_SERVER) {
    data = readServerJson<LeverageHeatmapData>("leverage_heatmap.json");
  } else {
    data = await fetchClientJson<LeverageHeatmapData>("leverage_heatmap.json");
  }
  return data;
}

export function getHeatmapSync(): LeverageHeatmapData {
  return readServerJson<LeverageHeatmapData>("leverage_heatmap.json");
}

export async function getValidation(): Promise<ValidationData> {
  if (IS_SERVER) {
    return readServerJson<ValidationData>("validation.json");
  }
  return fetchClientJson<ValidationData>("validation.json");
}

export function getValidationSync(): ValidationData {
  return readServerJson<ValidationData>("validation.json");
}
