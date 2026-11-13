import React from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer role="contentinfo" className="mt-auto border-t border-border-light bg-surface/50 py-14 text-sm text-text-secondary">
      <div className="max-w-[1200px] mx-auto px-6 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-[#2B4ACB] to-[#FF5C93] flex items-center justify-center text-white">
                <Sparkles className="w-3 h-3" />
              </div>
              <span className="font-semibold text-base tracking-tight text-text-primary">
                PRESSURE<span className="text-secondary font-bold">.XI</span>
              </span>
            </div>
            <p className="max-w-md leading-relaxed text-text-secondary text-sm">
              Who Delivers Under Pressure? IPL & T20I, 2022 to 2026. An empirical, audited historical evaluation of batting runs-above-expected and bowling run-suppression in high-leverage corridors.
            </p>
            <div className="inline-block text-xs font-mono text-secondary bg-soft-pink px-3 py-1 rounded-full">
              Descriptive historical ratings, not predictions.
            </div>
          </div>

          <div className="space-y-3 text-sm">
            <div className="font-semibold text-text-primary uppercase tracking-wider text-xs">Platform & Audit</div>
            <ul className="space-y-2">
              <li>
                <Link href="/method/" className="hover:text-primary transition-colors">
                  Methodology & Reliability Audit &rarr;
                </Link>
              </li>
              <li>
                <Link href="/rankings/" className="hover:text-primary transition-colors">
                  Player Roster Rankings &rarr;
                </Link>
              </li>
              <li>
                <Link href="/pressure/" className="hover:text-primary transition-colors">
                  Pressure Explorer & Heatmaps &rarr;
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-3 text-xs leading-relaxed text-text-muted">
            <div className="font-semibold text-text-primary uppercase tracking-wider">Dataset Scope</div>
            <p>
              829 clean non-DLS T20 matches (195,707 legal deliveries). All rain-shortened DLS matches (41) and Super Overs (38 balls) strictly excluded.
            </p>
            <p>
              No affiliation, endorsement, or sponsorship by any franchise or tournament organizers is implied.
            </p>
          </div>
        </div>

        <div className="pt-8 border-t border-border-light flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-text-muted">
          <div>&copy; 2026 Pressure XI Research Submission. Academic & Competition Evaluation.</div>
          <div className="flex items-center gap-4">
            <Link href="/data/rankings.json" target="_blank" className="hover:text-primary transition-colors">
              Static JSON Data
            </Link>
            <span>&bull;</span>
            <Link href="/outputs/final_rankings.csv" download className="hover:text-primary transition-colors">
              Download CSV
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
