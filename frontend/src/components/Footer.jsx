import React from 'react';

export default function Footer() {
  const footerLinks = [
    { name: 'Home', href: '#' },
    { name: 'Explore', href: '#explore' },
    { name: 'Map', href: '#map' },
    { name: 'Trip Planner', href: '#planner' },
    { name: 'Local Experiences', href: '#experiences' },
    { name: 'About', href: '#about' },
  ];

  return (
    <footer className="px-3 sm:px-4 pt-4 pb-8">
      <div className="max-w-[1360px] mx-auto bg-navy text-white rounded-3xl sm:rounded-[28px] p-8 sm:p-12 shadow-card border border-slate-800/20">
        
        {/* Main Footer Row */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8 pb-8 border-b border-white/10">
          
          {/* Left Brand Area */}
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center text-white shrink-0 shadow-sm">
              <svg
                className="w-6 h-6"
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
            <div>
              <span className="font-extrabold text-xl text-white tracking-tight block">
                Tripura Explore
              </span>
              <span className="text-[11px] font-semibold text-[#D4E0EE] tracking-wider uppercase block">
                Discover · Explore · Experience
              </span>
            </div>
          </div>

          {/* Center Links */}
          <nav className="flex flex-wrap items-center gap-x-6 gap-y-2.5 text-xs sm:text-sm font-medium text-slate-300">
            {footerLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="hover:text-white transition-colors duration-150 py-1"
              >
                {link.name}
              </a>
            ))}
          </nav>

          {/* Right Social Icons */}
          <div className="flex items-center gap-3">
            {/* Facebook */}
            <a
              href="https://facebook.com"
              target="_blank"
              rel="noreferrer"
              aria-label="Tripura Explore on Facebook"
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all duration-200 hover:scale-105"
            >
              <svg className="w-4 h-4 fill-currentColor" viewBox="0 0 24 24">
                <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3V2z" />
              </svg>
            </a>

            {/* Instagram */}
            <a
              href="https://instagram.com"
              target="_blank"
              rel="noreferrer"
              aria-label="Tripura Explore on Instagram"
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all duration-200 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                <rect x="2" y="2" width="20" height="20" rx="5" />
                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
                <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
              </svg>
            </a>

            {/* YouTube */}
            <a
              href="https://youtube.com"
              target="_blank"
              rel="noreferrer"
              aria-label="Tripura Explore on YouTube"
              className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all duration-200 hover:scale-105"
            >
              <svg className="w-4 h-4 fill-currentColor" viewBox="0 0 24 24">
                <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.94 2C5.12 20 12 20 12 20s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58zM9.75 15.02V8.98L15.5 12l-5.75 3.02z" />
              </svg>
            </a>
          </div>

        </div>

        {/* Bottom Copyright */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-3">
          <span>Explore Northeast India’s best kept secret.</span>
          <span>© 2025 Tripura Explore. All rights reserved.</span>
        </div>

      </div>
    </footer>
  );
}
