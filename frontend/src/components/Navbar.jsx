import React, { useState } from 'react';
import { Search, User, Menu, X } from 'lucide-react';
import { navLinks } from '../data/destinations';

export default function Navbar({ activeTab = 'home', onSelectTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs = [
    { id: 'home', name: 'Home', href: '#' },
    { id: 'explore', name: 'Explore', href: '#explore' },
    { id: 'map', name: 'Map', href: '#map' },
    { id: 'planner', name: 'Trip Planner', href: '#planner' },
    { id: 'experiences', name: 'Local Experiences', href: '#experiences' },
  ];

  const handleTabClick = (tabId, e) => {
    if (onSelectTab) {
      e.preventDefault();
      onSelectTab(tabId);
    }
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 pt-3 pb-2 px-3 sm:px-4">
      <div className="max-w-[1360px] mx-auto bg-white rounded-2xl sm:rounded-full px-5 py-3 shadow-soft flex items-center justify-between border border-slate-100/80 transition-all duration-200">
        
        {/* Brand Logo */}
        <a
          href="#"
          onClick={(e) => handleTabClick('home', e)}
          className="flex items-center gap-2.5 group"
        >
          <div className="w-9 h-9 rounded-xl bg-navy flex items-center justify-center text-white shadow-sm transition-transform duration-200 group-hover:scale-105">
            {/* Custom Mountain Peak SVG Logo */}
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m8 3 4 8 5-5 5 15H2L8 3z" />
            </svg>
          </div>
          <span className="font-extrabold text-lg sm:text-xl text-navy tracking-tight font-sans">
            Tripura Explore
          </span>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-7">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <a
                key={tab.id}
                href={tab.href}
                onClick={(e) => handleTabClick(tab.id, e)}
                className={`relative text-sm font-semibold transition-colors duration-150 py-1.5 ${
                  isActive
                    ? 'text-navy font-bold'
                    : 'text-slate-600 hover:text-navy'
                }`}
              >
                {tab.name}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2.5px] bg-navy rounded-full" />
                )}
              </a>
            );
          })}
        </nav>

        {/* Right Action Icons */}
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            aria-label="Search"
            className="w-9 h-9 rounded-full flex items-center justify-center text-slate-600 hover:text-navy hover:bg-slate-100 transition-colors"
          >
            <Search className="w-5 h-5" />
          </button>

          <button
            type="button"
            aria-label="User Account"
            className="w-9 h-9 rounded-full bg-cream-card hover:bg-slate-200 text-navy flex items-center justify-center border border-slate-200 transition-colors"
          >
            <User className="w-5 h-5" />
          </button>

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            aria-label="Toggle menu"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden w-9 h-9 rounded-full flex items-center justify-center text-slate-700 hover:bg-slate-100 ml-1"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-2 max-w-[1360px] mx-auto bg-white rounded-2xl shadow-card border border-slate-100 p-4 transition-all">
          <nav className="flex flex-col gap-2">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <a
                  key={tab.id}
                  href={tab.href}
                  onClick={(e) => handleTabClick(tab.id, e)}
                  className={`px-3 py-2 rounded-xl text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-navy text-white font-bold'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {tab.name}
                </a>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}
