import React from 'react';
import { Map, ArrowRight } from 'lucide-react';

export default function ActionCards() {
  return (
    <section className="px-3 sm:px-4 py-4 sm:py-6">
      <div className="max-w-[1360px] mx-auto grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6">
        
        {/* Card 1: Plan Your Trip (Full Scenic Road Background + Dark Gradient Overlay) */}
        <div className="relative rounded-3xl overflow-hidden min-h-[220px] sm:min-h-[240px] shadow-card group border border-slate-800/10 bg-[#0F1D2E] flex flex-col justify-between p-6 sm:p-8 text-white transition-all hover:shadow-xl hover:-translate-y-1">
          {/* Full Background Road Image & Overlay */}
          <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <img
              src="/images/plan-trip-road.jpg"
              alt="Scenic winding road through hills in Tripura"
              className="w-full h-full object-cover object-right sm:object-center transition-transform duration-700 ease-out group-hover:scale-105"
              loading="lazy"
            />
            {/* Left dark navy gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#0E1929]/95 via-[#0E1929]/90 md:via-[#0E1929]/80 md:to-transparent" />
          </div>

          {/* Card Content */}
          <div className="relative z-10 flex items-start gap-4 mb-6 max-w-sm">
            <div className="shrink-0 text-white pt-0.5">
              <svg className="w-9 h-9" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="8" cy="6" r="3" />
                <path d="M4 17l4-5 3 3 5-7 4 9" />
                <path d="M3 21h18" />
                <path d="M6 9l-2 12" />
              </svg>
            </div>
            <div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight mb-1.5 text-white">
                Plan Your Trip
              </h3>
              <p className="text-slate-200 text-xs sm:text-sm font-normal leading-relaxed">
                Get a personalized itinerary based on your interests and days.
              </p>
            </div>
          </div>

          <div className="relative z-10">
            <a
              href="#trip-planner"
              className="inline-flex items-center gap-2 bg-[#0E1929]/70 hover:bg-white hover:text-[#101C2E] text-white border border-white/80 hover:border-white px-5 sm:px-6 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all duration-200 active:scale-95 shadow-md group/btn"
            >
              <span>Start Planning</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" />
            </a>
          </div>
        </div>

        {/* Card 2: Explore the Map (Full Map Background + Cream Fade Overlay) */}
        <div className="relative rounded-3xl overflow-hidden min-h-[220px] sm:min-h-[240px] shadow-card group border border-slate-200/90 bg-[#FAF7F2] flex flex-col justify-between p-6 sm:p-8 transition-all hover:shadow-xl hover:-translate-y-1">
          {/* Full Background Map Image & Overlay */}
          <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <img
              src="/images/explore-map-bg.jpg"
              alt="Tripura interactive route map"
              className="w-full h-full object-cover object-right transition-transform duration-700 ease-out group-hover:scale-105"
              loading="lazy"
            />
            {/* Left cream fade gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#FAF7F2] via-[#FAF7F2] md:via-[#FAF7F2]/80 md:to-transparent" />
          </div>

          {/* Card Content */}
          <div className="relative z-10 flex items-start gap-4 mb-6 max-w-sm">
            <div className="w-12 h-12 rounded-full bg-white/70 backdrop-blur-sm border border-slate-200/60 flex items-center justify-center shrink-0 shadow-sm text-[#1B2A41]">
              <Map className="w-6 h-6 text-[#1B2A41]" />
            </div>
            <div>
              <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#1B2A41] mb-1.5">
                Explore the Map
              </h3>
              <p className="text-slate-600 text-xs sm:text-sm font-normal leading-relaxed">
                Find all attractions across Tripura on an interactive map.
              </p>
            </div>
          </div>

          <div className="relative z-10">
            <a
              href="#map"
              className="inline-flex items-center gap-2 bg-[#1B2A41] hover:bg-[#111D2E] text-white px-5 sm:px-6 py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all duration-200 active:scale-95 shadow-md group/btn"
            >
              <span>Open Map</span>
              <ArrowRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" />
            </a>
          </div>
        </div>

      </div>
    </section>
  );
}
