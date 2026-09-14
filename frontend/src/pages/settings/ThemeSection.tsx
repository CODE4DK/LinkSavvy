import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

export function ThemeSection() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>
          Follows your system by default, or pick a theme explicitly.
        </CardDescription>
      </CardHeader>
      <ThemeToggle />
    </Card>
  );
}
