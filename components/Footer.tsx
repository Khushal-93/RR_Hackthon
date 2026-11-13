import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer role="contentinfo" className="mt-auto border-t border-border-light bg-surface py-10 text-xs text-text-secondary">
      <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2 space-y-2">
            <div className="font-mono font-bold text-sm tracking-wider text-text-primary">
              PRESSURE<span className="text-accent-primary">.XI</span>
            </div>
            <p className="max-w-md leading-relaxed text-text-muted">
              Who Delivers Under Pressure? IPL & T20I, 2022 to 2026. A strictly historical, empirical evaluation of batting efficiency and bowling run suppression in high-leverage corridors.
            </p>
            <p className="font-mono text-[11px] text-accent-warning">
              Descriptive historical ratings, not predictions.
            </p>
          </div>

          <div className="space-y-2 font-mono text-xs">
            <div className="font-bold text-text-primary uppercase tracking-wider text-[11px]">Audit & Integrity</div>
            <ul className="space-y-1.5">
              <li>
                <Link href="/method/" className="hover:text-accent-primary transition-colors">
                  Methodology & Reliability Audit &rarr;
                </Link>
              </li>
              <li>
                <Link href="/rankings/" className="hover:text-accent-primary transition-colors">
                  Full Roster Rankings (243 players) &rarr;
                </Link>
              </li>
              <li>
                <Link href="/pressure/" className="hover:text-accent-primary transition-colors">
                  Pressure Definition & Explorer &rarr;
                </Link>
              </li>
            </ul>
          </div>

          <div className="space-y-2 text-xs">
            <div className="font-bold text-text-primary uppercase font-mono tracking-wider text-[11px]">Data Source & Scope</div>
            <p className="leading-relaxed text-text-muted font-mono text-[11px]">
              829 clean non-DLS T20 matches (195,707 legal deliveries). All rain-shortened DLS matches (41) and Super Overs (38 balls) strictly excluded.
            </p>
            <p className="text-[11px] text-text-muted">
              No affiliation, endorsement, or sponsorship by any franchise, cricket board, or tournament organizers is implied.
            </p>
          </div>
        </div>

        <div className="pt-6 border-t border-border-light flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-text-muted">
          <div>&copy; 2026 Pressure XI Research Submission. Academic & Competition Evaluation.</div>
          <div className="flex items-center gap-4">
            <Link href="/data/rankings.json" target="_blank" className="hover:text-accent-primary underline">
              JSON Data
            </Link>
            <span>&bull;</span>
            <Link href="/outputs/final_rankings.csv" download className="hover:text-accent-primary underline">
              Download CSV
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
