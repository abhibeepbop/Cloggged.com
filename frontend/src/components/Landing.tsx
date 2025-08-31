import { useNavigate } from "react-router-dom";

interface LandingProps {
  onGetStarted: () => void;
  onWatchDemo: () => void;
  onSignIn: () => void;
}

export function Landing({ onGetStarted, onWatchDemo, onSignIn }: LandingProps) {
  const navigate = useNavigate();
  return (
    <div className="bg-white min-h-screen flex flex-col max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex justify-between items-center px-8 py-6 border-b border-black">
        <div className="flex items-center gap-2">
          <img src="/cloggged_logo.png" alt="Logo" className="block h-10 w-15" />
          <div className="text-[24px] leading-none font-bold text-black">cloggged.com</div>
        </div>
        
        <nav className="flex gap-3">
          <button 
            onClick={onWatchDemo}
            className="border border-black rounded-[18px] px-5 py-2 hover:bg-gray-50 transition-colors text-sm"
          >
            watch demo
          </button>
          
          <button 
            onClick={onSignIn}
            className="border border-black rounded-[18px] px-5 py-2 hover:bg-gray-50 transition-colors text-sm"
          >
            sign in
          </button>
          
          <button 
            onClick={onGetStarted}
            className="bg-[#79d3e7] hover:bg-[#6bc5db] border border-black rounded-[18px] px-5 py-2 transition-colors text-sm"
          >
            Get Started
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Hero Section */}
        <section className="text-center py-12 px-8">
          <h1 className="text-[48px] font-bold text-black mb-4">Welcome to cloggged.com</h1>
          <p className="text-[18px] text-gray-600 mb-8 max-w-2xl mx-auto">
            Powerful AI solutions to streamline your workflow and boost productivity
          </p>
        </section>

        {/* Reviews Section */}
        <section className="bg-gray-800 py-12 mt-8">
          <div className="text-center mb-8">
            <h2 className="text-[32px] font-bold text-white">Reviews</h2>
          </div>
          
          <div className="flex justify-center gap-6 max-w-4xl mx-auto px-8">
            {/* Empty Review Cards */}
            <div className="bg-white border-4 border-black rounded-[53px] w-[240px] h-[160px] flex items-center justify-center">
              <div className="text-gray-400 text-center">
                <div className="text-sm">Review coming soon</div>
              </div>
            </div>
            <div className="bg-white border-4 border-black rounded-[53px] w-[240px] h-[160px] flex items-center justify-center">
              <div className="text-gray-400 text-center">
                <div className="text-sm">Review coming soon</div>
              </div>
            </div>
            <div className="bg-white border-4 border-black rounded-[53px] w-[240px] h-[160px] flex items-center justify-center">
              <div className="text-gray-400 text-center">
                <div className="text-sm">Review coming soon</div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
} 