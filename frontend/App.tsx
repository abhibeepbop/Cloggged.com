import imgImage2 from "figma:asset/983180bf1cd85161b16083f4efccaaf9f7350d91.png";

function PricingCard() {
  const handleStartFreeTrial = () => {
    // Handle free trial signup
    console.log("Starting free trial...");
  };

  return (
    <div className="flex justify-center gap-12 max-w-2xl mx-auto">
      {/* Standard Plan Card */}
      <div className="bg-[rgba(255,255,255,0.04)] border-[7px] border-gray-800 rounded-[27px] shadow-[17px_11px_4px_0px_rgba(0,0,0,0.25)] w-[260px] h-[300px] p-6 flex flex-col items-center">
        <div className="text-[28px] font-bold text-black mt-2">£5.99</div>
        <div
          className="bg-center bg-cover bg-no-repeat w-[70px] h-[70px] my-3"
          style={{ backgroundImage: `url('${imgImage2}')` }}
        />
        <div className="text-[24px] font-normal text-[#222222] mb-3">Standard</div>
        <button 
          onClick={handleStartFreeTrial}
          className="bg-[#efa6a7] hover:bg-[#e89899] transition-colors border border-black rounded-[15px] px-4 py-2 w-full text-sm"
        >
          Start free trial
        </button>
      </div>

      {/* Coming Soon Card */}
      <div className="bg-[rgba(255,255,255,0.04)] border-[7px] border-gray-800 rounded-[27px] shadow-[17px_11px_4px_0px_rgba(0,0,0,0.25)] w-[260px] h-[300px] p-6 flex flex-col items-center justify-center">
        <div className="text-[24px] font-bold text-black text-center leading-tight">
          More Features<br/>Coming Soon
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const handleWatchDemo = () => {
    // Handle watch demo action
    console.log("Watching demo...");
  };

  const handleSignIn = () => {
    // Handle sign in action
    console.log("Signing in...");
  };

  const handleGetStarted = () => {
    // Handle get started action
    console.log("Getting started...");
  };

  const handleStartFreeTrial = () => {
    // Handle free trial signup
    console.log("Starting free trial...");
  };

  return (
    <div className="bg-white min-h-screen flex flex-col max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex justify-between items-center px-8 py-6 border-b border-black">
        <div className="text-[24px] font-bold text-black">
          Clogged.ai
        </div>
        
        <nav className="flex gap-3">
          <button 
            onClick={handleWatchDemo}
            className="border border-black rounded-[18px] px-5 py-2 hover:bg-gray-50 transition-colors text-sm"
          >
            watch demo
          </button>
          
          <button 
            onClick={handleSignIn}
            className="border border-black rounded-[18px] px-5 py-2 hover:bg-gray-50 transition-colors text-sm"
          >
            sign in
          </button>
          
          <button 
            onClick={handleGetStarted}
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
          <h1 className="text-[48px] font-bold text-black mb-4">Welcome to Clogged.ai</h1>
          <p className="text-[18px] text-gray-600 mb-8 max-w-2xl mx-auto">
            Powerful AI solutions to streamline your workflow and boost productivity
          </p>
        </section>

        {/* Pricing Section */}
        <section className="py-8">
          <PricingCard />
        </section>

        {/* Action Buttons */}
        <section className="flex justify-center gap-6 py-8">
          <button 
            onClick={handleStartFreeTrial}
            className="bg-[#efa6a7] hover:bg-[#e89899] border-2 border-black rounded-[33px] px-8 py-3 text-[18px] transition-colors"
          >
            Start free trial
          </button>
          
          <button 
            onClick={handleWatchDemo}
            className="bg-[#79d3e7] hover:bg-[#6bc5db] border-2 border-black rounded-[33px] px-8 py-3 text-[18px] transition-colors"
          >
            How it works
          </button>
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