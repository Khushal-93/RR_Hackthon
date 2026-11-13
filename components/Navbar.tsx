"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Sun, Moon, Menu, X } from "lucide-react";
import { GlobalSearchModal } from "./GlobalSearchModal";

export function Navbar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light" || (!savedTheme && window.matchMedia("(prefers-color-scheme: light)").matches)) {
      setTheme("light");
      document.documentElement.classList.add("light");
    } else {
      setTheme("dark");
      document.documentElement.classList.remove("light");
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setSearchModalOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const toggleTheme = () => {
    if (theme === "dark") {
      setTheme("light");
      document.documentElement.classList.add("light");
      localStorage.setItem("theme", "light");
    } else {
      setTheme("dark");
      document.documentElement.classList.remove("light");
      localStorage.setItem("theme", "dark");
    }
  };

  const navLinks = [
    { label: "Overview", href: "/" },
    { label: "Rankings", href: "/rankings/" },
    { label: "Compare", href: "/compare/" },
    { label: "Pressure Explorer", href: "/pressure/" },
    { label: "Method & Reliability", href: "/method/" },
  ];

  return (
    <>
      <header role="banner" className="sticky top-0 z-40 bg-surface/95 backdrop-blur border-b border-border-light">
        <div className="max-w-[1344px] mx-auto px-4 sm:px-6 md:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Identity */}
          <Link href="/" className="flex items-center gap-2 group focus:outline-none">
            <span className="font-mono font-bold text-lg tracking-wider text-text-primary group-hover:text-accent-primary transition-colors">
              PRESSURE<span className="text-accent-primary">.XI</span>
            </span>
            <span className="hidden sm:inline-block text-[11px] font-mono px-2 py-0.5 rounded bg-surface-subtle text-text-muted border border-border-light">
              2022–2026
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav role="navigation" aria-label="Main Navigation" className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 text-xs font-mono rounded transition-colors ${
                    isActive
                      ? "bg-surface-subtle text-accent-primary font-bold border border-border-medium"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-subtle/50"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Actions: Search Trigger & Theme Toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSearchModalOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono bg-surface-subtle text-text-secondary border border-border-light rounded hover:border-border-medium transition-colors"
              aria-label="Search players by name"
            >
              <Search className="w-3.5 h-3.5 text-text-muted" />
              <span className="hidden md:inline">Search player...</span>
              <kbd className="hidden md:inline-block bg-surface px-1.5 py-0.5 text-[10px] rounded border border-border-light text-text-muted">
                /
              </kbd>
            </button>

            <button
              onClick={toggleTheme}
              className="p-2 text-text-secondary hover:text-text-primary bg-surface-subtle border border-border-light rounded transition-colors"
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
            >
              {theme === "dark" ? <Sun className="w-4 h-4 text-accent-batter" /> : <Moon className="w-4 h-4 text-text-primary" />}
            </button>

            {/* Mobile Hamburger Trigger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-text-secondary hover:text-text-primary bg-surface-subtle border border-border-light rounded"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <nav
            role="navigation"
            aria-label="Mobile Navigation Drawer"
            className="lg:hidden bg-surface border-b border-border-medium px-4 py-4 space-y-2 animate-in fade-in slide-in-from-top-2"
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-3 py-2 text-sm font-mono rounded ${
                    isActive
                      ? "bg-surface-subtle text-accent-primary font-bold border border-border-medium"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-subtle/50"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        )}
      </header>

      {/* Global Search Modal */}
      <GlobalSearchModal isOpen={searchModalOpen} onClose={() => setSearchModalOpen(false)} />
    </>
  );
}
