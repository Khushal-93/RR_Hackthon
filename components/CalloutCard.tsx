import React from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

interface Props {
  tag: string;
  title: string;
  description: string;
  linkHref?: string;
  linkLabel?: string;
}

export function CalloutCard({ tag, title, description, linkHref, linkLabel }: Props) {
  return (
    <div className="apple-card p-7 flex flex-col justify-between">
      <div className="space-y-3">
        <span className="text-[11px] font-mono font-semibold uppercase tracking-wider px-3 py-1 rounded-full bg-soft-blue text-primary inline-block">
          {tag}
        </span>
        <h3 className="text-xl font-semibold tracking-tight text-text-primary">{title}</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
      </div>

      {linkHref && (
        <div className="pt-5 mt-5 border-t border-border-light">
          <Link
            href={linkHref}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary-dark transition-colors group"
          >
            <span>{linkLabel || "Learn more"}</span>
            <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </Link>
        </div>
      )}
    </div>
  );
}
