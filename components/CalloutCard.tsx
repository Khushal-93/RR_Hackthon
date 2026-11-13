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
    <div className="bg-surface border border-border-light rounded-lg p-5 flex flex-col justify-between hover:border-border-medium transition-colors">
      <div className="space-y-2">
        <span className="font-mono text-[10px] uppercase font-bold text-accent-primary tracking-wider px-2 py-0.5 rounded bg-surface-subtle border border-border-light inline-block">
          {tag}
        </span>
        <h3 className="font-bold text-base text-text-primary">{title}</h3>
        <p className="text-xs text-text-secondary leading-relaxed">{description}</p>
      </div>

      {linkHref && (
        <div className="pt-4 mt-4 border-t border-border-light/50">
          <Link
            href={linkHref}
            className="inline-flex items-center gap-1 font-mono text-xs text-accent-primary hover:underline"
          >
            <span>{linkLabel || "Learn more"}</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}
    </div>
  );
}
