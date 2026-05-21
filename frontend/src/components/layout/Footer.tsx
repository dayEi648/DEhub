import { Terminal, Code, Mail } from 'lucide-react'
import { APP_NAME } from '@/constants'

export default function Footer() {
  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">{APP_NAME}</span>
            <span className="text-xs text-muted-foreground">开发者个人网站</span>
          </div>
          <div className="flex items-center gap-4 text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors" aria-label="GitHub">
              <Code className="h-4 w-4" />
            </a>
            <a href="#" className="hover:text-foreground transition-colors" aria-label="Email">
              <Mail className="h-4 w-4" />
            </a>
          </div>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} {APP_NAME}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
