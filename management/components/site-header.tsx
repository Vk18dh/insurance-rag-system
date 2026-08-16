import Link from "next/link"
import { ShieldAlert, LogOut } from "lucide-react"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { BackendStatus } from "@/components/backend-status"
import { useAuth } from "@/components/auth-provider"

interface SiteHeaderProps {
    title?: string;
    icon?: React.ReactNode;
}

export function SiteHeader({ title = "Management", icon }: SiteHeaderProps) {
  const { logout, role } = useAuth();
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={role === 'admin' ? '/admin' : '/expert'} className="flex items-center space-x-2">
            {icon ? icon : <ShieldAlert className="h-6 w-6" />}
            <span className="hidden font-bold sm:inline-block">
              {title}
            </span>
          </Link>
          <BackendStatus />
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <nav className="flex items-center space-x-2">
            <ThemeToggle />
            <Button variant="ghost" size="icon" onClick={logout} title="Sign Out">
              <LogOut className="h-4 w-4" />
              <span className="sr-only">Sign Out</span>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  )
}
