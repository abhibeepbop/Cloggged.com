import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { CheckCircle, Brain, Clock, Filter, Trash2, Star } from "lucide-react";

export function Features() {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Advanced machine learning algorithms that understand your email patterns and preferences.",
      badge: "Smart"
    },
    {
      icon: Filter,
      title: "Automatic Filtering",
      description: "Instantly categorize emails into Important, Promotions, Social, and Spam with 99% accuracy.",
      badge: "Automated"
    },
    {
      icon: Clock,
      title: "Priority Inbox",
      description: "See your most important emails first with intelligent priority scoring and urgency detection.",
      badge: "Priority"
    },
    {
      icon: Trash2,
      title: "Spam Elimination",
      description: "Remove unwanted emails before they reach your inbox with advanced threat detection.",
      badge: "Protection"
    },
    {
      icon: Star,
      title: "VIP Recognition",
      description: "Automatically identify and prioritize emails from your most important contacts.",
      badge: "VIP"
    },
    {
      icon: CheckCircle,
      title: "Bulk Actions",
      description: "Clean up your inbox faster with intelligent bulk operations and one-click organization.",
      badge: "Efficiency"
    }
  ];

  return (
    <section id="features" className="container mx-auto px-4 py-24">
      <div className="text-center mb-16">
        <h2 className="mb-4 text-3xl md:text-4xl tracking-tight">
          Everything you need to manage email efficiently
        </h2>
        <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
          Powerful features designed to save you hours every day while keeping your inbox organized and secure.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => (
          <Card key={index} className="relative group hover:border-primary/20 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between mb-2">
                <div className="h-10 w-10 rounded-lg bg-primary/5 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <Badge variant="secondary">{feature.badge}</Badge>
              </div>
              <CardTitle className="text-xl">{feature.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-base">
                {feature.description}
              </CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}