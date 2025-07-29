import { Button } from "./ui/button";
import { Mail, Zap, Shield } from "lucide-react";

export function Hero() {
  return (
    <section className="container mx-auto px-4 py-24 text-center">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-4xl md:text-6xl tracking-tight">
          Stop drowning in your inbox.
          <br />
          <span className="text-primary">Let AI unclog it.</span>
        </h1>
        
        <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground">
          clogged.ai is an intelligent email agent that automatically filters, prioritizes, and organizes your inbox so you can focus on what matters most.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button size="lg" className="px-8">
            Start free trial
          </Button>
          <Button variant="outline" size="lg" className="px-8">
            Watch demo
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
          <div className="flex flex-col items-center p-6 rounded-lg border bg-card group hover:border-primary/20 transition-colors">
            <div className="h-12 w-12 rounded-full bg-primary/5 flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
              <Mail className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-2">Smart Filtering</h3>
            <p className="text-sm text-muted-foreground text-center">
              AI learns your preferences and automatically sorts important emails
            </p>
          </div>
          
          <div className="flex flex-col items-center p-6 rounded-lg border bg-card group hover:border-primary/20 transition-colors">
            <div className="h-12 w-12 rounded-full bg-primary/5 flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-2">Lightning Fast</h3>
            <p className="text-sm text-muted-foreground text-center">
              Process thousands of emails in seconds, not hours
            </p>
          </div>
          
          <div className="flex flex-col items-center p-6 rounded-lg border bg-card group hover:border-primary/20 transition-colors">
            <div className="h-12 w-12 rounded-full bg-primary/5 flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <h3 className="mb-2">Privacy First</h3>
            <p className="text-sm text-muted-foreground text-center">
              Your emails stay private and secure with end-to-end encryption
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}