import { useState } from "react";

interface EmailCollectionProps {
  onEmailSubmitted: (email: string) => void;
}

export function EmailCollection({ onEmailSubmitted }: EmailCollectionProps) {
  const [email, setEmail] = useState("");
  const [isValid, setIsValid] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setIsValid(false);
      return;
    }
    
    setIsValid(true);
    onEmailSubmitted(email);
  };

  return (
    <div className="bg-white min-h-screen flex flex-col max-w-6xl mx-auto">
      {/* Header */}
      <header className="flex justify-between items-center px-8 py-6 border-b border-black">
        <div className="text-[24px] font-bold text-black">
          cloggged.com
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-8">
        <div className="text-center max-w-md">
          <h1 className="text-[48px] font-bold text-black mb-4">Get Started</h1>
          <p className="text-[18px] text-gray-600 mb-8">
            Enter your email to start organizing your inbox with AI
          </p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setIsValid(true);
                }}
                placeholder="Enter your email address"
                className={`w-full px-4 py-3 border-2 border-black rounded-[18px] text-[16px] focus:outline-none focus:border-[#79d3e7] ${
                  !isValid ? 'border-red-500' : ''
                }`}
              />
              {!isValid && (
                <p className="text-red-500 text-sm mt-1">Please enter a valid email address</p>
              )}
            </div>
            
            <button
              type="submit"
              className="w-full bg-[#79d3e7] hover:bg-[#6bc5db] border-2 border-black rounded-[18px] px-8 py-3 text-[18px] transition-colors"
            >
              Continue
            </button>
          </form>
          
          <p className="text-sm text-gray-500 mt-4">
            We'll never share your email with anyone else
          </p>
        </div>
      </main>
    </div>
  );
} 