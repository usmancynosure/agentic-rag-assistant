"use client";

import {
  BotIcon,
  CompassIcon,
  FolderIcon,
  GridIcon,
  HistoryIcon,
  HomeIcon,
  SearchIcon,
} from "./icons";

interface SidebarProps {
  onOpenDocuments?: () => void;
}

/** Left vertical icon rail (glassy), matching the reference layout. */
export default function Sidebar({ onOpenDocuments }: SidebarProps) {
  const nav = [
    { label: "Search", icon: SearchIcon, onClick: undefined },
    { label: "Home", icon: HomeIcon, onClick: undefined },
    { label: "Explore", icon: CompassIcon, onClick: undefined },
    { label: "Documents", icon: FolderIcon, onClick: onOpenDocuments },
    { label: "History", icon: HistoryIcon, onClick: undefined },
  ];

  return (
    <aside className="flex flex-col items-center gap-2 py-6">
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary text-white shadow-rail">
        <BotIcon className="h-6 w-6" aria-hidden />
        <span className="sr-only">Agentic RAG</span>
      </div>
      <nav className="flex flex-col items-center gap-1">
        {nav.map(({ label, icon: Icon, onClick }) => (
          <button
            key={label}
            type="button"
            className="rail-btn"
            aria-label={label}
            title={label}
            onClick={onClick}
          >
            <Icon className="h-5 w-5" aria-hidden />
          </button>
        ))}
      </nav>
      <div className="mt-auto">
        <button type="button" className="rail-btn" aria-label="Apps" title="Apps">
          <GridIcon className="h-5 w-5" aria-hidden />
        </button>
      </div>
    </aside>
  );
}
