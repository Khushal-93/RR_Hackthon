"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Sun, Moon, Menu, X, Sparkles } from "lucide-react";
import { GlobalSearchModal } from "./GlobalSearchModal";

export function Navbar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setTheme("dark");
      document.documentElement.classList.add("dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
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
    if (theme === "light") {
      setTheme("dark");
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      setTheme("light");
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
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
      <header role="banner" className="apple-nav">
        <div className="max-w-[1200px] mx-auto px-6 h-16 flex items-center justify-between gap-6">
          {/* Logo & Identity */}
          <Link href="/" className="flex items-center gap-2.5 group focus:outline-none">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#2B4ACB] to-[#FF5C93] flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-semibold text-lg tracking-tight text-text-primary group-hover:text-primary transition-colors">
              PRESSURE<span className="text-secondary font-bold">.XI</span>
            </span>
            <span className="hidden sm:inline-block text-[11px] font-mono px-2 py-0.5 rounded-full bg-soft-blue text-primary font-medium">
              IPL & T20I
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav role="navigation" aria-label="Main Navigation" className="hidden lg:flex items-center gap-1.5">
            {navLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3.5 py-1.5 text-sm rounded-full transition-all duration-200 ${
                    isActive
                      ? "bg-primary text-white font-medium shadow-sm"
                      : "text-text-secondary hover:text-text-primary hover:bg-black/5 dark:hover:bg-white/10"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Actions: Search Trigger & Theme Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSearchModalOpen(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded-full bg-surface-subtle text-text-secondary border border-border-light hover:border-primary/40 transition-colors"
              aria-label="Search players by name"
            >
              <Search className="w-3.5 h-3.5 text-text-muted" />
              <span className="hidden md:inline">Search...</span>
              <kbd className="hidden md:inline-block bg-surface px-1.5 py-0.5 text-[10px] font-mono rounded-full border border-border-light text-text-muted">
                /
              </kbd>
            </button>

            <button
              onClick={toggleTheme}
              className="p-2 text-text-secondary hover:text-text-primary rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            >
              {theme === "light" ? <Moon className="w-4 h-4 text-primary" /> : <Sun className="w-4 h-4 text-amber-300" />}
            </button>

            {/* Mobile Hamburger Trigger */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-text-secondary hover:text-text-primary rounded-full hover:bg-black/5 dark:hover:bg-white/10"
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
            className="lg:hidden bg-surface/95 backdrop-blur-xl border-b border-border-light px-6 py-4 space-y-2 animate-in fade-in"
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-2.5 text-sm rounded-xl font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-white"
                      : "text-text-secondary hover:text-text-primary hover:bg-black/5 dark:hover:bg-white/10"
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
