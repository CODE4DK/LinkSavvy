import { EmptyState } from "@/components/ui/EmptyState";

export interface HubComingSoonProps {
  title: string;
  description: string;
}

export function HubComingSoon({ title, description }: HubComingSoonProps) {
  return (
    <div className="flex h-full flex-col">
      <h1 className="mb-6 text-2xl font-semibold text-fg">{title}</h1>
      <EmptyState
        title="Coming in a later phase"
        description={description}
        icon={
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            className="h-6 w-6"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 6v6l4 2m6-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z"
            />
          </svg>
        }
      />
    </div>
  );
}
