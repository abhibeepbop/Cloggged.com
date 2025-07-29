import { InboxHeader } from "./components/InboxHeader";
import { InboxSidebar } from "./components/InboxSidebar";
import { InboxContent } from "./components/InboxContent";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <InboxHeader />
      <div className="flex">
        <InboxSidebar />
        <InboxContent />
      </div>
    </div>
  );
}