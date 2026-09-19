import type { ComponentType } from "react";
import {
  IconBell,
  IconBolt,
  IconFolder,
  IconGlobe,
  IconMail,
  IconOverview,
  IconSettings,
  IconWorkflow,
} from "../components/NavIcons";

export type NavItem = {
  to: string;
  label: string;
  shortLabel?: string;
  end?: boolean;
  Icon: ComponentType<{ className?: string }>;
};

export type NavSection = {
  label: string;
  items: NavItem[];
};

export const navSections: NavSection[] = [
  {
    label: "Intelligence",
    items: [
      { to: "/app", label: "Overview", shortLabel: "Home", end: true, Icon: IconOverview },
      { to: "/app/attacks", label: "Attacks", shortLabel: "Attacks", Icon: IconBolt },
      { to: "/app/sources", label: "Source IPs", shortLabel: "Sources", Icon: IconGlobe },
    ],
  },
  {
    label: "Response",
    items: [
      { to: "/app/cases", label: "Cases", Icon: IconFolder },
      { to: "/app/abuse-reports", label: "Abuse reports", shortLabel: "Abuse", Icon: IconMail },
    ],
  },
  {
    label: "Automation",
    items: [
      { to: "/app/rules", label: "Rules", Icon: IconWorkflow },
      { to: "/app/notifications", label: "Notifications", shortLabel: "Alerts", Icon: IconBell },
      { to: "/app/settings", label: "Settings", Icon: IconSettings },
    ],
  },
];

export const mobilePrimaryNav: NavItem[] = [
  { to: "/app", label: "Overview", shortLabel: "Home", end: true, Icon: IconOverview },
  { to: "/app/attacks", label: "Attacks", shortLabel: "Attacks", Icon: IconBolt },
  { to: "/app/sources", label: "Source IPs", shortLabel: "Sources", Icon: IconGlobe },
  { to: "/app/cases", label: "Cases", shortLabel: "Cases", Icon: IconFolder },
];

export const allNavItems: NavItem[] = navSections.flatMap((s) => s.items);
