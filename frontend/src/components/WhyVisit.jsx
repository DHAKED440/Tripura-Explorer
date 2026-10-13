import React from 'react';
import { Leaf, Landmark, Sparkles, ShieldCheck } from 'lucide-react';
import { whyVisitFeatures } from '../data/destinations';

export default function WhyVisit() {
  const getFeatureIcon = (id) => {
    switch (id) {
      case 'nature':
        return <Leaf className="w-5 h-5 text-[#2F7D4F]" />;
      case 'heritage':
        return <Landmark className="w-5 h-5 text-[#E8892B]" />;
      case 'culture':
        return <Sparkles className="w-5 h-5 text-[#E8892B]" />;
      case 'peaceful':
        return <ShieldCheck className="w-5 h-5 text-[#2F7D4F]" />;
      default:
        return <Sparkles className="w-5 h-5 text-amber" />;
    }
  };

  const getCircleBg = (id) => {
    switch (id) {
      case 'nature':
        return 'bg-[#EBF5EE]';
      case 'heritage':
        return 'bg-[#FEF6EE]';
      case 'culture':
        return 'bg-[#FEF6EE]';
      case 'peaceful':
        return 'bg-[#EBF5EE]';
      default:
        return 'bg-cream';
    }
  };

  return (
    <section className="px-3 sm:px-4 py-8 sm:py-10">
      <div className="max-w-[1360px] mx-auto bg-white rounded-3xl p-6 sm:p-10 shadow-card border border-slate-100">
        
        {/* Section Heading */}
        <div className="mb-8">
          <h2 className="text-xl sm:text-2xl font-bold text-navy tracking-tight font-sans">
            Why Visit Tripura?
          </h2>
        </div>

        {/* 4 Feature Columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {whyVisitFeatures.map((item) => (
            <div key={item.id} className="flex flex-col items-start group">
              
              {/* Circular Soft Icon Badge */}
              <div
                className={`w-13 h-13 sm:w-14 sm:h-14 rounded-full ${getCircleBg(
                  item.id
                )} flex items-center justify-center mb-4 transition-transform duration-200 group-hover:scale-110 shadow-sm`}
              >
                {getFeatureIcon(item.id)}
              </div>

              {/* Title & Description */}
              <h3 className="text-[15px] sm:text-base font-bold text-navy mb-1.5 leading-snug">
                {item.title}
              </h3>
              <p className="text-xs sm:text-sm text-slate-500 font-normal leading-relaxed">
                {item.description}
              </p>

            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
