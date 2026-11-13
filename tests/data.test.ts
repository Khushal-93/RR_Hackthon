import { describe, it, expect } from "vitest";
import {
  getMetaSync,
  getRankingsSync,
  getRankings,
  getPlayerSync,
  getAllPlayerIdsSync,
  getLeverageByOverSync,
  getHeatmapSync,
  getValidationSync,
} from "../lib/data";

describe("Phase 1: Static Data Layer Unit Tests", () => {
  it("loads meta.json with correct non-DLS sample counts", () => {
    const meta = getMetaSync();
    expect(meta.dataset.total_matches).toBe(829);
    expect(meta.dataset.excluded_dls_matches).toBe(41);
    expect(meta.dataset.excluded_dls_balls).toBe(5254);
    expect(meta.dataset.eligible_batters).toBe(118);
    expect(meta.dataset.eligible_bowlers).toBe(125);
    expect(meta.dataset.min_balls_threshold).toBe(150);
  });

  it("loads all 243 eligible players in rankings.json", () => {
    const all = getRankingsSync();
    expect(all.length).toBe(243);

    const batters = getRankingsSync("batter");
    expect(batters.length).toBe(118);

    const bowlers = getRankingsSync("bowler");
    expect(bowlers.length).toBe(125);
  });

  it("reconciles top 10 batters and bowlers in exact order", () => {
    const batters = getRankingsSync("batter").slice(0, 10);
    expect(batters[0].player_name).toBe("Vaibhav Sooryavanshi");
    expect(batters[1].player_name).toBe("Priyansh Arya");
    expect(batters[2].player_name).toBe("Abhishek Sharma");

    const bowlers = getRankingsSync("bowler").slice(0, 10);
    expect(bowlers[0].player_name).toBe("Krunal Pandya");
    expect(bowlers[1].player_name).toBe("Sunil Narine");
    expect(bowlers[2].player_name).toBe("Rashid Khan");
  });

  it("filters rankings by role, minimum balls, and search query", async () => {
    const filtered = await getRankings({
      role: "batter",
      minBalls: 500,
      searchQuery: "Abhishek",
    });
    expect(filtered.length).toBeGreaterThanOrEqual(1);
    expect(filtered[0].player_name).toBe("Abhishek Sharma");
  });

  it("loads individual player profiles and handles missing players gracefully", () => {
    const profile = getPlayerSync("vaibhav-sooryavanshi-batter");
    expect(profile).not.toBeNull();
    expect(profile?.player_name).toBe("Vaibhav Sooryavanshi");
    expect(profile?.stats.balls).toBe(331);
    expect(profile?.phase_split.powerplay_pct).toBeGreaterThan(0);

    const missing = getPlayerSync("nonexistent-player-role");
    expect(missing).toBeNull();
  });

  it("loads all 243 player IDs for static page generation", () => {
    const ids = getAllPlayerIdsSync();
    expect(ids.length).toBe(243);
    expect(new Set(ids).size).toBe(243);
  });

  it("loads leverage by over for overs 1 to 20", () => {
    const lbo = getLeverageByOverSync();
    expect(lbo.length).toBe(20);
    expect(lbo[0].over).toBe(1);
    expect(lbo[19].over).toBe(20);
    expect(lbo[0].innings_1_mean).toBeGreaterThan(0);
  });

  it("loads leverage heatmaps for innings 1 and 2", () => {
    const hm = getHeatmapSync();
    expect(hm.innings_1.length).toBe(20);
    expect(hm.innings_2.length).toBe(20);
    expect(hm.summary.inn1_powerplay_share).toBe(75.54);
  });

  it("loads validation results including out-of-time tests and Brier score", () => {
    const val = getValidationSync();
    expect(val.win_probability_brier.group_kfold_brier).toBe(0.1796);
    expect(val.out_of_time_repeatability.batters.spearman_rho).toBe(0.2501);
    expect(val.out_of_time_repeatability.bowlers.spearman_rho).toBe(0.2861);
    expect(val.calibration_deciles.length).toBe(10);
  });
});
