import {
  BotIcon,
  CompassIcon,
  FolderIcon,
  GridIcon,
  HistoryIcon,
  HomeIcon,
  SearchIcon,
} from "./icons";

const NAV = [
  { label: "Search", icon: SearchIcon },
  { label: "Home", icon: HomeIcon },
  { label: "Explore", icon: CompassIcon },
  { label: "Documents", icon: FolderIcon },
  { label: "History", icon: HistoryIcon },
];

/** Left vertical icon rail (glassy), matching the reference layout. */
export default function Sidebar() {
  return (
    <aside className="flex flex-col items-center gap-2 py-6">
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary text-white shadow-rail">
        <BotIcon className="h-6 w-6" aria-hidden />
        <span className="sr-only">Agentic RAG</span>
      </div>
      <nav className="flex flex-col items-center gap-1">
        {NAV.map(({ label, icon: Icon }) => (
          <button key={label} type="button" className="rail-btn" aria-label={label} title={label}>
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
