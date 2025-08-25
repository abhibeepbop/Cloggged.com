
import React from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../utils/api";
import { InboxHeaderUser } from "./InboxHeaderUser";

interface PricingProps {
  onStartFreeTrial: () => void;
}

export function Pricing({ onStartFreeTrial }: PricingProps) {
  const navigate = useNavigate();
  
  const handleStartFreeTrial = async () => {
    window.location.href = 'https://buy.stripe.com/00w8wP0XQ3bK4KH69KefC00';
  };

  const handleHomeClick = () => {
    navigate('/');
  };



  return (
    <div className="bg-navy-50 min-h-screen font-['Inter']">
      {/* Header replaced with shared InboxHeaderUser */}
      <InboxHeaderUser />

      {/* Main Content */}
      <main className="flex flex-col items-center justify-center py-16 px-6 pb-0">
        <h2 className="text-4xl font-bold mb-10 text-center text-navy-900">Pricing</h2>

        <div className="flex flex-col lg:flex-row justify-center items-center gap-12">
          {/* Standard Plan Card */}
          <div className="bg-white border-4 border-navy-800 rounded-3xl shadow-[10px_10px_0px_0px_rgba(30,58,138,0.2)] w-72 h-96 p-6 flex flex-col items-center text-center">
            <p className="text-5xl font-bold text-navy-900 mb-2">£5.99</p>
            <div className="w-16 h-16 bg-navy-100 rounded-full flex items-center justify-center mb-3">
                             <span className="text-7xl text-navy-600 mt-20">🧹</span>
            </div>
            <p className="text-4xl font-small text-navy-900 mb-6 mt-20">Standard</p>
            <button 
              onClick={handleStartFreeTrial}
              className="bg-[#EFA6A7] hover:bg-[#e89899] text-black border border-navy-800 rounded-full px-6 py-2 font-medium text-lg transition-colors w-full"
            >
              Start free trial
            </button>
          </div>

          {/* Features Section */}
          <div className="space-y-6 max-w-sm">
            <div className="flex items-start gap-3">
              <div>
                <p className="font-bold text-xl text-navy-900">AI-powered sorting</p>
                <p className="text-navy-700 text-xl">Organizes and prioritizes your inbox automatically.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div>
                <p className="font-bold text-xl text-navy-900">Always running</p>
                <p className="text-navy-700 text-xl">Keeps your inbox clean without lifting a finger.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div>
                <p className="font-bold text-xl text-navy-900">Privacy-first</p>
                <p className="text-navy-700 text-xl">No data stored. Your emails remain private.</p>
              </div>
            </div>
          </div>

          {/* Coming Soon Card */}
          <div className="bg-white border-4 border-navy-800 rounded-3xl shadow-[10px_10px_0px_0px_rgba(30,58,138,0.2)] w-72 p-6 flex items-center justify-center text-center h-96">
            <p className="text-4xl font-normal text-navy-900 leading-tight">
              More Features<br/>Coming Soon
            </p>
          </div>
        </div>

        {/* Call to Action */}
        <div className="flex flex-col sm:flex-row justify-center gap-6 mt-16">
                      <button 
              onClick={handleStartFreeTrial}
              className="bg-[#EFA6A7] hover:bg-[#e89899] border-2 border-navy-800 rounded-full px-8 py-3 text-lg font-semibold text-black transition-colors"
            >
              Start free trial
            </button>

          <button 
            className="bg-[#79D3E7] hover:bg-[#6bc5db] border-2 border-navy-800 rounded-full px-8 py-3 text-lg font-semibold text-black transition-colors"
          >
            Watch demo
          </button>
        </div>

        {/* Reviews Section */}
        <section className="w-screen -mx-6 mt-24 bg-[#1F2937] py-12 min-h-screen -mb-6">
          <div className="max-w-6xl mx-auto px-6">
            <h3 className="text-3xl font-bold text-center text-navy-900 mb-8 text-white">Reviews</h3>
            <div className="flex flex-col sm:flex-row justify-center gap-16">
              {[1, 2, 3, 4].map((_, idx) => (
                <div key={idx} className="bg-white border-4 border-navy-800 rounded-3xl shadow-[3px_3px_0px_0px_rgba(30,58,138,0.2)] w-80 h-60 flex items-center justify-center">
                  <p className="text-navy-600 text-lg text-center">Review coming soon</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>


    </div>
  );
} 