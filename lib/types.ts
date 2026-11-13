export type PlayerRole = "batter" | "bowler";

export interface RankingItem {
  player_id: string;
  rank: number;
  role: PlayerRole;
  player_name: string;
  balls: number;
  matches: number;
  raw_rate: number;
  shrunk_rate: number;
  lambda: number;
  ci80_lower: number;
  ci80_upper: number;
  prob_top10: number;
  dismissal_rate_vs_exp: number;
  ipl_share_pct: number;
  t20i_share_pct: number;
  tier: string;
  pace_or_spin?: "Pace" | "Spin" | null;
  batting_type?: string | null;
  bowling_type?: string | null;
}

export interface MetaData {
  dataset: {
    total_matches: number;
    excluded_dls_matches: number;
    excluded_dls_balls: number;
    excluded_super_over_balls: number;
    total_legal_deliveries: number;
    high_pressure_deliveries: number;
    high_pressure_pct: number;
    eligible_batters: number;
    eligible_bowlers: number;
    min_balls_threshold: number;
    min_matches_threshold: number;
    leverage_inn1_cutoff: number;
    leverage_inn2_cutoff: number;
  };
  build: {
    version: string;
    git_commit: string;
    build_timestamp: string;
    data_span: string;
    competitions: string[];
    caveat: string;
  };
}

export interface LeverageByOverItem {
  over: number;
  innings_1_mean: number;
  innings_1_stderr: number;
  innings_2_mean: number;
  innings_2_stderr: number;
  overall_mean: number;
}

export interface LeverageHeatmapRow {
  over: number;
  [key: string]: number | null | undefined;
}

export interface LeverageHeatmapData {
  innings_1: LeverageHeatmapRow[];
  innings_2: LeverageHeatmapRow[];
  summary: {
    inn1_powerplay_share: number;
    inn1_top_order_share: number;
    tactical_note: string;
  };
}

export interface OutOfTimeStats {
  n_qualifiers: number;
  spearman_rho: number;
  ci95_lower: number;
  ci95_upper: number;
  pearson_r: number;
  top10_overlap: number;
  top10_chance: number;
  top20pct_overlap_pct: number;
  top20pct_chance_pct: number;
  signal_interpretation: string;
}

export interface ValidationData {
  win_probability_brier: {
    group_kfold_brier: number;
    temporal_holdout_brier: number;
    naive_baseline_brier: number;
    relative_improvement_pct: number;
  };
  out_of_time_repeatability: {
    evaluation_threshold: string;
    train_span: string;
    test_span: string;
    batters: OutOfTimeStats;
    bowlers: OutOfTimeStats;
  };
  dropped_experiments: Array<{
    candidate: string;
    reason: string;
    disposition: string;
  }>;
  calibration_deciles: Array<{
    decile: number;
    pred_wp: number;
    obs_win_rate: number;
    count: number;
  }>;
}

export interface MatchContribution {
  match_id: number;
  season: number;
  match_date: string;
  balls: number;
  runs: number;
  wickets: number;
  contribution_rate: number;
}

export interface PlayerProfile {
  player_id: string;
  player_name: string;
  role: PlayerRole;
  rank: number;
  tier: string;
  plain_language_reading: string;
  stats: {
    balls: number;
    matches: number;
    raw_rate: number;
    shrunk_rate: number;
    lambda: number;
    ci80_lower: number;
    ci80_upper: number;
    prob_top10: number;
    dismissal_rate_vs_exp: number;
    ipl_share_pct: number;
    t20i_share_pct: number;
  };
  profile: {
    batting_type?: string | null;
    bowling_type?: string | null;
    pace_or_spin?: "Pace" | "Spin" | null;
    active_years: [number, number];
  };
  phase_split: {
    powerplay_balls: number;
    powerplay_pct: number;
    middle_balls: number;
    middle_pct: number;
    death_balls: number;
    death_pct: number;
  };
  innings_split: {
    innings_1_balls: number;
    innings_1_pct: number;
    innings_2_balls: number;
    innings_2_pct: number;
  };
  stability_check: {
    leave_2_matches_raw_rate: number;
    leave_2_matches_shrunk_rate: number;
    leave_2_matches_rank: number;
    rank_delta: number;
    is_sensitive: boolean;
    audit_note: string;
  };
  match_strip: MatchContribution[];
}

export interface FilterOptions {
  role?: PlayerRole;
  minBalls?: number;
  competition?: "all" | "ipl" | "t20i";
  paceOrSpin?: "all" | "Pace" | "Spin";
  searchQuery?: string;
  sortBy?: "rank" | "shrunk_rate" | "prob_top10" | "balls" | "matches";
  sortOrder?: "asc" | "desc";
}
