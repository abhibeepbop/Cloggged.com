import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { ArrowRight, Mail, Settings, CheckCircle } from "lucide-react";

export function HowItWorks() {
  const steps = [
    {
      icon: Mail,
      title: "Connect Your Email",
      description: "Securely connect your Gmail, Outlook, or other email accounts in just a few clicks.",
      step: "01"
    },
    {
      icon: Settings,
      title: "AI Learns Your Preferences",
      description: "Our AI analyzes your email patterns and learns what's important to you automatically.",
      step: "02"
    },
    {
      icon: CheckCircle,
      title: "Enjoy a Clean Inbox",
      description: "Sit back and watch as your inbox becomes organized, filtered, and prioritized in real-time.",
      step: "03"
    }
  ];

  return (
    <section id="how-it-works" className="bg-muted/20 py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="mb-4 text-3xl md:text-4xl tracking-tight">
            Get started in minutes
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Setting up clogged.ai is simple and takes less than 5 minutes. No technical knowledge required.
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <Card className="h-full group hover:border-primary/20 transition-colors">
                  <CardHeader className="text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground group-hover:scale-105 transition-transform">
                      <step.icon className="h-8 w-8" />
                    </div>
                    <div className="mb-2 text-sm font-medium text-primary">
                      Step {step.step}
                    </div>
                    <CardTitle className="text-xl">{step.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-center">
                    <p className="text-muted-foreground">{step.description}</p>
                  </CardContent>
                </Card>

                {index < steps.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                    <ArrowRight className="h-6 w-6 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}